#!/usr/bin/env python3
"""Educational FTP-like honeypot.

This server does not authenticate users or execute operating-system commands.
It records connection metadata, submitted usernames/passwords, and FTP-like
commands for defensive observation in an isolated lab environment.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import signal
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Config:
    host: str
    port: int
    banner: str
    server_name: str
    idle_timeout_seconds: int
    max_command_length: int
    log_file: Path


def load_config(path: Path) -> Config:
    with path.open("r", encoding="utf-8") as fh:
        raw: dict[str, Any] = yaml.safe_load(fh) or {}

    required = {"host", "port", "banner", "server_name", "idle_timeout_seconds", "max_command_length", "log_file"}
    missing = required - raw.keys()
    if missing:
        raise ValueError(f"設定項目が不足しています: {', '.join(sorted(missing))}")

    port = int(raw["port"])
    if not 1 <= port <= 65535:
        raise ValueError("port は 1～65535 の範囲で指定してください")

    return Config(
        host=str(raw["host"]),
        port=port,
        banner=str(raw["banner"]),
        server_name=str(raw["server_name"]),
        idle_timeout_seconds=max(1, int(raw["idle_timeout_seconds"])),
        max_command_length=max(32, int(raw["max_command_length"])),
        log_file=Path(str(raw["log_file"])),
    )


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class JsonLineLogger:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path

    def write(self, event: str, **fields: Any) -> None:
        record = {"timestamp": utc_now(), "event": event, **fields}
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


class HoneyFTP:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.events = JsonLineLogger(config.log_file)
        self.server: asyncio.AbstractServer | None = None

    async def start(self) -> None:
        self.server = await asyncio.start_server(self.handle_client, self.config.host, self.config.port)
        sockets = self.server.sockets or []
        addresses = ", ".join(str(sock.getsockname()) for sock in sockets)
        logging.info("HoneyFTP started on %s", addresses)
        self.events.write("server_started", addresses=addresses)

    async def stop(self) -> None:
        if self.server is not None:
            self.server.close()
            await self.server.wait_closed()
            self.events.write("server_stopped")
            logging.info("HoneyFTP stopped")

    async def serve_forever(self) -> None:
        if self.server is None:
            raise RuntimeError("server is not started")
        async with self.server:
            await self.server.serve_forever()

    async def send_line(self, writer: asyncio.StreamWriter, text: str) -> None:
        writer.write((text + "\r\n").encode("utf-8"))
        await writer.drain()

    async def read_line(self, reader: asyncio.StreamReader) -> str | None:
        try:
            raw = await asyncio.wait_for(reader.readline(), timeout=self.config.idle_timeout_seconds)
        except asyncio.TimeoutError:
            return None
        if not raw:
            return None
        if len(raw) > self.config.max_command_length:
            return "__TOO_LONG__"
        return raw.decode("utf-8", errors="replace").strip("\r\n")

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        client_ip = peer[0] if isinstance(peer, tuple) and peer else "unknown"
        client_port = peer[1] if isinstance(peer, tuple) and len(peer) > 1 else 0
        username = ""
        logged_in = False

        self.events.write("connection_opened", client_ip=client_ip, client_port=client_port)
        try:
            await self.send_line(writer, f"220 {self.config.server_name} {self.config.banner}")

            while True:
                line = await self.read_line(reader)
                if line is None:
                    self.events.write("connection_timeout_or_closed", client_ip=client_ip, client_port=client_port)
                    break
                if line == "__TOO_LONG__":
                    self.events.write("oversized_input", client_ip=client_ip, client_port=client_port)
                    await self.send_line(writer, "500 Command line too long")
                    break

                command, _, argument = line.partition(" ")
                command = command.upper().strip()
                argument = argument.strip()
                self.events.write(
                    "command_received",
                    client_ip=client_ip,
                    client_port=client_port,
                    command=command,
                    argument=argument,
                )

                if command == "USER":
                    username = argument
                    await self.send_line(writer, "331 Password required")
                elif command == "PASS":
                    # Educational honeypot: accept any credential but never grant real access.
                    self.events.write(
                        "credential_submitted",
                        client_ip=client_ip,
                        client_port=client_port,
                        username=username,
                        password=argument,
                    )
                    logged_in = True
                    await self.send_line(writer, "230 Login successful")
                elif command in {"SYST", "FEAT"}:
                    await self.send_line(writer, "215 UNIX Type: L8")
                elif command == "PWD":
                    await self.send_line(writer, '257 "/srv/backup" is the current directory')
                elif command == "LIST":
                    if not logged_in:
                        await self.send_line(writer, "530 Please login with USER and PASS")
                    else:
                        await self.send_line(writer, "150 Opening ASCII mode data connection")
                        await self.send_line(writer, "226 Transfer complete")
                elif command in {"RETR", "STOR", "DELE", "MKD", "RMD", "CWD"}:
                    await self.send_line(writer, "550 Requested action not taken")
                elif command in {"QUIT", "EXIT"}:
                    await self.send_line(writer, "221 Goodbye")
                    break
                elif command == "NOOP":
                    await self.send_line(writer, "200 OK")
                elif not command:
                    await self.send_line(writer, "500 Empty command")
                else:
                    await self.send_line(writer, "502 Command not implemented")
        except (ConnectionResetError, BrokenPipeError):
            self.events.write("connection_reset", client_ip=client_ip, client_port=client_port)
        except Exception as exc:  # Defensive logging; server continues accepting later clients.
            logging.exception("client handler failed")
            self.events.write("handler_error", client_ip=client_ip, client_port=client_port, error=repr(exc))
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            self.events.write("connection_closed", client_ip=client_ip, client_port=client_port)


async def async_main(config_path: Path) -> None:
    config = load_config(config_path)
    app = HoneyFTP(config)
    await app.start()

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass

    serve_task = asyncio.create_task(app.serve_forever())
    stop_task = asyncio.create_task(stop_event.wait())
    done, pending = await asyncio.wait({serve_task, stop_task}, return_when=asyncio.FIRST_COMPLETED)

    for task in pending:
        task.cancel()
    await app.stop()


def main() -> int:
    parser = argparse.ArgumentParser(description="Educational FTP-like honeypot")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML configuration file")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    try:
        asyncio.run(async_main(Path(args.config)))
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        logging.error("起動に失敗しました: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

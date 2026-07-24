#!/usr/bin/env python3
"""Local functional test client for HoneyFTP."""

from __future__ import annotations

import argparse
import socket
import sys


def recv_line(sock: socket.socket) -> str:
    data = bytearray()
    while not data.endswith(b"\n"):
        chunk = sock.recv(1)
        if not chunk:
            break
        data.extend(chunk)
    return data.decode("utf-8", errors="replace").strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2121)
    args = parser.parse_args()

    commands = [
        ("USER student", "331"),
        ("PASS test-pass-123", "230"),
        ("PWD", "257"),
        ("LIST", "150"),
        ("RETR secret.zip", "550"),
        ("QUIT", "221"),
    ]

    with socket.create_connection((args.host, args.port), timeout=5) as sock:
        banner = recv_line(sock)
        print(f"RECV: {banner}")
        if not banner.startswith("220"):
            print("FAIL: banner", file=sys.stderr)
            return 1

        for command, expected in commands:
            print(f"SEND: {command}")
            sock.sendall((command + "\r\n").encode())
            response = recv_line(sock)
            print(f"RECV: {response}")
            if not response.startswith(expected):
                print(f"FAIL: expected {expected}", file=sys.stderr)
                return 1
            if command == "LIST":
                second = recv_line(sock)
                print(f"RECV: {second}")
                if not second.startswith("226"):
                    return 1

    print("PASS: all functional checks succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

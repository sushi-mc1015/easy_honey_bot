from pathlib import Path
import tempfile
import unittest

from honeyftp import JsonLineLogger, load_config


class HoneyFTPUnitTests(unittest.TestCase):
    def test_load_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.yaml"
            path.write_text(
                "host: '127.0.0.1'\n"
                "port: 2121\n"
                "banner: 'Ready'\n"
                "server_name: 'TestFTP'\n"
                "idle_timeout_seconds: 10\n"
                "max_command_length: 128\n"
                "log_file: 'logs/test.jsonl'\n",
                encoding="utf-8",
            )
            cfg = load_config(path)
            self.assertEqual(cfg.port, 2121)
            self.assertEqual(cfg.host, "127.0.0.1")

    def test_json_logger(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            JsonLineLogger(path).write("unit_test", value=1)
            text = path.read_text(encoding="utf-8")
            self.assertIn('"event": "unit_test"', text)


if __name__ == "__main__":
    unittest.main()

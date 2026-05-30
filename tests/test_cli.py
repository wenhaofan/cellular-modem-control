import io
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from cellular_modem.cli import _default_port, _normalize, build_parser, main
from cellular_modem.modem import SMSMessage


class CLITests(unittest.TestCase):
    def test_parser_accepts_json_after_subcommand(self):
        parser = build_parser()

        args = parser.parse_args(["--port", "COM8", "signal", "--json"])

        self.assertEqual(args.port, "COM8")
        self.assertEqual(args.command, "signal")
        self.assertTrue(args.json)

    def test_normalize_dataclass_list(self):
        message = SMSMessage(index=1, status="REC READ", sender="+123", timestamp="now", text="hello")

        self.assertEqual(
            _normalize([message]),
            [{"index": 1, "status": "REC READ", "sender": "+123", "timestamp": "now", "text": "hello"}],
        )

    def test_default_port_prefers_modem_port_env(self):
        with patch.dict(os.environ, {"MODEM_PORT": "COM42", "QUECTEL_MODEM_PORT": "COM8"}):
            self.assertEqual(_default_port(), "COM42")

    def test_main_without_command_returns_usage_error(self):
        output = io.StringIO()
        with redirect_stdout(output):
            result = main([])

        self.assertEqual(result, 2)
        self.assertIn("usage: modemctl", output.getvalue())


if __name__ == "__main__":
    unittest.main()

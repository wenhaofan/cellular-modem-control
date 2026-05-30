import io
import os
import unittest
from contextlib import contextmanager, redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

from cellular_modem import cli
from cellular_modem.at import ATResponse
from cellular_modem.cli import _default_port, _normalize, build_parser, main
from cellular_modem.modem import CallInfo, SMSMessage
from cellular_modem.ports import SerialPortInfo


class CLITests(unittest.TestCase):
    def test_parser_accepts_json_after_subcommand(self):
        parser = build_parser()

        args = parser.parse_args(["--port", "COM8", "signal", "--json"])

        self.assertEqual(args.port, "COM8")
        self.assertEqual(args.command, "signal")
        self.assertTrue(args.json)

    def test_parser_accepts_smoke_show_sensitive(self):
        parser = build_parser()

        args = parser.parse_args(["--port", "COM8", "smoke", "--show-sensitive", "--format", "markdown", "--json"])

        self.assertEqual(args.command, "smoke")
        self.assertTrue(args.show_sensitive)
        self.assertEqual(args.format, "markdown")
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

    def test_ports_handler_uses_public_port_discovery(self):
        args = args_for(json=False)
        fake_ports = [SerialPortInfo(device="COM8", description="USB Serial Port", hwid="USB")]

        with patch("cellular_modem.cli.list_serial_ports", return_value=fake_ports) as list_ports:
            output = io.StringIO()
            with redirect_stdout(output):
                result = cli.cmd_ports(args)

        self.assertEqual(result, 0)
        list_ports.assert_called_once_with()
        self.assertIn("COM8", output.getvalue())

    def test_read_only_handlers_use_open_modem(self):
        fake = FakeCliModem()
        args = args_for(json=False)

        with patched_modem(fake):
            self.assertEqual(run_silent(cli.cmd_info, args), 0)
            self.assertEqual(run_silent(cli.cmd_sim, args), 0)
            self.assertEqual(run_silent(cli.cmd_signal, args), 0)

        self.assertEqual(fake.calls[:3], ["info", "sim_status", "signal_quality"])

    def test_state_changing_handlers_return_success_for_ok_finals(self):
        fake = FakeCliModem()
        args = args_for(number="+123", index=1, digits="12#", duration=3, level=70, state="on")

        with patched_modem(fake):
            self.assertEqual(run_silent(cli.cmd_sms_send, args), 0)
            self.assertEqual(run_silent(cli.cmd_sms_delete, args), 0)
            self.assertEqual(run_silent(cli.cmd_call_dial, args), 0)
            self.assertEqual(run_silent(cli.cmd_call_answer, args), 0)
            self.assertEqual(run_silent(cli.cmd_call_hangup, args), 0)
            self.assertEqual(run_silent(cli.cmd_dtmf, args), 0)
            self.assertEqual(run_silent(cli.cmd_audio_volume, args), 0)
            self.assertEqual(run_silent(cli.cmd_audio_mute, args), 0)

        self.assertIn(("send_sms", "+123", "hello", "auto"), fake.calls)
        self.assertIn(("send_dtmf", "12#", 3), fake.calls)
        self.assertIn(("set_speaker_volume", 70), fake.calls)
        self.assertIn(("mute_microphone", True), fake.calls)

    def test_list_and_read_handlers_print_collections(self):
        fake = FakeCliModem()
        args = args_for(index=1, status="ALL")

        with patched_modem(fake):
            self.assertEqual(run_silent(cli.cmd_sms_list, args), 0)
            self.assertEqual(run_silent(cli.cmd_sms_read, args), 0)
            self.assertEqual(run_silent(cli.cmd_call_list, args), 0)

        self.assertIn(("list_sms", "ALL"), fake.calls)
        self.assertIn(("read_sms", 1), fake.calls)
        self.assertIn("list_calls", fake.calls)

    def test_raw_and_call_handlers_return_failure_for_non_ok_final(self):
        fake = FakeCliModem(raw_final="ERROR", call_final="BUSY")

        with patched_modem(fake):
            self.assertEqual(run_silent(cli.cmd_raw, args_for(at_command="AT+FAIL", command_timeout=2.0)), 1)
            self.assertEqual(run_silent(cli.cmd_call_dial, args_for(number="+123")), 1)

    def test_monitor_handler_enables_events_when_requested(self):
        fake = FakeCliModem()

        with patched_modem(fake):
            self.assertEqual(run_silent(cli.cmd_monitor, args_for(enable_events=True, seconds=1)), 0)

        self.assertIn("enable_event_notifications", fake.calls)
        self.assertIn(("monitor_events", 1), fake.calls)


class FakeCliModem:
    def __init__(self, raw_final="OK", call_final="OK"):
        self.raw_final = raw_final
        self.call_final = call_final
        self.calls = []

    def info(self):
        self.calls.append("info")
        return {"manufacturer": "Test", "model": "M1"}

    def sim_status(self):
        self.calls.append("sim_status")
        return "READY"

    def signal_quality(self):
        self.calls.append("signal_quality")
        return {"rssi": 20, "dbm": -73, "ber": 99}

    def raw(self, command, timeout=5.0):
        self.calls.append(("raw", command, timeout))
        return ATResponse(command=command, lines=["payload"], final=self.raw_final)

    def send_sms(self, number, text, encoding="auto"):
        self.calls.append(("send_sms", number, text, encoding))
        return 1

    def list_sms(self, status="ALL"):
        self.calls.append(("list_sms", status))
        return [SMSMessage(index=1, status="REC READ", sender="+123", timestamp="now", text="hello")]

    def read_sms(self, index):
        self.calls.append(("read_sms", index))
        return SMSMessage(index=index, status="REC READ", sender="+123", timestamp="now", text="hello")

    def delete_sms(self, index):
        self.calls.append(("delete_sms", index))

    def dial(self, number):
        self.calls.append(("dial", number))
        return ATResponse(command="ATD", lines=[], final=self.call_final)

    def answer(self):
        self.calls.append("answer")
        return ATResponse(command="ATA", lines=[], final=self.call_final)

    def hangup(self):
        self.calls.append("hangup")
        return ATResponse(command="ATH", lines=[], final=self.call_final)

    def list_calls(self):
        self.calls.append("list_calls")
        return [CallInfo(index=1, direction=0, status=0, mode=0, multiparty=0, number="+123", number_type=145)]

    def send_dtmf(self, digits, duration=None):
        self.calls.append(("send_dtmf", digits, duration))
        return ATResponse(command="AT+VTS", lines=[], final=self.call_final)

    def set_speaker_volume(self, level):
        self.calls.append(("set_speaker_volume", level))
        return ATResponse(command="AT+CLVL", lines=[], final=self.call_final)

    def mute_microphone(self, enabled):
        self.calls.append(("mute_microphone", enabled))
        return ATResponse(command="AT+CMUT", lines=[], final=self.call_final)

    def enable_event_notifications(self):
        self.calls.append("enable_event_notifications")

    def monitor_events(self, seconds=None):
        self.calls.append(("monitor_events", seconds))
        yield "RING"


def args_for(**overrides):
    values = {
        "json": False,
        "port": "COM8",
        "profile": "generic",
        "baud": 115200,
        "timeout": 1.0,
        "no_init": False,
        "number": "+123",
        "text": "hello",
        "encoding": "auto",
        "index": 1,
        "status": "ALL",
        "at_command": "ATI",
        "command_timeout": 5.0,
        "digits": "12#",
        "duration": None,
        "level": 50,
        "state": "off",
        "enable_events": False,
        "seconds": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@contextmanager
def fake_context(fake):
    yield fake


def patched_modem(fake):
    return patch("cellular_modem.cli._open_modem", side_effect=lambda args: fake_context(fake))


def run_silent(handler, args):
    output = io.StringIO()
    with redirect_stdout(output):
        return handler(args)


if __name__ == "__main__":
    unittest.main()

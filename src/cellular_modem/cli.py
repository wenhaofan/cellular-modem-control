"""Command line interface for cellular modem control."""

from __future__ import annotations

import argparse
import json
import os
import sys
from contextlib import contextmanager
from dataclasses import is_dataclass
from typing import Any

from .at import ATError, ATTimeout
from .modem import Modem
from .profiles import PROFILES
from .smoke import report_to_dict, report_to_markdown, run_read_only_smoke


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "handler"):
        parser.print_help()
        return 2

    try:
        return args.handler(args)
    except (ATError, ATTimeout, OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="modemctl", description="Control a cellular modem over AT serial.")
    parser.add_argument("--port", default=_default_port(), help="Serial AT port. Defaults to COM8 on Windows.")
    parser.add_argument(
        "--baud",
        type=int,
        default=int(os.getenv("MODEM_BAUD", os.getenv("QUECTEL_MODEM_BAUD", "115200"))),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("MODEM_TIMEOUT", os.getenv("QUECTEL_MODEM_TIMEOUT", "1.0"))),
    )
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILES),
        default=os.getenv("MODEM_PROFILE", "generic"),
        help="AT command profile. Defaults to generic standard commands.",
    )
    parser.add_argument("--no-init", action="store_true", help="Skip AT/ATE0/CMEE initialization.")
    parser.add_argument("--json", action="store_true", help="Print structured output as JSON where supported.")

    subparsers = parser.add_subparsers(dest="command")

    _add(subparsers, "ports", cmd_ports, "List serial ports.")
    _add(subparsers, "info", cmd_info, "Show module identity.")
    _add(subparsers, "sim", cmd_sim, "Show SIM PIN/ready status.")
    _add(subparsers, "signal", cmd_signal, "Show signal quality.")

    smoke = _add(subparsers, "smoke", cmd_smoke, "Run read-only hardware smoke checks.")
    smoke.add_argument(
        "--format",
        choices=["plain", "json", "markdown"],
        default="plain",
        help="Smoke report output format. --json is kept as a global shortcut for JSON.",
    )
    smoke.add_argument("--show-sensitive", action="store_true", help="Do not redact modem identifiers in the report.")

    raw = _add(subparsers, "raw", cmd_raw, "Run a raw AT command.")
    raw.add_argument("at_command")
    raw.add_argument("--command-timeout", type=float, default=5.0)

    sms_send = _add(subparsers, "sms-send", cmd_sms_send, "Send an SMS.")
    sms_send.add_argument("number")
    sms_send.add_argument("text")
    sms_send.add_argument("--encoding", choices=["auto", "gsm", "ucs2"], default="auto")

    sms_list = _add(subparsers, "sms-list", cmd_sms_list, "List SMS messages.")
    sms_list.add_argument("--status", default="ALL", help='ALL, "REC UNREAD", "REC READ", etc.')

    sms_read = _add(subparsers, "sms-read", cmd_sms_read, "Read an SMS by storage index.")
    sms_read.add_argument("index", type=int)

    sms_delete = _add(subparsers, "sms-delete", cmd_sms_delete, "Delete an SMS by storage index.")
    sms_delete.add_argument("index", type=int)

    call_dial = _add(subparsers, "call-dial", cmd_call_dial, "Dial a voice call.")
    call_dial.add_argument("number")

    _add(subparsers, "call-answer", cmd_call_answer, "Answer an incoming call.")
    _add(subparsers, "call-hangup", cmd_call_hangup, "Hang up the current call.")
    _add(subparsers, "call-list", cmd_call_list, "List active calls.")

    dtmf = _add(subparsers, "dtmf", cmd_dtmf, "Send DTMF digits during a call.")
    dtmf.add_argument("digits")
    dtmf.add_argument("--duration", type=int)

    volume = _add(subparsers, "audio-volume", cmd_audio_volume, "Set speaker volume if supported.")
    volume.add_argument("level", type=int)

    mute = _add(subparsers, "audio-mute", cmd_audio_mute, "Mute or unmute microphone if supported.")
    mute.add_argument("state", choices=["on", "off"])

    monitor = _add(subparsers, "monitor", cmd_monitor, "Print unsolicited modem events.")
    monitor.add_argument("--seconds", type=float, help="Stop after this many seconds. Default is forever.")
    monitor.add_argument("--enable-events", action="store_true", help="Enable CLIP and SMS indications first.")

    return parser


def _add(subparsers, name: str, handler, help_text: str):
    parser = subparsers.add_parser(name, help=help_text, description=help_text)
    parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    parser.set_defaults(handler=handler)
    return parser


def cmd_ports(args) -> int:
    try:
        from serial.tools import list_ports
    except ImportError as exc:
        raise RuntimeError("pyserial is required: python -m pip install pyserial") from exc
    ports = [
        {
            "device": port.device,
            "description": port.description,
            "hwid": port.hwid,
        }
        for port in list_ports.comports()
    ]
    _print(ports, args.json)
    return 0


def cmd_info(args) -> int:
    with _open_modem(args) as modem:
        _print(modem.info(), args.json)
    return 0


def cmd_sim(args) -> int:
    with _open_modem(args) as modem:
        _print({"sim": modem.sim_status()}, args.json)
    return 0


def cmd_signal(args) -> int:
    with _open_modem(args) as modem:
        _print(modem.signal_quality(), args.json)
    return 0


def cmd_smoke(args) -> int:
    report = run_read_only_smoke(
        port=args.port,
        profile=args.profile,
        baudrate=args.baud,
        timeout=args.timeout,
        initialize=not args.no_init,
        show_sensitive=args.show_sensitive,
    )
    if args.json or args.format == "json":
        print(json.dumps(report_to_dict(report), ensure_ascii=False, indent=2))
    elif args.format == "markdown":
        print(report_to_markdown(report))
    else:
        _print(report_to_dict(report), False)
    return 0 if report.ok else 1


def cmd_raw(args) -> int:
    with _open_modem(args) as modem:
        response = modem.raw(args.at_command, timeout=args.command_timeout)
        _print({"final": response.final, "lines": response.lines}, args.json)
    return 0 if response.final == "OK" else 1


def cmd_sms_send(args) -> int:
    with _open_modem(args) as modem:
        reference = modem.send_sms(args.number, args.text, encoding=args.encoding)
        _print({"message_reference": reference}, args.json)
    return 0


def cmd_sms_list(args) -> int:
    with _open_modem(args) as modem:
        _print(modem.list_sms(status=args.status), args.json)
    return 0


def cmd_sms_read(args) -> int:
    with _open_modem(args) as modem:
        _print(modem.read_sms(args.index), args.json)
    return 0


def cmd_sms_delete(args) -> int:
    with _open_modem(args) as modem:
        modem.delete_sms(args.index)
    print(f"deleted SMS index {args.index}")
    return 0


def cmd_call_dial(args) -> int:
    with _open_modem(args) as modem:
        response = modem.dial(args.number)
        _print({"final": response.final, "lines": response.lines}, args.json)
    return 0 if response.final == "OK" else 1


def cmd_call_answer(args) -> int:
    with _open_modem(args) as modem:
        response = modem.answer()
        _print({"final": response.final, "lines": response.lines}, args.json)
    return 0 if response.final == "OK" else 1


def cmd_call_hangup(args) -> int:
    with _open_modem(args) as modem:
        response = modem.hangup()
        _print({"final": response.final, "lines": response.lines}, args.json)
    return 0 if response.final == "OK" else 1


def cmd_call_list(args) -> int:
    with _open_modem(args) as modem:
        _print(modem.list_calls(), args.json)
    return 0


def cmd_dtmf(args) -> int:
    with _open_modem(args) as modem:
        response = modem.send_dtmf(args.digits, duration=args.duration)
        _print({"final": response.final, "lines": response.lines}, args.json)
    return 0 if response.final == "OK" else 1


def cmd_audio_volume(args) -> int:
    with _open_modem(args) as modem:
        response = modem.set_speaker_volume(args.level)
        _print({"final": response.final, "lines": response.lines}, args.json)
    return 0 if response.final == "OK" else 1


def cmd_audio_mute(args) -> int:
    with _open_modem(args) as modem:
        response = modem.mute_microphone(args.state == "on")
        _print({"final": response.final, "lines": response.lines}, args.json)
    return 0 if response.final == "OK" else 1


def cmd_monitor(args) -> int:
    with _open_modem(args) as modem:
        if args.enable_events:
            modem.enable_event_notifications()
        for line in modem.monitor_events(seconds=args.seconds):
            print(line, flush=True)
    return 0


@contextmanager
def _open_modem(args):
    modem = Modem(port=args.port, baudrate=args.baud, timeout=args.timeout, profile=args.profile).open()
    try:
        if not args.no_init:
            modem.initialize()
        yield modem
    finally:
        modem.close()


def _print(value: Any, as_json: bool) -> None:
    normalized = _normalize(value)
    if as_json:
        print(json.dumps(normalized, ensure_ascii=False, indent=2))
        return
    if isinstance(normalized, list):
        for item in normalized:
            print(_format_plain(item))
        return
    print(_format_plain(normalized))


def _normalize(value: Any) -> Any:
    dataclass_fields = getattr(value, "__dataclass_fields__", None)
    if dataclass_fields is not None and is_dataclass(value) and not isinstance(value, type):
        return {key: _normalize(getattr(value, key)) for key in dataclass_fields}
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize(item) for key, item in value.items()}
    return value


def _format_plain(value: Any) -> str:
    if isinstance(value, dict):
        return "\n".join(f"{key}: {item}" for key, item in value.items())
    return str(value)


def _default_port() -> str:
    configured = os.getenv("MODEM_PORT") or os.getenv("QUECTEL_MODEM_PORT")
    if configured:
        return configured
    return "COM8" if os.name == "nt" else "/dev/ttyUSB2"


if __name__ == "__main__":
    raise SystemExit(main())

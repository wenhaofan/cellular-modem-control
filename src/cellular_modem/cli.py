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
from .ports import SerialPortInfo, detect_serial_port, list_serial_ports, probe_serial_ports
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
    parser.add_argument(
        "--port",
        default=_default_port(),
        help="Serial AT port, or 'auto' to probe visible ports. Defaults to MODEM_PORT or auto.",
    )
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
    probe = _add(subparsers, "probe", cmd_probe, "Probe serial ports for an AT-responsive modem.")
    probe.add_argument("--command", default="ATI", help="Read-only AT command used after the initial AT probe.")
    _add(subparsers, "info", cmd_info, "Show module identity.")
    sim = _add(subparsers, "sim", cmd_sim, "Show SIM status, IMSI/ICCID, operator, and subscriber numbers.")
    sim.add_argument("--show-sensitive", action="store_true", help="Do not redact IMSI, ICCID, or phone numbers.")
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
    _add_dry_run(raw)

    sms_send = _add(subparsers, "sms-send", cmd_sms_send, "Send an SMS.")
    sms_send.add_argument("number")
    sms_send.add_argument("text")
    sms_send.add_argument("--encoding", choices=["auto", "gsm", "ucs2"], default="auto")
    _add_dry_run(sms_send)

    sms_list = _add(subparsers, "sms-list", cmd_sms_list, "List SMS messages.")
    sms_list.add_argument("--status", default="ALL", help='ALL, "REC UNREAD", "REC READ", etc.')

    sms_read = _add(subparsers, "sms-read", cmd_sms_read, "Read an SMS by storage index.")
    sms_read.add_argument("index", type=int)

    sms_delete = _add(subparsers, "sms-delete", cmd_sms_delete, "Delete an SMS by storage index.")
    sms_delete.add_argument("index", type=int)
    _add_dry_run(sms_delete)

    sms_mode = _add(subparsers, "sms-mode", cmd_sms_mode, "Show or set SMS mode: text or PDU.")
    sms_mode.add_argument("mode", nargs="?", choices=["text", "pdu"], help="Set SMS mode. Omit to query current mode.")
    _add_dry_run(sms_mode)

    call_dial = _add(subparsers, "call-dial", cmd_call_dial, "Dial a voice call.")
    call_dial.add_argument("number")
    _add_dry_run(call_dial)

    call_answer = _add(subparsers, "call-answer", cmd_call_answer, "Answer an incoming call.")
    _add_dry_run(call_answer)
    call_hangup = _add(subparsers, "call-hangup", cmd_call_hangup, "Hang up the current call.")
    _add_dry_run(call_hangup)
    _add(subparsers, "call-list", cmd_call_list, "List active calls.")

    dtmf = _add(subparsers, "dtmf", cmd_dtmf, "Send DTMF digits during a call.")
    dtmf.add_argument("digits")
    dtmf.add_argument("--duration", type=int)
    _add_dry_run(dtmf)

    volume = _add(subparsers, "audio-volume", cmd_audio_volume, "Set speaker volume if supported.")
    volume.add_argument("level", type=int)
    _add_dry_run(volume)

    mute = _add(subparsers, "audio-mute", cmd_audio_mute, "Mute or unmute microphone if supported.")
    mute.add_argument("state", choices=["on", "off"])
    _add_dry_run(mute)

    monitor = _add(subparsers, "monitor", cmd_monitor, "Print unsolicited modem events.")
    monitor.add_argument("--seconds", type=float, help="Stop after this many seconds. Default is forever.")
    monitor.add_argument("--enable-events", action="store_true", help="Enable CLIP and SMS indications first.")

    return parser


def _add(subparsers, name: str, handler, help_text: str):
    parser = subparsers.add_parser(name, help=help_text, description=help_text)
    parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    parser.set_defaults(handler=handler)
    return parser


def _add_dry_run(parser) -> None:
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the intended operation without opening the modem.",
    )


def cmd_ports(args) -> int:
    _print(list_serial_ports(), args.json)
    return 0


def cmd_probe(args) -> int:
    ports = None
    if args.port.lower() != "auto":
        ports = [SerialPortInfo(device=args.port, description="explicit", hwid="")]
    probes = probe_serial_ports(ports=ports, baudrate=args.baud, timeout=args.timeout, command=args.command)
    _print(probes, args.json)
    return 0 if any(probe.responsive for probe in probes) else 1


def cmd_info(args) -> int:
    with _open_modem(args) as modem:
        _print(modem.info(), args.json)
    return 0


def cmd_sim(args) -> int:
    with _open_modem(args) as modem:
        _print(modem.sim_info(show_sensitive=args.show_sensitive), args.json)
    return 0


def cmd_signal(args) -> int:
    with _open_modem(args) as modem:
        _print(modem.signal_quality(), args.json)
    return 0


def cmd_smoke(args) -> int:
    port = _resolve_port(args)
    report = run_read_only_smoke(
        port=port,
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
    if args.dry_run:
        return _dry_run(args, "raw", at_command=args.at_command, command_timeout=args.command_timeout)
    with _open_modem(args) as modem:
        response = modem.raw(args.at_command, timeout=args.command_timeout)
        _print({"final": response.final, "lines": response.lines}, args.json)
    return 0 if response.final == "OK" else 1


def cmd_sms_send(args) -> int:
    if args.dry_run:
        return _dry_run(
            args,
            "sms-send",
            number=args.number,
            encoding=args.encoding,
            text_length=len(args.text),
        )
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
    if args.dry_run:
        return _dry_run(args, "sms-delete", index=args.index)
    with _open_modem(args) as modem:
        modem.delete_sms(args.index)
    print(f"deleted SMS index {args.index}")
    return 0


def cmd_sms_mode(args) -> int:
    if args.mode:
        if args.dry_run:
            return _dry_run(args, "sms-mode", mode=args.mode)
        with _open_modem(args) as modem:
            response = modem.set_sms_mode(args.mode)
            _print({"mode": args.mode, "final": response.final, "lines": response.lines}, args.json)
        return 0 if response.final == "OK" else 1
    with _open_modem(args) as modem:
        _print({"sms_mode": modem.sms_mode()}, args.json)
    return 0


def cmd_call_dial(args) -> int:
    if args.dry_run:
        return _dry_run(args, "call-dial", number=args.number)
    with _open_modem(args) as modem:
        response = modem.dial(args.number)
        _print({"final": response.final, "lines": response.lines}, args.json)
    return 0 if response.final == "OK" else 1


def cmd_call_answer(args) -> int:
    if args.dry_run:
        return _dry_run(args, "call-answer")
    with _open_modem(args) as modem:
        response = modem.answer()
        _print({"final": response.final, "lines": response.lines}, args.json)
    return 0 if response.final == "OK" else 1


def cmd_call_hangup(args) -> int:
    if args.dry_run:
        return _dry_run(args, "call-hangup")
    with _open_modem(args) as modem:
        response = modem.hangup()
        _print({"final": response.final, "lines": response.lines}, args.json)
    return 0 if response.final == "OK" else 1


def cmd_call_list(args) -> int:
    with _open_modem(args) as modem:
        _print(modem.list_calls(), args.json)
    return 0


def cmd_dtmf(args) -> int:
    if args.dry_run:
        return _dry_run(args, "dtmf", digits_length=len(args.digits), duration=args.duration)
    with _open_modem(args) as modem:
        response = modem.send_dtmf(args.digits, duration=args.duration)
        _print({"final": response.final, "lines": response.lines}, args.json)
    return 0 if response.final == "OK" else 1


def cmd_audio_volume(args) -> int:
    if args.dry_run:
        return _dry_run(args, "audio-volume", level=args.level)
    with _open_modem(args) as modem:
        response = modem.set_speaker_volume(args.level)
        _print({"final": response.final, "lines": response.lines}, args.json)
    return 0 if response.final == "OK" else 1


def cmd_audio_mute(args) -> int:
    if args.dry_run:
        return _dry_run(args, "audio-mute", state=args.state)
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
    modem = Modem(port=_resolve_port(args), baudrate=args.baud, timeout=args.timeout, profile=args.profile).open()
    try:
        if not args.no_init:
            modem.initialize()
        yield modem
    finally:
        modem.close()


def _resolve_port(args) -> str:
    port = args.port
    if port and port.lower() != "auto":
        return port
    return detect_serial_port(baudrate=args.baud, timeout=args.timeout)


def _dry_run(args, action: str, **details: Any) -> int:
    payload = {
        "dry_run": True,
        "action": action,
        "port": args.port,
        "profile": args.profile,
        **details,
    }
    _print(payload, args.json)
    return 0


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
    return "auto"


if __name__ == "__main__":
    raise SystemExit(main())

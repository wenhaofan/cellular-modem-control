"""High-level cellular modem operations using mostly standard AT commands."""

from __future__ import annotations

import csv
import re
from collections.abc import Iterable
from dataclasses import dataclass

from .at import ATClient, ATResponse, SerialTransport
from .encoding import encode_ucs2, maybe_decode_ucs2, needs_ucs2
from .profiles import ModemProfile, get_profile

DEFAULT_BAUDRATE = 115200
CMGS_RE = re.compile(r"^\+CMGS:\s*(?P<mr>\d+)")


@dataclass(frozen=True)
class SMSMessage:
    index: int | None
    status: str
    sender: str
    timestamp: str
    text: str


@dataclass(frozen=True)
class CallInfo:
    index: int
    direction: int
    status: int
    mode: int
    multiparty: int
    number: str | None = None
    number_type: int | None = None


class Modem:
    """High-level convenience API for a cellular AT-command modem."""

    def __init__(
        self,
        port: str,
        baudrate: int = DEFAULT_BAUDRATE,
        timeout: float = 1.0,
        profile: str | ModemProfile | None = "generic",
    ):
        transport = SerialTransport(port=port, baudrate=baudrate, timeout=timeout)
        self.client = ATClient(transport)
        self.profile = get_profile(profile)

    def open(self) -> Modem:
        self.client.open()
        return self

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> Modem:
        return self.open()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def initialize(self) -> None:
        for command in self.profile.basic_init_commands:
            self.client.command(command, timeout=3.0)
        for command in self.profile.caller_id_commands:
            self.client.command(command, timeout=3.0, raise_on_error=False)

    def raw(self, command: str, timeout: float = 5.0) -> ATResponse:
        return self.client.command(command, timeout=timeout, raise_on_error=False)

    def info(self) -> dict[str, str | list[str]]:
        responses = {
            "manufacturer": self.client.command("AT+CGMI").lines,
            "model": self.client.command("AT+CGMM").lines,
            "revision": self.client.command("AT+CGMR").lines,
            "imei": self.client.command("AT+CGSN").lines,
        }
        return {key: _join_lines(value) for key, value in responses.items()}

    def sim_status(self) -> str:
        response = self.client.command("AT+CPIN?")
        return _first_payload_value(response.lines, "+CPIN:")

    def signal_quality(self) -> dict[str, int | None]:
        response = self.client.command("AT+CSQ")
        value = _first_payload_value(response.lines, "+CSQ:")
        parts = [part.strip() for part in value.split(",")]
        rssi_raw = int(parts[0]) if parts and parts[0].isdigit() else 99
        ber = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
        dbm = None if rssi_raw == 99 else -113 + (2 * rssi_raw)
        return {"rssi": rssi_raw, "dbm": dbm, "ber": ber}

    def enable_event_notifications(self) -> None:
        for command in self.profile.event_commands:
            self.client.command(command, raise_on_error=False)

    def set_sms_text_mode(self, charset: str = "GSM", dcs: int = 0) -> None:
        self.client.command("AT+CMGF=1")
        self.client.command(f'AT+CSCS="{charset}"')
        self.client.command(f"AT+CSMP=17,167,0,{dcs}", raise_on_error=False)

    def send_sms(self, number: str, text: str, encoding: str = "auto") -> int | None:
        selected = _select_encoding(text, encoding)
        if selected == "ucs2":
            if not self.profile.supports_ucs2_sms:
                raise ValueError(f"profile {self.profile.name!r} does not declare UCS2 SMS support")
            self.set_sms_text_mode(charset="UCS2", dcs=8)
            target = encode_ucs2(number)
            payload = encode_ucs2(text).encode("ascii")
        else:
            self.set_sms_text_mode(charset="GSM", dcs=0)
            target = number
            payload = text.encode("ascii", errors="replace")

        response = self.client.command_with_prompt(f'AT+CMGS="{target}"', payload=payload, timeout=60.0)
        for line in response.lines:
            match = CMGS_RE.match(line)
            if match:
                return int(match.group("mr"))
        return None

    def list_sms(self, status: str = "ALL") -> list[SMSMessage]:
        self.set_sms_text_mode(charset="UCS2", dcs=8)
        response = self.client.command(f'AT+CMGL="{status}"', timeout=20.0)
        return _parse_cmgl(response.lines)

    def read_sms(self, index: int) -> SMSMessage:
        self.set_sms_text_mode(charset="UCS2", dcs=8)
        response = self.client.command(f"AT+CMGR={index}", timeout=10.0)
        return _parse_cmgr(index, response.lines)

    def delete_sms(self, index: int) -> None:
        self.client.command(f"AT+CMGD={index}")

    def dial(self, number: str) -> ATResponse:
        return self.client.command(self.profile.dial_command(number), timeout=10.0, raise_on_error=False)

    def answer(self) -> ATResponse:
        return self.client.command(self.profile.answer_command(), timeout=10.0, raise_on_error=False)

    def hangup(self) -> ATResponse:
        return self.client.command(self.profile.hangup_command(), timeout=10.0, raise_on_error=False)

    def send_dtmf(self, digits: str, duration: int | None = None) -> ATResponse:
        return self.client.command(self.profile.dtmf_command(digits, duration), timeout=10.0, raise_on_error=False)

    def list_calls(self) -> list[CallInfo]:
        response = self.client.command("AT+CLCC", timeout=5.0, raise_on_error=False)
        return _parse_clcc(response.lines)

    def set_speaker_volume(self, level: int) -> ATResponse:
        if not 0 <= level <= 100:
            raise ValueError("level must be between 0 and 100")
        return self.client.command(self.profile.speaker_volume_command(level), raise_on_error=False)

    def mute_microphone(self, enabled: bool) -> ATResponse:
        return self.client.command(self.profile.microphone_mute_command(enabled), raise_on_error=False)

    def monitor_events(self, seconds: float | None = None) -> Iterable[str]:
        yield from self.client.read_unsolicited(timeout=seconds)


def _select_encoding(text: str, encoding: str) -> str:
    normalized = encoding.lower()
    if normalized not in {"auto", "gsm", "ucs2"}:
        raise ValueError("encoding must be one of: auto, gsm, ucs2")
    if normalized == "auto":
        return "ucs2" if needs_ucs2(text) else "gsm"
    return normalized


def _join_lines(lines: list[str]) -> str | list[str]:
    if len(lines) == 1:
        return lines[0]
    return lines


def _first_payload_value(lines: list[str], prefix: str) -> str:
    for line in lines:
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    raise ValueError(f"response did not contain {prefix}")


def _parse_cmgl(lines: list[str]) -> list[SMSMessage]:
    messages: list[SMSMessage] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.startswith("+CMGL:"):
            index += 1
            continue
        fields = _parse_header_fields(line)
        text = ""
        if index + 1 < len(lines) and not lines[index + 1].startswith("+CMGL:"):
            text = maybe_decode_ucs2(lines[index + 1])
            index += 1
        messages.append(
            SMSMessage(
                index=_int_or_none(fields[0] if fields else None),
                status=maybe_decode_ucs2(fields[1]) if len(fields) > 1 else "",
                sender=maybe_decode_ucs2(fields[2]) if len(fields) > 2 else "",
                timestamp=maybe_decode_ucs2(fields[4]) if len(fields) > 4 else "",
                text=text,
            )
        )
        index += 1
    return messages


def _parse_cmgr(index: int, lines: list[str]) -> SMSMessage:
    if not lines or not lines[0].startswith("+CMGR:"):
        raise ValueError("response did not contain +CMGR")
    fields = _parse_header_fields(lines[0])
    text = maybe_decode_ucs2(lines[1]) if len(lines) > 1 else ""
    return SMSMessage(
        index=index,
        status=maybe_decode_ucs2(fields[0]) if fields else "",
        sender=maybe_decode_ucs2(fields[1]) if len(fields) > 1 else "",
        timestamp=maybe_decode_ucs2(fields[3]) if len(fields) > 3 else "",
        text=text,
    )


def _parse_clcc(lines: list[str]) -> list[CallInfo]:
    calls: list[CallInfo] = []
    for line in lines:
        if not line.startswith("+CLCC:"):
            continue
        fields = _parse_header_fields(line)
        if len(fields) < 5:
            continue
        calls.append(
            CallInfo(
                index=int(fields[0]),
                direction=int(fields[1]),
                status=int(fields[2]),
                mode=int(fields[3]),
                multiparty=int(fields[4]),
                number=fields[5] if len(fields) > 5 and fields[5] else None,
                number_type=_int_or_none(fields[6] if len(fields) > 6 else None),
            )
        )
    return calls


def _parse_header_fields(line: str) -> list[str]:
    _, payload = line.split(":", 1)
    return next(csv.reader([payload.strip()], skipinitialspace=True))


def _int_or_none(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None

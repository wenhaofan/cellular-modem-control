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

    def sim_info(self, show_sensitive: bool = False) -> dict[str, object]:
        info: dict[str, object] = {
            "status": self.sim_status(),
            "imsi": self._optional_line("AT+CIMI"),
            "iccid": self._optional_payload("AT+CCID", prefixes=("+CCID:", "+QCCID:")),
            "operator": self._operator_info(),
            "numbers": self._subscriber_numbers(),
        }
        return info if show_sensitive else _redact_sensitive(info)

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
        self.set_sms_mode("text")
        self.client.command(f'AT+CSCS="{charset}"')
        self.client.command(f"AT+CSMP=17,167,0,{dcs}", raise_on_error=False)

    def set_sms_pdu_mode(self) -> ATResponse:
        return self.set_sms_mode("pdu")

    def set_sms_mode(self, mode: str) -> ATResponse:
        normalized = mode.lower()
        if normalized not in {"text", "pdu"}:
            raise ValueError("mode must be one of: text, pdu")
        return self.client.command(f"AT+CMGF={1 if normalized == 'text' else 0}")

    def sms_mode(self) -> str:
        response = self.client.command("AT+CMGF?")
        value = _first_payload_value(response.lines, "+CMGF:").strip()
        return {"0": "pdu", "1": "text"}.get(value, value)

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

    def _optional_line(self, command: str) -> str | None:
        response = self.client.command(command, timeout=5.0, raise_on_error=False)
        if response.final != "OK":
            return None
        return _first_nonempty_line(response.lines)

    def _optional_payload(self, command: str, prefixes: tuple[str, ...]) -> str | None:
        response = self.client.command(command, timeout=5.0, raise_on_error=False)
        if response.final != "OK":
            return None
        for prefix in prefixes:
            value = _first_payload_value_or_none(response.lines, prefix)
            if value:
                return value.strip().strip('"')
        return _first_nonempty_line(response.lines)

    def _operator_info(self) -> dict[str, str | None] | None:
        response = self.client.command("AT+COPS?", timeout=5.0, raise_on_error=False)
        if response.final != "OK":
            return None
        value = _first_payload_value_or_none(response.lines, "+COPS:")
        if not value:
            return None
        fields = next(csv.reader([value], skipinitialspace=True))
        return {
            "mode": fields[0] if len(fields) > 0 else None,
            "format": fields[1] if len(fields) > 1 else None,
            "name": maybe_decode_ucs2(fields[2]) if len(fields) > 2 else None,
            "access_technology": fields[3] if len(fields) > 3 else None,
        }

    def _subscriber_numbers(self) -> list[dict[str, str | None]]:
        response = self.client.command("AT+CNUM", timeout=5.0, raise_on_error=False)
        if response.final != "OK":
            return []
        numbers = []
        for line in response.lines:
            if not line.startswith("+CNUM:"):
                continue
            fields = _parse_header_fields(line)
            numbers.append(
                {
                    "alpha": maybe_decode_ucs2(fields[0]) if len(fields) > 0 else None,
                    "number": maybe_decode_ucs2(fields[1]) if len(fields) > 1 else None,
                    "type": fields[2] if len(fields) > 2 else None,
                }
            )
        return numbers


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


def _first_payload_value_or_none(lines: list[str], prefix: str) -> str | None:
    for line in lines:
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return None


def _first_nonempty_line(lines: list[str]) -> str | None:
    return next((line.strip() for line in lines if line.strip()), None)


def _redact_sensitive(value, key_hint: str | None = None):
    sensitive_keys = {"imsi", "iccid", "number"}
    if isinstance(value, dict):
        return {key: _redact_sensitive(item, key_hint=str(key).lower()) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_sensitive(item, key_hint=key_hint) for item in value]
    if isinstance(value, str) and key_hint in sensitive_keys:
        return _redact_identifier(value)
    return value


def _redact_identifier(value: str) -> str:
    if len(value) <= 4:
        return "***"
    return f"{value[:2]}***{value[-2:]}"


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

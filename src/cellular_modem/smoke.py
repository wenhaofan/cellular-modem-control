"""Read-only hardware smoke checks for cellular modems."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from .modem import DEFAULT_BAUDRATE, Modem

SENSITIVE_KEYS = {"imei", "imsi", "iccid", "phone", "number", "sender", "recipient"}


@dataclass(frozen=True)
class SmokeCheck:
    name: str
    ok: bool
    value: Any = None
    error: str | None = None


@dataclass(frozen=True)
class SmokeReport:
    port: str
    profile: str
    checks: list[SmokeCheck]
    sensitive_redacted: bool = True

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks)


class ModemLike(Protocol):
    def open(self) -> ModemLike:
        ...

    def close(self) -> None:
        ...

    def initialize(self) -> None:
        ...

    def info(self) -> dict[str, str | list[str]]:
        ...

    def sim_info(self, show_sensitive: bool = False) -> dict[str, Any]:
        ...

    def signal_quality(self) -> dict[str, int | None]:
        ...

    def raw(self, command: str, timeout: float = 5.0):
        ...


class ModemFactory(Protocol):
    def __call__(self, port: str, baudrate: int, timeout: float, profile: str) -> ModemLike:
        ...


def run_read_only_smoke(
    port: str,
    profile: str = "generic",
    baudrate: int = DEFAULT_BAUDRATE,
    timeout: float = 1.0,
    initialize: bool = True,
    show_sensitive: bool = False,
    modem_factory: ModemFactory = Modem,
) -> SmokeReport:
    """Run non-destructive modem checks and return a structured report."""

    modem: ModemLike | None = None
    checks: list[SmokeCheck] = []
    redacted = not show_sensitive

    try:
        modem = modem_factory(port=port, baudrate=baudrate, timeout=timeout, profile=profile).open()
        checks.append(SmokeCheck(name="open", ok=True, value="OK"))
    except Exception as exc:  # noqa: BLE001 - hardware smoke should report all open failures
        checks.append(SmokeCheck(name="open", ok=False, error=_error_message(exc)))
        return SmokeReport(port=port, profile=profile, checks=checks, sensitive_redacted=redacted)

    try:
        if initialize:
            checks.append(_check("initialize", lambda: _initialize_modem(modem), show_sensitive=show_sensitive))
        else:
            checks.append(SmokeCheck(name="initialize", ok=True, value="SKIPPED"))
        checks.append(_check("info", modem.info, show_sensitive=show_sensitive))
        checks.append(
            _check("sim", lambda: modem.sim_info(show_sensitive=show_sensitive), show_sensitive=show_sensitive)
        )
        checks.append(_check("signal", modem.signal_quality, show_sensitive=show_sensitive))
        checks.append(_check("ati", lambda: _raw_response(modem.raw("ATI")), show_sensitive=show_sensitive))
    finally:
        modem.close()

    return SmokeReport(port=port, profile=profile, checks=checks, sensitive_redacted=redacted)


def report_to_dict(report: SmokeReport) -> dict[str, Any]:
    return {
        "ok": report.ok,
        "port": report.port,
        "profile": report.profile,
        "sensitive_redacted": report.sensitive_redacted,
        "checks": [
            {
                "name": check.name,
                "ok": check.ok,
                "value": check.value,
                "error": check.error,
            }
            for check in report.checks
        ],
    }


def report_to_markdown(report: SmokeReport) -> str:
    payload = report_to_dict(report)
    lines = [
        "# Modem Smoke Report",
        "",
        f"- Overall: {'PASS' if report.ok else 'FAIL'}",
        f"- Port: `{report.port}`",
        f"- Profile: `{report.profile}`",
        f"- Sensitive values redacted: `{str(report.sensitive_redacted).lower()}`",
        "",
        "| Check | Result | Value | Error |",
        "| --- | --- | --- | --- |",
    ]
    for check in payload["checks"]:
        result = "PASS" if check["ok"] else "FAIL"
        value = _markdown_value(check["value"])
        error = _markdown_value(check["error"])
        lines.append(f"| `{check['name']}` | {result} | {value} | {error} |")
    return "\n".join(lines)


def _check(name: str, func, show_sensitive: bool) -> SmokeCheck:
    try:
        value = func()
    except Exception as exc:  # noqa: BLE001 - report check failures instead of aborting the whole smoke run
        return SmokeCheck(name=name, ok=False, error=_error_message(exc))
    return SmokeCheck(name=name, ok=True, value=value if show_sensitive else _redact(value))


def _markdown_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return f"`{_escape_markdown_table(value)}`"
    return f"`{_escape_markdown_table(json.dumps(value, ensure_ascii=False, sort_keys=True))}`"


def _escape_markdown_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _initialize_modem(modem: ModemLike) -> str:
    modem.initialize()
    return "OK"


def _raw_response(response) -> dict[str, Any]:
    return {"final": response.final, "lines": response.lines}


def _redact(value: Any, key_hint: str | None = None) -> Any:
    if isinstance(value, dict):
        return {key: _redact(item, key_hint=str(key).lower()) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item, key_hint=key_hint) for item in value]
    if isinstance(value, str) and key_hint in SENSITIVE_KEYS:
        return _redact_identifier(value)
    return value


def _redact_identifier(value: str) -> str:
    if len(value) <= 4:
        return "***"
    return f"{value[:2]}***{value[-2:]}"


def _error_message(exc: Exception) -> str:
    return f"{exc.__class__.__name__}: {exc}"

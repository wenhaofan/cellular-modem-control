"""Small AT-command client built on pyserial."""

from __future__ import annotations

import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

FINAL_LINES = {"OK", "ERROR", "NO CARRIER", "BUSY", "NO ANSWER", "NO DIALTONE"}
ERROR_PREFIXES = ("+CME ERROR:", "+CMS ERROR:")


class ATTimeout(TimeoutError):
    """Raised when the modem does not complete an AT operation in time."""


@dataclass(frozen=True)
class ATResponse:
    command: str
    lines: list[str]
    final: str


class ATError(RuntimeError):
    """Raised when a modem returns an AT error final result."""

    def __init__(self, response: ATResponse):
        self.response = response
        detail = response.final
        if response.lines:
            detail = f"{detail}: {' | '.join(response.lines)}"
        super().__init__(f"{response.command} failed with {detail}")


class SerialTransport:
    """Thin serial wrapper with predictable AT line handling."""

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        timeout: float = 1.0,
        write_timeout: float = 2.0,
        rtscts: bool = False,
        dsrdtr: bool = False,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.write_timeout = write_timeout
        self.rtscts = rtscts
        self.dsrdtr = dsrdtr
        self._serial = None

    def open(self) -> None:
        if self._serial is not None and self._serial.is_open:
            return
        try:
            import serial
        except ImportError as exc:  # pragma: no cover - depends on environment
            raise RuntimeError("pyserial is required: python -m pip install pyserial") from exc

        self._serial = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=self.timeout,
            write_timeout=self.write_timeout,
            rtscts=self.rtscts,
            dsrdtr=self.dsrdtr,
        )

    def close(self) -> None:
        if self._serial is not None:
            self._serial.close()
            self._serial = None

    @property
    def is_open(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def reset_input(self) -> None:
        self._require_open().reset_input_buffer()

    def write_line(self, line: str) -> None:
        self.write_bytes(line.encode("ascii") + b"\r")

    def write_bytes(self, data: bytes) -> None:
        serial_port = self._require_open()
        serial_port.write(data)
        serial_port.flush()

    def read_line(self) -> str | None:
        raw = self._require_open().readline()
        if not raw:
            return None
        return raw.decode("utf-8", errors="replace").strip("\r\n")

    def read_until_prompt(self, timeout: float) -> bytes:
        serial_port = self._require_open()
        end = time.monotonic() + timeout
        buffer = bytearray()
        while time.monotonic() < end:
            chunk = serial_port.read(1)
            if not chunk:
                continue
            buffer.extend(chunk)
            if b">" in buffer:
                return bytes(buffer)
        raise ATTimeout("timed out waiting for SMS prompt")

    def _require_open(self):
        if self._serial is None or not self._serial.is_open:
            raise RuntimeError("serial transport is not open")
        return self._serial


class ATClient:
    """Synchronous AT client for command/response style modem operations."""

    def __init__(self, transport: SerialTransport):
        self.transport = transport

    def open(self) -> ATClient:
        self.transport.open()
        return self

    def close(self) -> None:
        self.transport.close()

    def __enter__(self) -> ATClient:
        return self.open()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def command(
        self,
        command: str,
        timeout: float = 5.0,
        ok_final: Sequence[str] = ("OK",),
        raise_on_error: bool = True,
    ) -> ATResponse:
        self.transport.reset_input()
        self.transport.write_line(command)
        response = self._read_response(command=command, timeout=timeout)
        if raise_on_error and response.final not in ok_final:
            raise ATError(response)
        return response

    def command_with_prompt(
        self,
        command: str,
        payload: bytes,
        timeout: float = 30.0,
        ok_final: Sequence[str] = ("OK",),
        raise_on_error: bool = True,
    ) -> ATResponse:
        self.transport.reset_input()
        self.transport.write_line(command)
        self.transport.read_until_prompt(timeout=min(timeout, 10.0))
        self.transport.write_bytes(payload + b"\x1a")
        response = self._read_response(command=command, timeout=timeout)
        if raise_on_error and response.final not in ok_final:
            raise ATError(response)
        return response

    def read_unsolicited(self, timeout: float | None = None) -> Iterable[str]:
        end = None if timeout is None else time.monotonic() + timeout
        while end is None or time.monotonic() < end:
            line = self.transport.read_line()
            if line is None or line == "":
                continue
            yield line

    def _read_response(self, command: str, timeout: float) -> ATResponse:
        end = time.monotonic() + timeout
        lines: list[str] = []
        while time.monotonic() < end:
            line = self.transport.read_line()
            if line is None or line == "":
                continue
            if line == command:
                continue
            if _is_final(line):
                return ATResponse(command=command, lines=lines, final=line)
            lines.append(line)
        raise ATTimeout(f"{command} timed out after {timeout:g}s")


def _is_final(line: str) -> bool:
    return line in FINAL_LINES or any(line.startswith(prefix) for prefix in ERROR_PREFIXES)

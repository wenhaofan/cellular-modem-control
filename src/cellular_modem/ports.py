"""Serial port discovery helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SerialPortInfo:
    """Portable serial port metadata returned by pyserial."""

    device: str
    description: str
    hwid: str


def list_serial_ports() -> list[SerialPortInfo]:
    """Return serial ports visible to pyserial on the current host."""

    try:
        from serial.tools import list_ports
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("pyserial is required: python -m pip install pyserial") from exc

    return [
        SerialPortInfo(device=port.device, description=port.description, hwid=port.hwid)
        for port in list_ports.comports()
    ]

"""Serial port discovery helpers."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .at import ATClient, SerialTransport


@dataclass(frozen=True)
class SerialPortInfo:
    """Portable serial port metadata returned by pyserial."""

    device: str
    description: str
    hwid: str


@dataclass(frozen=True)
class SerialPortProbe:
    """Result from actively probing a serial port with read-only AT commands."""

    device: str
    description: str
    hwid: str
    responsive: bool
    command: str
    final: str | None = None
    lines: list[str] | None = None
    error: str | None = None


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


def probe_serial_ports(
    ports: Iterable[SerialPortInfo] | None = None,
    baudrate: int = 115200,
    timeout: float = 1.0,
    command: str = "ATI",
) -> list[SerialPortProbe]:
    """Actively probe visible serial ports for an AT-responsive modem.

    The probe opens each candidate port, sends `AT`, then sends the read-only
    identification command provided by `command` when the port responds.
    """

    candidates = list(ports) if ports is not None else list_serial_ports()
    return [_probe_one_port(port, baudrate=baudrate, timeout=timeout, command=command) for port in candidates]


def detect_serial_port(baudrate: int = 115200, timeout: float = 1.0) -> str:
    """Return the first AT-responsive serial port, or raise a helpful error."""

    candidates = sorted(list_serial_ports(), key=_port_priority)
    probes: list[SerialPortProbe] = []
    for port in candidates:
        probe = _probe_one_port(port, baudrate=baudrate, timeout=timeout, command="ATI")
        probes.append(probe)
        if probe.responsive:
            return probe.device

    responsive = [probe for probe in probes if probe.responsive]
    if responsive:
        return responsive[0].device
    if not probes:
        raise RuntimeError("no serial ports found; run `modemctl ports` after connecting the modem")
    devices = ", ".join(probe.device for probe in probes)
    raise RuntimeError(f"no AT-responsive modem detected on: {devices}; pass --port explicitly if needed")


def _port_priority(port: SerialPortInfo) -> tuple[int, str]:
    text = f"{port.device} {port.description} {port.hwid}".lower()
    if " at " in f" {text} " or "at port" in text:
        return (0, port.device)
    if any(token in text for token in ("quectel", "simcom", "fibocom", "sierra", "telit", "u-blox", "ublox")):
        return (1, port.device)
    if any(token in text for token in ("modem", "cellular", "gsm", "lte", "usb serial", "acm")):
        return (2, port.device)
    if any(token in text for token in ("diag", "nmea", "gnss", "bluetooth", "bthenum")):
        return (4, port.device)
    return (3, port.device)


def _probe_one_port(
    port: SerialPortInfo,
    baudrate: int,
    timeout: float,
    command: str,
) -> SerialPortProbe:
    client = ATClient(SerialTransport(port=port.device, baudrate=baudrate, timeout=timeout))
    try:
        client.open()
        response = client.command("AT", timeout=timeout, raise_on_error=False)
        if response.final != "OK":
            return SerialPortProbe(
                device=port.device,
                description=port.description,
                hwid=port.hwid,
                responsive=False,
                command="AT",
                final=response.final,
                lines=response.lines,
            )
        detail = client.command(command, timeout=max(timeout, 2.0), raise_on_error=False)
        return SerialPortProbe(
            device=port.device,
            description=port.description,
            hwid=port.hwid,
            responsive=True,
            command=command,
            final=detail.final,
            lines=detail.lines,
        )
    except Exception as exc:  # noqa: BLE001 - probe should report per-port failures
        return SerialPortProbe(
            device=port.device,
            description=port.description,
            hwid=port.hwid,
            responsive=False,
            command=command,
            error=f"{exc.__class__.__name__}: {exc}",
        )
    finally:
        client.close()

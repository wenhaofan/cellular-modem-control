# Python API

The public package is `cellular_modem`.

```python
from cellular_modem import Modem, detect_serial_port, list_serial_ports, probe_serial_ports

for port in list_serial_ports():
    print(port.device, port.description)

for probe in probe_serial_ports():
    print(probe.device, probe.responsive, probe.lines)

port = detect_serial_port()

with Modem(port=port, profile="generic") as modem:
    modem.initialize()
    print(modem.info())
    print(modem.sim_info())
    print(modem.signal_quality())
```

## Main Classes

- `SerialTransport`: pyserial-backed byte and line I/O.
- `SerialPortInfo`: serial port metadata returned by `list_serial_ports()`.
- `SerialPortProbe`: active AT probe result returned by `probe_serial_ports()`.
- `ATClient`: synchronous AT command/response client.
- `Modem`: high-level SMS, call, signal, SIM, raw command, and event API.
- `ModemProfile`: command profile for standard and vendor-specific behavior.

## Error Handling

```python
from cellular_modem import ATError, ATTimeout, Modem

try:
    with Modem(port=detect_serial_port()) as modem:
        modem.initialize()
        modem.raw("AT+CPIN?")
except ATTimeout:
    print("The modem did not return a final result in time.")
except ATError as exc:
    print(exc.response.final)
    print(exc.response.lines)
```

## SIM And Network

```python
port = detect_serial_port()

with Modem(port=port) as modem:
    modem.initialize()
    print(modem.sim_info())
    print(modem.sim_info(show_sensitive=True))
    print(modem.signal_quality())
```

`sim_info()` returns SIM readiness, IMSI, ICCID, operator data, and subscriber
numbers when supported by the module. Sensitive identifiers are redacted by
default.

## SMS

```python
with Modem(port=detect_serial_port()) as modem:
    modem.initialize()
    print(modem.sms_mode())
    modem.set_sms_mode("text")
    message_reference = modem.send_sms("+1234567890", "hello")
```

Use `encoding="ucs2"` for non-ASCII content when you do not want auto-detection:

```python
modem.send_sms("+1234567890", "你好", encoding="ucs2")
```

Use `modem.set_sms_pdu_mode()` or `modem.set_sms_mode("pdu")` to switch the
modem to PDU mode for raw or vendor-specific workflows. The high-level SMS
helpers currently implement text-mode send/list/read parsing.

## Calls

```python
with Modem(port=detect_serial_port()) as modem:
    modem.initialize()
    modem.dial("+1234567890")
    modem.send_dtmf("123#")
    modem.hangup()
```

## Raw AT Commands

```python
response = modem.raw("ATI")
print(response.final)
print(response.lines)
```

Use raw commands for diagnostics and vendor-specific experiments before adding
profile support.

## Read-Only Smoke Checks

```python
from cellular_modem import report_to_dict, run_read_only_smoke

report = run_read_only_smoke(port=detect_serial_port(), profile="generic")
print(report_to_dict(report))
```

Smoke checks open the modem once, initialize it, and run only read-only checks.
Sensitive identifiers are redacted unless `show_sensitive=True` is passed.

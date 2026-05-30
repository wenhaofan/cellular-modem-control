# Testing

The default test suite must run without a physical modem.

```bash
python -m unittest discover -s tests
ruff check .
mypy
python -m build
```

## Test Categories

- Unit tests: no hardware, no pyserial device, safe in CI.
- CLI smoke tests: parser and output behavior that does not open a real modem.
- Hardware smoke tests: manual or opt-in checks against a real AT port.

## Hardware Smoke Checks

Run only on a machine with a known AT command port:

```bash
modemctl ports
modemctl --port COM8 --profile generic --json smoke
modemctl --port COM8 --profile generic --json info
modemctl --port COM8 --profile generic --json sim
modemctl --port COM8 --profile generic --json signal
```

Prefer `smoke` for issue reports because it opens the port once and redacts
modem identifiers by default.

Do not include state-changing commands in automated CI:

- `sms-send`
- `sms-delete`
- `call-dial`
- `call-answer`
- `call-hangup`
- `dtmf`
- `audio-volume`
- `audio-mute`

## Fixture Rules

- Redact phone numbers, IMEI, IMSI, ICCID, SMS body, and account details.
- Keep parser fixtures small and focused on one response shape.
- Prefer fake transports and fake clients over sleeping or opening serial ports.

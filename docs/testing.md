# Testing

The default test suite must run without a physical modem.

```bash
python scripts/check.py
```

Use `python scripts/check.py --skip-build` while iterating locally.

Install pre-commit hooks for faster feedback:

```bash
pre-commit install
```

## Test Categories

- Unit tests: no hardware, no pyserial device, safe in CI.
- CLI smoke tests: parser and output behavior that does not open a real modem.
- Hardware smoke tests: manual or opt-in checks against a real AT port.

Coverage is intentionally enforced only for source packages, not for docs,
skills, or test helpers. Keep new behavior covered by no-hardware tests unless
the feature is fundamentally hardware-only. The initial gate is 65%; raise it
only after adding coverage for existing gaps.

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

For copy-pasteable issue output:

```bash
modemctl --port COM8 --profile generic smoke --format markdown
```

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

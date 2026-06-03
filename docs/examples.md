# Examples

The `examples/` directory contains small scripts that use the public Python API.
Run them from a checkout after installing the package in editable mode:

```bash
python -m pip install -e .
```

The examples default to `--port auto`, which probes for an AT-responsive modem
before opening hardware. Pass `--port COM8`, `--port /dev/ttyUSB2`, or another
explicit AT port when you already know the correct device.

## Read-Only Smoke Report

```bash
python examples/read_only_smoke.py --port auto --profile generic
```

This opens the modem, runs the same read-only checks as `modemctl smoke`, and
prints a Markdown report with sensitive identifiers redacted by default.

## Send One SMS

```bash
python examples/send_sms.py --port auto "+1234567890" "hello" --dry-run
```

SMS delivery may incur carrier charges. Keep `--dry-run` while reviewing command
arguments. Remove it only when you intentionally want to send the message. For
non-ASCII text, use auto-detection or force UCS2:

```bash
python examples/send_sms.py --port auto "+1234567890" "你好" --encoding ucs2 --dry-run
```

The example calls `Modem.initialize()` before sending so it follows the same
setup path as the CLI.

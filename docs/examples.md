# Examples

The `examples/` directory contains small scripts that use the public Python API.
Run them from a checkout after installing the package in editable mode:

```bash
python -m pip install -e .
```

On Windows, the examples default to `COM8`. Pass `--port` for Linux, macOS, or a
different Windows port.

## Read-Only Smoke Report

```bash
python examples/read_only_smoke.py --port COM8 --profile generic
```

This opens the modem, runs the same read-only checks as `modemctl smoke`, and
prints a Markdown report with sensitive identifiers redacted by default.

## Send One SMS

```bash
python examples/send_sms.py --port COM8 "+1234567890" "hello"
```

SMS delivery may incur carrier charges. For non-ASCII text, use auto-detection
or force UCS2:

```bash
python examples/send_sms.py --port COM8 "+1234567890" "hello" --encoding ucs2
```

The example calls `Modem.initialize()` before sending so it follows the same
setup path as the CLI.

# Cellular Modem Control

Cross-platform Python tools for controlling cellular modules over a serial
AT-command port. The project uses standard modem commands by default and keeps
vendor-specific behavior behind profiles.

The default Windows port is `COM8`. Override it for Linux/macOS devices such as
`/dev/ttyUSB2`, `/dev/ttyACM0`, or `/dev/cu.usbserial-*`.

## Standard Core

These operations are implemented with common Hayes/3GPP-style AT commands:

- Probe module identity, SIM/network signal, and raw AT commands.
- Send, list, read, and delete SMS messages in text mode.
- Use UCS2 SMS encoding for non-ASCII text such as Chinese.
- Dial, answer, hang up, list active calls, and send DTMF.
- Monitor unsolicited modem events such as incoming calls and new SMS notices.

## Vendor Profiles

The CLI defaults to `--profile generic`. Use profiles for vendor-specific
extensions while keeping the common API stable:

- `generic`: standard AT commands for broad modem compatibility.
- `quectel`: Quectel-compatible profile. It currently uses the same standard
  commands and is ready for model-specific audio routing extensions.

Actual call audio is hardware dependent. Most modules do not carry live voice
audio over the AT serial port. Use the module's USB Audio, PCM/I2S, or analog
audio interface according to the exact module datasheet.

## Quick Start

```powershell
python -m pip install -e .
modemctl ports
modemctl --port COM8 --profile generic smoke --json
modemctl --port COM8 --profile generic info
modemctl --port COM8 signal
modemctl --port COM8 sms-send "+8613800138000" "test"
modemctl --port COM8 call-dial "+8613800138000"
modemctl --port COM8 call-hangup
```

Without installing the package, run from this repository:

```powershell
$env:PYTHONPATH="src"
python -m cellular_modem.cli --port COM8 info
```

The older `python -m quectel_modem.cli ...` entry point is kept as a compatibility
alias.

## Documentation

- [Architecture](docs/architecture.md)
- [CLI reference](docs/cli.md)
- [Python API](docs/api.md)
- [Examples](docs/examples.md)
- [Hardware notes](docs/hardware.md)
- [Profiles](docs/profiles.md)
- [Testing](docs/testing.md)
- [Maintenance](docs/maintenance.md)
- [Release process](docs/release.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

## Useful Commands

```powershell
modemctl ports
modemctl --port COM8 raw "ATI"
modemctl --port COM8 smoke --json
modemctl --port COM8 sms-send "+8613800138000" "Chinese text" --encoding ucs2
modemctl --port COM8 sms-list
modemctl --port COM8 sms-read 1
modemctl --port COM8 sms-delete 1
modemctl --port COM8 call-answer
modemctl --port COM8 dtmf "123#"
modemctl --port COM8 audio-volume 70
modemctl --port COM8 audio-mute on
modemctl --port COM8 monitor --enable-events
```

## Safety

Sending SMS and placing calls may incur carrier charges. The CLI only performs
those actions when the command explicitly asks for them.

Use `modemctl --port COM8 smoke --json` for a read-only hardware validation
report. It runs open/init/info/SIM/signal/ATI checks and redacts modem
identifiers by default.

For issue reports, use `modemctl --port COM8 smoke --format markdown`.

## Development

```powershell
python -m pip install -e ".[dev]"
python scripts/check.py
```

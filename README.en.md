# Cellular Modem Control

Language / 语言: [中文](README.md) | English

Cross-platform Python tools for controlling cellular modules over a serial
AT-command port. The project uses standard modem commands by default and keeps
vendor-specific behavior behind profiles.

It can also act as the communication layer for agent systems. Codex, Claude,
CrawBot, Hermes, and other AI or automation agents can call it through the CLI,
Python API, or a local skill wrapper to give a cellular module real phone-number
capabilities: SMS, dialing, answering, hanging up, DTMF, and modem event
monitoring.

The default Windows port is `COM8`. Override it for Linux/macOS devices such as
`/dev/ttyUSB2`, `/dev/ttyACM0`, or `/dev/cu.usbserial-*`.

## Project Status

This project is pre-1.0 and suitable for early open-source use. The generic AT
core, no-hardware tests, packaging checks, dry-run safety checks, and one local
Quectel EC600N smoke validation are in place. Hardware-specific behavior should
continue to be added through profiles and reproducible reports.

## One-Command Install

Clone the repository first, then run the matching installer from the project
root. By default it creates or refreshes `.venv`, runs `pip install -e .`, and
installs the bundled Codex skills into `$CODEX_HOME/skills` or `~/.codex/skills`.

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

Linux/macOS:

```bash
bash scripts/install.sh
```

Preview package and skill installation actions before writing files:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -DryRun
```

Install or refresh only the agent skills:

```powershell
python scripts/install_skills.py --dry-run
python scripts/install_skills.py --skill cellular-at-modem
python scripts/install_skills.py --skill quectel-modem
```

Use `cellular-at-modem` for generic AT modems and `quectel-modem` for Quectel
modules. After installation, Codex or another local-skill-aware agent can load
the skill as an SMS / phone-call / AT-modem playbook and call `modemctl` or the
Python API.

## Standard Core

These operations are implemented with common Hayes/3GPP-style AT commands:

- Probe module identity, SIM/network signal, and raw AT commands.
- Send, list, read, and delete SMS messages in text mode.
- Use UCS2 SMS encoding for non-ASCII text such as Chinese.
- Dial, answer, hang up, list active calls, and send DTMF.
- Monitor unsolicited modem events such as incoming calls and new SMS notices.

## Use Cases

- Add auditable phone call and SMS tools to agents such as Codex, Claude,
  CrawBot, Hermes, and other automation systems.
- Wrap Quectel, SIMCom, Fibocom, Sierra, Telit, u-blox, or other cellular
  modules as a local communication skill for AI agents, robots, IoT gateways,
  and lab automation.
- Build SMS verification tests, SMS alerts, phone-call reminders, outbound call
  confirmations, DTMF IVR tests, incoming-call monitors, and new-SMS workflows.
- Provide a cross-platform fallback communication channel with a local SIM card
  and AT modem when cloud SMS or cloud voice services are not desired.

## Search Keywords

AI phone call skill, agent phone call tool, SMS agent, Codex skill, Claude
tool, CrawBot, Hermes agent, AT command modem, GSM modem Python, LTE modem
control, cellular modem CLI, Quectel SMS, SIMCom modem, voice call AT commands,
DTMF modem, serial modem automation.

## Usage Demo

Read-only hardware validation for issues or compatibility reports:

```powershell
modemctl --port COM8 --profile generic smoke --json
modemctl --port COM8 --profile generic info
modemctl --port COM8 signal
```

Preview SMS, dialing, and DTMF actions for an agent workflow:

```powershell
modemctl --port COM8 sms-send "+8613800138000" "Codex task finished" --dry-run
modemctl --port COM8 call-dial "+8613800138000" --dry-run
modemctl --port COM8 dtmf "123#" --dry-run
modemctl --port COM8 call-hangup --dry-run
```

Monitor incoming calls and new SMS events:

```powershell
modemctl --port COM8 monitor --enable-events
```

Python read-only smoke example:

```python
from cellular_modem import report_to_markdown, run_read_only_smoke

report = run_read_only_smoke(port="COM8", profile="generic")
print(report_to_markdown(report))
```

Agent wrappers can use the CLI as tools, for example:

- Generate an auditable SMS dry-run plan when a task finishes, then ask for
  confirmation before sending the live SMS.
- Place a phone-call reminder when a monitoring task fails.
- Dial into an IVR and send DTMF digits for automated tests.
- Convert incoming calls or new SMS notices into agent workflow inputs.

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
modemctl --port COM8 sms-send "+8613800138000" "test" --dry-run
modemctl --port COM8 call-dial "+8613800138000" --dry-run
modemctl --port COM8 call-hangup --dry-run
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
- [Compatibility](docs/compatibility.md)
- [Codex skills](docs/skills.md)
- [Testing](docs/testing.md)
- [Maintenance](docs/maintenance.md)
- [Release process](docs/release.md)
- [Contributing](CONTRIBUTING.md)
- [Support](SUPPORT.md)
- [Security policy](SECURITY.md)

## Useful Commands

```powershell
modemctl ports
modemctl --port COM8 raw "ATI"
modemctl --port COM8 smoke --json
modemctl --port COM8 sms-send "+8613800138000" "test" --dry-run
modemctl --port COM8 sms-send "+8613800138000" "Chinese text" --encoding ucs2 --dry-run
modemctl --port COM8 sms-list
modemctl --port COM8 sms-read 1
modemctl --port COM8 sms-delete 1 --dry-run
modemctl --port COM8 call-answer --dry-run
modemctl --port COM8 dtmf "123#" --dry-run
modemctl --port COM8 audio-volume 70 --dry-run
modemctl --port COM8 audio-mute on --dry-run
modemctl --port COM8 monitor --enable-events
```

## Safety

Sending SMS and placing calls may incur carrier charges. The CLI only performs
those actions when the command explicitly asks for them.

Use `--dry-run` on state-changing commands such as `sms-send`, `sms-delete`,
`call-dial`, `call-answer`, `call-hangup`, `dtmf`, `audio-volume`, and
`audio-mute` to preview the operation without opening the serial port.

Use `modemctl --port COM8 smoke --json` for a read-only hardware validation
report. It runs open/init/info/SIM/signal/ATI checks and redacts modem
identifiers by default.

For issue reports, use `modemctl --port COM8 smoke --format markdown`.

## Development

```powershell
python -m pip install -e ".[dev]"
python scripts/check.py
```

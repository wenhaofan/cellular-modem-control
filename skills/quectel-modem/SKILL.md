---
name: quectel-modem
description: Control local Quectel cellular communication modules over serial AT commands. Use when Codex needs to inspect a modem on COM ports or /dev/tty devices, send/list/read/delete SMS, dial/answer/hang up calls, monitor incoming call/SMS events, run raw AT commands, or explain/extend voice-call audio routing for Quectel modules.
---

# Quectel Modem

## Workflow

1. Confirm the local project is available. On this machine the source project is
   usually `L:\项目\sms_skill`. Prefer that repository's Python CLI:
   `python -m quectel_modem.cli ...` with `PYTHONPATH=src`, or the installed
   console script `modemctl ...`.
2. Probe before changing state:
   `modemctl ports`, then prefer `modemctl --port COM8 --profile quectel smoke
   --json`. For narrower checks use `info`, `sim`, and `signal`.
3. Do not send SMS, dial calls, answer calls, hang up calls, delete SMS, or
   change audio settings unless the user explicitly requested that action.
4. Use `--port COM8` for the user's Windows machine unless they provide another
   port. For Linux/macOS use a detected `/dev/ttyUSB*`, `/dev/ttyACM*`, or
   `/dev/cu.*` AT port.
5. For Chinese or other non-ASCII SMS content, use `sms-send ... --encoding ucs2`
   or rely on `--encoding auto`.

## Common Commands

Run from the repository root without installing:

```powershell
$env:PYTHONPATH="src"
python -m quectel_modem.cli --port COM8 info
```

Installed CLI examples:

```powershell
modemctl ports
modemctl --port COM8 info
modemctl --port COM8 --profile quectel smoke --json
modemctl --port COM8 sim
modemctl --port COM8 signal
modemctl --port COM8 raw "ATI"
modemctl --port COM8 sms-send "+8613800138000" "test"
modemctl --port COM8 sms-list
modemctl --port COM8 sms-read 1
modemctl --port COM8 call-dial "+8613800138000"
modemctl --port COM8 call-answer
modemctl --port COM8 call-hangup
modemctl --port COM8 monitor --enable-events
```

Use `--json` when downstream parsing is useful.

## Voice Notes

Treat the serial AT port as call-control, not live audio transport. It can dial,
answer, hang up, send DTMF, and sometimes set volume/mute. Capturing or playing
voice audio depends on the exact Quectel module and hardware interface: USB
Audio, PCM/I2S, or analog audio pins. When the user asks for live audio, first
identify the module with `info`/`ATI`, then read
`references/quectel-at-notes.md` and use `raw` commands or extend the Python
library for that model's documented audio commands.

## Development

Keep changes in the Python package under `src/quectel_modem`. Add deterministic
tests under `tests/` and run:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests
```

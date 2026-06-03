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
   `modemctl ports`, then `modemctl probe --json`, then prefer
   `modemctl --port auto --profile quectel smoke --json`. For narrower checks
   use `info`, `sim`, `signal`, and `sms-mode`.
3. Do not send SMS, dial calls, answer calls, hang up calls, delete SMS, or
   change audio settings unless the user explicitly requested that action.
4. Use `--dry-run` first for state-changing commands and raw AT commands when
   planning or reviewing an action. Dry-run output must not be treated as proof
   that the module supports the command.
5. Use `--port auto` unless the user provides a specific port. If auto probing
   is ambiguous, ask the user to choose from `modemctl ports` / `modemctl probe`
   results such as `COM8`, `/dev/ttyUSB*`, `/dev/ttyACM*`, or `/dev/cu.*`.
6. For Chinese or other non-ASCII SMS content, use `sms-send ... --encoding ucs2`
   or rely on `--encoding auto`.

## Common Commands

Run from the repository root without installing:

```powershell
$env:PYTHONPATH="src"
python -m quectel_modem.cli --port auto info
```

Installed CLI examples:

```powershell
modemctl ports
modemctl probe --json
modemctl --port auto info
modemctl --port auto --profile quectel smoke --json
modemctl --port auto sim
modemctl --port auto signal
modemctl --port auto sms-mode
modemctl --port auto sms-mode pdu --dry-run
modemctl --port auto raw "ATI"
modemctl --port auto raw "AT+CFUN?" --dry-run
modemctl --port auto sms-send "+8613800138000" "test" --dry-run
modemctl --port auto sms-list
modemctl --port auto sms-read 1
modemctl --port auto sms-delete 1 --dry-run
modemctl --port auto call-dial "+8613800138000" --dry-run
modemctl --port auto call-answer --dry-run
modemctl --port auto call-hangup --dry-run
modemctl --port auto monitor --enable-events
```

Use `--json` when downstream parsing is useful.

Only run the non-dry-run form of `sms-send`, `sms-delete`, `sms-mode text`,
`sms-mode pdu`, `call-dial`, `call-answer`, `call-hangup`, `dtmf`,
`audio-volume`, or `audio-mute` after the user explicitly asks for the live
action.

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
python scripts/check.py --skip-build
```

Run the full `python scripts/check.py` gate before committing changes to the
packaged Python project or bundled skills.

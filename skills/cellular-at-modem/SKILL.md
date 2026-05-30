---
name: cellular-at-modem
description: Control local cellular modems over standard AT commands with optional vendor profiles. Use when Codex needs to inspect COM or /dev/tty modem ports, send/list/read/delete SMS, dial/answer/hang up calls, monitor incoming call/SMS events, run raw AT commands, or extend modem support for Quectel, SIMCom, Fibocom, Sierra, Telit, u-blox, or other cellular modules.
---

# Cellular AT Modem

## Workflow

1. Confirm the local project is available. On this machine the source project is
   usually `L:\项目\sms_skill`. Prefer that repository's Python CLI:
   `python -m cellular_modem.cli ...` with `PYTHONPATH=src`, or the installed
   console script `modemctl ...`.
2. Probe before changing state:
   `modemctl ports`, then prefer `modemctl --port COM8 smoke --json`. For
   narrower checks use `info`, `sim`, and `signal`.
3. Use the `generic` profile first. Switch to a vendor profile only when the
   standard command fails or the user asks for vendor-specific behavior.
4. Do not send SMS, dial calls, answer calls, hang up calls, delete SMS, or
   change audio settings unless the user explicitly requested that action.
5. Use `--dry-run` first for state-changing commands and raw AT commands when
   planning or reviewing an action. Dry-run output must not be treated as proof
   that the modem supports the command.
6. For Chinese or other non-ASCII SMS content, use `sms-send ... --encoding ucs2`
   or rely on `--encoding auto`.

## Command Pattern

Run from the repository root without installing:

```powershell
$env:PYTHONPATH="src"
python -m cellular_modem.cli --port COM8 --profile generic info
```

Installed CLI examples:

```powershell
modemctl ports
modemctl --port COM8 --profile generic info
modemctl --port COM8 --profile generic smoke --json
modemctl --port COM8 sim
modemctl --port COM8 signal
modemctl --port COM8 raw "ATI"
modemctl --port COM8 raw "AT+CFUN?" --dry-run
modemctl --port COM8 sms-send "+8613800138000" "test" --dry-run
modemctl --port COM8 sms-list
modemctl --port COM8 sms-read 1
modemctl --port COM8 sms-delete 1 --dry-run
modemctl --port COM8 call-dial "+8613800138000" --dry-run
modemctl --port COM8 call-answer --dry-run
modemctl --port COM8 call-hangup --dry-run
modemctl --port COM8 monitor --enable-events
```

Use `--json` when downstream parsing is useful. Use `--profile quectel` for the
local Quectel EC600N module if model-specific extensions are added later.

Only run the non-dry-run form of `sms-send`, `sms-delete`, `call-dial`,
`call-answer`, `call-hangup`, `dtmf`, `audio-volume`, or `audio-mute` after the
user explicitly asks for the live action.

## Standard Vs Vendor-Specific

Treat SMS, SIM status, signal, basic call control, DTMF, and unsolicited event
monitoring as the standard AT core. Treat audio routing, USB audio enablement,
engineering commands, radio band locking, and advanced packet-data behavior as
vendor-specific extensions.

When adding support for a new module:

1. Keep common behavior in `src/cellular_modem/modem.py`.
2. Add or extend profile behavior in `src/cellular_modem/profiles.py`.
3. Keep raw AT escape hatches through `modemctl raw`.
4. Read `references/at-standard-notes.md` before changing command semantics.

## Voice Notes

The serial AT port controls calls but normally does not carry live audio.
Capturing or playing call audio depends on the exact module and hardware
interface: USB Audio, PCM/I2S, or analog audio pins. First identify the module
with `info`/`ATI`, then add a vendor profile method only for documented audio
commands.

## Development

Run tests after changes:

```powershell
python scripts/check.py --skip-build
```

Run the full `python scripts/check.py` gate before committing changes to the
packaged Python project or bundled skills.

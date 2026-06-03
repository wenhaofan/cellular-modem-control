# CLI Reference

The command line entry point is `modemctl`.

Global options must appear before the command unless a command explicitly
documents otherwise:

```bash
modemctl --port auto --profile generic info
```

## Global Options

- `--port`: serial AT port, or `auto` to actively probe visible ports for an
  AT-responsive modem. Defaults to `MODEM_PORT` when set, otherwise `auto`.
- `--baud`: serial baud rate. Defaults to `115200`. Can also be set with
  `MODEM_BAUD`.
- `--timeout`: serial read timeout in seconds. Defaults to `1.0`. Can also be
  set with `MODEM_TIMEOUT`.
- `--profile`: modem profile. Defaults to `generic`. Can also be set with
  `MODEM_PROFILE`.
- `--no-init`: skip `AT`, `ATE0`, `AT+CMEE=2`, and caller ID setup.
- `--json`: print structured output where supported.

Legacy environment variables `QUECTEL_MODEM_PORT`, `QUECTEL_MODEM_BAUD`, and
`QUECTEL_MODEM_TIMEOUT` are still accepted for compatibility.

## Read-Only Commands

These commands are safe for automated smoke checks:

```bash
modemctl ports
modemctl probe --json
modemctl --port auto smoke --json
modemctl --port auto info
modemctl --port auto sim
modemctl --port auto sim --show-sensitive --json
modemctl --port auto signal
modemctl --port auto sms-mode
modemctl --port auto raw "ATI"
modemctl --port auto raw "AT+CFUN?" --dry-run
```

`smoke` opens the port once, initializes the modem, runs `info`, `sim`,
`signal`, and `raw "ATI"`, and returns a structured report. It redacts sensitive
identifiers by default. Use `--show-sensitive` only for private local debugging.

`ports` uses the same serial port discovery API exposed as
`cellular_modem.list_serial_ports()`. `probe` actively opens candidate ports,
sends `AT`, then sends a read-only identity command such as `ATI`.

`sim` returns SIM readiness, IMSI, ICCID, operator information, and subscriber
numbers when the modem supports the underlying AT commands. IMSI, ICCID, and
phone numbers are redacted by default; pass `--show-sensitive` only for private
local debugging.

Raw AT commands can be read-only or state-changing depending on the command.
Use `raw --dry-run` when collecting or reviewing command plans before touching
hardware.

For issue reports, prefer Markdown:

```bash
modemctl --port auto smoke --format markdown
```

## SMS Commands

```bash
modemctl --port auto sms-mode
modemctl --port auto sms-mode text --dry-run
modemctl --port auto sms-mode pdu --dry-run
modemctl --port auto sms-send "+1234567890" "hello" --dry-run
modemctl --port auto sms-send "+1234567890" "你好" --encoding ucs2 --dry-run
modemctl --port auto sms-list
modemctl --port auto sms-read 1
modemctl --port auto sms-delete 1 --dry-run
```

`sms-mode` without an argument queries `AT+CMGF?`. With `text` or `pdu`, it sets
`AT+CMGF=1` or `AT+CMGF=0`; use `--dry-run` while reviewing plans. The high-level
send/list/read helpers currently implement text mode. Use `raw` for vendor or
PDU-specific experiments before adding a parser.

`sms-send`, `sms-delete`, and `sms-mode text|pdu` are state-changing. Sending SMS
may incur charges and deleting SMS removes messages from modem storage. Use
`--dry-run` to print the intended operation without opening the modem.

## Call Commands

```bash
modemctl --port auto call-dial "+1234567890" --dry-run
modemctl --port auto call-answer --dry-run
modemctl --port auto call-hangup --dry-run
modemctl --port auto call-list
modemctl --port auto dtmf "123#" --dry-run
```

`call-dial`, `call-answer`, `call-hangup`, and `dtmf` affect live call state.
They support `--dry-run`.

## Audio Control Commands

```bash
modemctl --port auto audio-volume 70 --dry-run
modemctl --port auto audio-mute on --dry-run
modemctl --port auto audio-mute off --dry-run
```

These use common AT commands when supported by the module. Live call audio is
not transported through the serial AT port. They support `--dry-run`.

## Event Monitoring

```bash
modemctl --port auto monitor --enable-events
modemctl --port auto monitor --seconds 30
```

`monitor` prints unsolicited modem lines such as incoming call and SMS
indications.

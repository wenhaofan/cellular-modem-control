# CLI Reference

The command line entry point is `modemctl`.

Global options must appear before the command unless a command explicitly
documents otherwise:

```bash
modemctl --port COM8 --profile generic info
```

## Global Options

- `--port`: serial AT port. Defaults to `COM8` on Windows and `/dev/ttyUSB2`
  elsewhere. Can also be set with `MODEM_PORT`.
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
modemctl --port COM8 smoke --json
modemctl --port COM8 info
modemctl --port COM8 sim
modemctl --port COM8 signal
modemctl --port COM8 raw "ATI"
modemctl --port COM8 raw "AT+CFUN?" --dry-run
```

`smoke` opens the port once, initializes the modem, runs `info`, `sim`,
`signal`, and `raw "ATI"`, and returns a structured report. It redacts sensitive
identifiers by default. Use `--show-sensitive` only for private local debugging.

`ports` uses the same serial port discovery API exposed as
`cellular_modem.list_serial_ports()`.

Raw AT commands can be read-only or state-changing depending on the command.
Use `raw --dry-run` when collecting or reviewing command plans before touching
hardware.

For issue reports, prefer Markdown:

```bash
modemctl --port COM8 smoke --format markdown
```

## SMS Commands

```bash
modemctl --port COM8 sms-send "+1234567890" "hello"
modemctl --port COM8 sms-send "+1234567890" "hello" --dry-run
modemctl --port COM8 sms-send "+1234567890" "你好" --encoding ucs2
modemctl --port COM8 sms-list
modemctl --port COM8 sms-read 1
modemctl --port COM8 sms-delete 1
modemctl --port COM8 sms-delete 1 --dry-run
```

`sms-send` and `sms-delete` are state-changing. They may incur charges or remove
messages from modem storage. Use `--dry-run` to print the intended operation
without opening the modem.

## Call Commands

```bash
modemctl --port COM8 call-dial "+1234567890"
modemctl --port COM8 call-dial "+1234567890" --dry-run
modemctl --port COM8 call-answer
modemctl --port COM8 call-hangup
modemctl --port COM8 call-list
modemctl --port COM8 dtmf "123#"
```

`call-dial`, `call-answer`, `call-hangup`, and `dtmf` affect live call state.
They support `--dry-run`.

## Audio Control Commands

```bash
modemctl --port COM8 audio-volume 70
modemctl --port COM8 audio-volume 70 --dry-run
modemctl --port COM8 audio-mute on
modemctl --port COM8 audio-mute off
```

These use common AT commands when supported by the module. Live call audio is
not transported through the serial AT port. They support `--dry-run`.

## Event Monitoring

```bash
modemctl --port COM8 monitor --enable-events
modemctl --port COM8 monitor --seconds 30
```

`monitor` prints unsolicited modem lines such as incoming call and SMS
indications.

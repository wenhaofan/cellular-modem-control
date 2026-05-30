# Hardware Notes

## Serial Port Selection

Many USB cellular modules expose multiple serial ports. Common examples:

- AT port: command/control port used by this project.
- DIAG port: diagnostic logging, not suitable for normal AT control.
- NMEA/GNSS port: location output on modules with GNSS.

Use:

```bash
modemctl ports
```

Then probe the likely AT port:

```bash
modemctl --port COM8 info
modemctl --port /dev/ttyUSB2 info
```

For a single read-only validation report:

```bash
modemctl --port COM8 --profile generic smoke --json
```

The smoke report redacts modem identifiers by default. Use `--show-sensitive`
only for private local troubleshooting.

## Local Validation Snapshot

The project has been smoke-tested on Windows against a Quectel EC600N module
using the module's AT port:

```bash
modemctl ports
modemctl --port COM8 --profile generic --json smoke
```

Observed read-only result on 2026-05-31:

- AT port: `COM8`, `Quectel USB AT Port`.
- Module: `Quectel EC600N`, revision `EC600NCNLAR03A06M08`.
- SIM: `READY`.
- Signal: RSSI `26`, approximately `-61 dBm`; BER `99`.
- Identifier redaction: enabled by default, with IMEI reported as a masked
  value.

Treat this as a reproducible smoke snapshot, not a compatibility guarantee for
every firmware revision or carrier environment.

## Safe Probing

These commands are read-only:

- `info`
- `sim`
- `signal`
- `raw "ATI"`
- `smoke`

These commands can change state or incur carrier charges:

- `sms-send`
- `sms-delete`
- `call-dial`
- `call-answer`
- `call-hangup`
- `dtmf`
- `audio-volume`
- `audio-mute`

## Voice Audio

AT commands control the call state. They normally do not carry live audio.
Check the module documentation for USB Audio, PCM/I2S, or analog audio support.

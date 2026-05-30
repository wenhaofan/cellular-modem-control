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

## Safe Probing

These commands are read-only:

- `info`
- `sim`
- `signal`
- `raw "ATI"`

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

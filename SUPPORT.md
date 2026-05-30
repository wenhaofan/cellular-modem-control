# Support

This project is a community-maintained pre-1.0 tool for AT-command control of
cellular modules. Support is best-effort and depends on reproducible reports.

## Where To Ask

- Use a bug report for crashes, parser errors, packaging failures, or behavior
  that should work through the generic AT profile.
- Use a modem profile request for vendor-specific commands, firmware-specific
  behavior, or features that need a module manual.
- Use a feature request for new CLI or Python API capabilities.
- Report security issues through the process in `SECURITY.md`.

## Before Reporting Hardware Issues

Run the read-only smoke report and keep identifiers redacted:

```bash
modemctl --port <port> --profile generic smoke --format markdown
```

Include the operating system, Python version, package version or commit, modem
vendor/model, firmware revision if available, and the exact command or API call.
Do not post phone numbers, IMSI, ICCID, IMEI, SMS bodies, carrier credentials,
or billing/account details.

## Scope

The project can help with serial AT control, SMS commands, call state commands,
parser behavior, packaging, and profile design. It cannot guarantee carrier
service, emergency calling, regulatory compliance, USB audio behavior, antenna
performance, or compatibility with undocumented vendor firmware behavior.

Voice call audio is especially hardware-specific. AT commands can usually dial
or answer a call, but audio capture/playback depends on USB Audio, PCM/I2S, or
analog audio wiring outside the serial AT port.

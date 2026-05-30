# Changelog

All notable changes to this project will be documented in this file.

The format follows Keep a Changelog style, and this project uses semantic
versioning once public releases begin.

## [0.1.0] - Unreleased

### Added

- Generic `cellular_modem` package for standard AT modem operations.
- Backward-compatible `quectel_modem` import and CLI module aliases.
- `generic` and `quectel` modem profiles.
- CLI command `modemctl` for port listing, module information, SIM status,
  signal quality, SMS, call control, DTMF, audio controls, event monitoring,
  and raw AT commands.
- Read-only `modemctl smoke` hardware validation report with default identifier
  redaction.
- Codex skills for generic cellular AT modems and Quectel modems.
- Unit tests for SMS parsing, UCS2 encoding, call parsing, and profile commands.

# Changelog

All notable changes to this project will be documented in this file.

The format follows Keep a Changelog style, and this project uses semantic
versioning once public releases begin.

## [0.1.0] - Unreleased

### Added

- Generic `cellular_modem` package for standard AT modem operations.
- Backward-compatible `quectel_modem` import and CLI module aliases.
- Bilingual English/Chinese README for public project upload.
- `generic` and `quectel` modem profiles.
- Compatibility support tiers and hardware validation matrix documentation.
- CLI command `modemctl` for port listing, module information, SIM status,
  signal quality, SMS, call control, DTMF, audio controls, event monitoring,
  and raw AT commands.
- Read-only `modemctl smoke` hardware validation report with default identifier
  redaction.
- Markdown smoke report output for issue attachments.
- Public serial port discovery API and runnable Python examples.
- `--dry-run` previews for state-changing CLI commands and raw AT commands.
- Bundled skill metadata validation in the local quality gate.
- Release workflow for trusted publishing to TestPyPI and PyPI.
- Distribution content validation for source and wheel artifacts.
- Version consistency checks across project metadata, package exports, changelog,
  and release tags.
- Redacted local Quectel EC600N hardware smoke validation notes.
- Documentation safety checks for public examples of state-changing modem
  commands.
- Local Markdown link validation in the default quality gate.
- Dry-run CLI example validation in the default quality gate.
- Support policy and feature request template for public issue triage.
- Ruff security linting in the default local quality gate.
- Wheel installation smoke check in the build quality gate.
- Local installer for refreshing bundled Codex skills.
- Codex skills for generic cellular AT modems and Quectel modems.
- Unit tests for SMS parsing, UCS2 encoding, call parsing, and profile commands.

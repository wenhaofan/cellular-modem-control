# Modem Profiles

Profiles keep the standard modem API stable while allowing vendor-specific
commands when needed.

See [Compatibility](compatibility.md) for support tiers, current hardware smoke
coverage, and the standards baseline used by the generic profile.

## Built-In Profiles

- `generic`: Standard AT commands for broad compatibility.
- `quectel`: Quectel-compatible profile. It currently reuses the generic
  command set and is the extension point for model-specific Quectel audio or
  diagnostic commands.

## Adding A Profile

1. Add a `ModemProfile` instance or subclass in `src/cellular_modem/profiles.py`.
2. Register it in `PROFILES`.
3. Add tests for every command that differs from `generic`.
4. Document the supported module family and the source manual.

Keep parser changes generic unless the response format is truly vendor-specific.

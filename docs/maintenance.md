# Maintenance

## Local Checks

Use the same cross-platform command as CI:

```bash
python scripts/check.py
```

Use `--skip-build` while iterating when package metadata is not part of the
change.

## Pre-Commit

Install hooks after installing development dependencies:

```bash
pre-commit install
```

The hook configuration runs Ruff and basic whitespace/YAML/TOML checks before
commits. CI remains authoritative; hooks are a fast local guard, not a
replacement for `python scripts/check.py`.

## Dependency Updates

Dependabot configuration is included for GitHub hosting. It checks GitHub
Actions and Python packaging metadata weekly. Review dependency updates with the
full local quality gate and keep hardware-affecting behavior covered by
no-hardware tests where possible.

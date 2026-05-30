# Maintenance

## Local Checks

Use the same cross-platform command as CI:

```bash
python scripts/check.py
```

Use `--skip-build` while iterating when package metadata is not part of the
change.

The build check creates an sdist and wheel, verifies expected distribution
contents with `scripts/check_dist.py`, installs the wheel in a temporary virtual
environment with `scripts/check_install.py`, and then runs `twine check`.

Version consistency is checked with `scripts/check_version.py`. It compares
`pyproject.toml`, `cellular_modem.__version__`, `CHANGELOG.md`, and release tags
when a tag is present.

High-level public examples are checked with `scripts/check_docs_safety.py` so
state-changing commands stay behind `--dry-run` in README, examples, and bundled
skills.

Local Markdown links are checked with `scripts/check_links.py`. It validates
relative links in README, root Markdown files, docs, GitHub Markdown templates,
and bundled skill Markdown without requiring network access.

Documented dry-run CLI examples are checked with `scripts/check_cli_examples.py`.
It executes only examples that explicitly include `--dry-run`, using the local
Python module instead of the `modemctl` console script, so the check does not
open a serial port.

Run a focused bundled-skill metadata check with:

```bash
python scripts/check.py skills
```

Refresh locally installed Codex skills from the bundled skill folders with:

```bash
python scripts/install_skills.py --dry-run
python scripts/install_skills.py
```

Run a focused static security lint pass with:

```bash
python scripts/check.py security
```

Ruff security rules (`S`) are enabled in the default lint configuration. When a
subprocess or filesystem operation is intentional, prefer a narrow per-file
ignore with a code review note rather than disabling the rule globally.

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

## Bundled Skills

Skill folders under `skills/` are packaged with the source distribution and
validated by `scripts/check_skills.py`. Keep the skill workflow aligned with the
CLI safety model, especially read-only probes and `--dry-run` previews for
state-changing commands. Use `scripts/install_skills.py` to refresh local
Codex installations after changing bundled skill content.

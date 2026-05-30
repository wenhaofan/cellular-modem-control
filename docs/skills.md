# Codex Skills

This repository ships two Codex skill folders under `skills/`:

- `cellular-at-modem`: generic AT-command workflow for cellular modems.
- `quectel-modem`: Quectel-focused workflow for modules such as the local EC600N.

The skills are intentionally thin. They point Codex to the same CLI, safety
rules, dry-run previews, and quality gate used by the Python package.

## Local Installation

Copy or symlink a skill folder into the Codex skills directory on a machine that
should use it:

```powershell
Copy-Item -Recurse .\skills\cellular-at-modem "$env:USERPROFILE\.codex\skills\cellular-at-modem"
Copy-Item -Recurse .\skills\quectel-modem "$env:USERPROFILE\.codex\skills\quectel-modem"
```

Keep the project checkout available when using the skills locally. On this
Windows machine, the expected checkout path is `L:\项目\sms_skill`.

## Validation

The project quality gate validates bundled skill metadata:

```bash
python scripts/check.py skills
```

The full gate also runs this check:

```bash
python scripts/check.py
```

Skill updates should keep `SKILL.md`, `agents/openai.yaml`, and the Python CLI
documentation in sync.

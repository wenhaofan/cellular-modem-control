# Codex Skills

This repository ships two Codex skill folders under `skills/`:

- `cellular-at-modem`: generic AT-command workflow for cellular modems.
- `quectel-modem`: Quectel-focused workflow for modules such as the local EC600N.

The skills are intentionally thin. They point Codex to the same CLI, safety
rules, dry-run previews, and quality gate used by the Python package.

## Local Installation

Install or refresh the bundled skills on a machine that should use them:

```powershell
python scripts/install_skills.py --dry-run
python scripts/install_skills.py
```

By default, the installer writes to `$CODEX_HOME/skills` when `CODEX_HOME` is
set, otherwise to `~/.codex/skills`. Use `--target` to install into another
Codex skills directory, and use `--skill cellular-at-modem` to install a single
skill.

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

"""Validate bundled Codex skill folders."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def main() -> int:
    errors: list[str] = []
    skill_dirs = sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir())

    if not skill_dirs:
        errors.append("skills/: no skill folders found")

    for skill_dir in skill_dirs:
        errors.extend(_validate_skill(skill_dir))

    if errors:
        for error in errors:
            print(f"skill check: {error}", file=sys.stderr)
        return 1

    print(f"validated {len(skill_dirs)} skill folder(s)")
    return 0


def _validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"
    agent_file = skill_dir / "agents" / "openai.yaml"

    if not skill_file.is_file():
        return [f"{skill_dir.name}: missing SKILL.md"]

    frontmatter = _read_frontmatter(skill_file)
    if frontmatter is None:
        errors.append(f"{skill_dir.name}: SKILL.md must start with YAML frontmatter")
        return errors

    fields = _parse_frontmatter(frontmatter)
    name = fields.get("name", "")
    description = fields.get("description", "")

    if not name:
        errors.append(f"{skill_dir.name}: missing frontmatter name")
    elif name != skill_dir.name:
        errors.append(f"{skill_dir.name}: frontmatter name must match folder name")
    elif not NAME_RE.fullmatch(name):
        errors.append(f"{skill_dir.name}: name must use lowercase letters, digits, and hyphens")

    if not description:
        errors.append(f"{skill_dir.name}: missing frontmatter description")
    elif "use when" not in description.lower():
        errors.append(f"{skill_dir.name}: description should describe when to use the skill")

    if not agent_file.is_file():
        errors.append(f"{skill_dir.name}: missing agents/openai.yaml")

    return errors


def _read_frontmatter(skill_file: Path) -> str | None:
    text = skill_file.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    try:
        _, frontmatter, _ = text.split("---\n", 2)
    except ValueError:
        return None
    return frontmatter


def _parse_frontmatter(frontmatter: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    active_key: str | None = None
    for line in frontmatter.splitlines():
        if not line.strip():
            continue
        if line.startswith(" ") and active_key:
            fields[active_key] = f"{fields[active_key]} {line.strip()}".strip()
            continue
        key, separator, value = line.partition(":")
        if not separator:
            continue
        active_key = key.strip()
        fields[active_key] = value.strip().strip('"')
    return fields


if __name__ == "__main__":
    raise SystemExit(main())

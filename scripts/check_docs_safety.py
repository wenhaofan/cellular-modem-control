"""Check public examples for unsafe modem commands without dry-run."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET_FILES = [
    ROOT / "README.md",
    ROOT / "README.en.md",
    ROOT / "docs" / "examples.md",
    ROOT / "skills" / "cellular-at-modem" / "SKILL.md",
    ROOT / "skills" / "quectel-modem" / "SKILL.md",
]
UNSAFE_MODEMCTL_COMMANDS = (
    "sms-send",
    "sms-delete",
    "call-dial",
    "call-answer",
    "call-hangup",
    "dtmf",
    "audio-volume",
    "audio-mute",
    "raw",
)


def main() -> int:
    errors: list[str] = []
    for path in TARGET_FILES:
        errors.extend(_check_file(path))

    if errors:
        for error in errors:
            print(f"docs safety: {error}", file=sys.stderr)
        return 1

    print(f"validated {len(TARGET_FILES)} public example file(s)")
    return 0


def _check_file(path: Path) -> list[str]:
    errors: list[str] = []
    in_code_block = False
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if not in_code_block:
            continue
        if "--dry-run" in stripped:
            continue
        if "modemctl " in stripped and _needs_dry_run(stripped):
            errors.append(f"{_relative(path)}:{line_number}: add --dry-run to unsafe command example")
        if "python examples/send_sms.py" in stripped:
            errors.append(f"{_relative(path)}:{line_number}: add --dry-run to send_sms example")
    return errors


def _needs_dry_run(line: str) -> bool:
    for command in UNSAFE_MODEMCTL_COMMANDS:
        if f" {command}" not in line:
            continue
        return not (command == "raw" and _is_safe_raw_probe(line))
    return False


def _is_safe_raw_probe(line: str) -> bool:
    return 'raw "ATI"' in line or "raw 'ATI'" in line or line.endswith(" raw ATI")


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


if __name__ == "__main__":
    raise SystemExit(main())

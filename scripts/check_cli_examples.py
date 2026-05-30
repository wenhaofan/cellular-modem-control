"""Validate documented dry-run CLI examples."""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = ("README.md", "docs/**/*.md", "skills/**/*.md")
FENCE_MARKERS = ("```", "~~~")


@dataclass(frozen=True)
class Example:
    path: Path
    line_number: int
    command: str


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate documented dry-run CLI examples.")
    parser.add_argument("paths", nargs="*", type=Path, help="Markdown files or directories to check.")
    args = parser.parse_args(argv)

    files = _collect_markdown_files(args.paths)
    examples = [example for path in files for example in _extract_examples(path)]
    errors = [_run_example(example) for example in examples]
    errors = [error for error in errors if error]

    if errors:
        for error in errors:
            print(f"cli example check: {error}", file=sys.stderr)
        return 1

    print(f"validated {len(examples)} dry-run CLI example(s) in {len(files)} markdown file(s)")
    return 0


def _collect_markdown_files(paths: list[Path]) -> list[Path]:
    if not paths:
        files: set[Path] = set()
        for pattern in SCAN_ROOTS:
            files.update(path.resolve() for path in ROOT.glob(pattern) if path.is_file())
        return sorted(files)

    files = set()
    for raw_path in paths:
        path = raw_path if raw_path.is_absolute() else ROOT / raw_path
        if path.is_dir():
            files.update(child.resolve() for child in path.rglob("*.md") if child.is_file())
        elif path.is_file() and path.suffix.lower() == ".md":
            files.add(path.resolve())
        else:
            raise SystemExit(f"not a markdown file or directory: {raw_path}")
    return sorted(files)


def _extract_examples(path: Path) -> list[Example]:
    examples: list[Example] = []
    in_code_block = False
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith(FENCE_MARKERS):
            in_code_block = not in_code_block
            continue
        if not in_code_block or "--dry-run" not in stripped:
            continue
        if stripped.startswith("modemctl ") or stripped.startswith("python examples/send_sms.py "):
            examples.append(Example(path=path, line_number=line_number, command=stripped))
    return examples


def _run_example(example: Example) -> str | None:
    try:
        command = _build_command(example.command)
    except ValueError as exc:
        return f"{_relative(example.path)}:{example.line_number}: {exc}"

    env = os.environ.copy()
    env["PYTHONPATH"] = _pythonpath()
    completed = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=10)
    if completed.returncode != 0:
        return (
            f"{_relative(example.path)}:{example.line_number}: command failed with {completed.returncode}: "
            f"{_first_line(completed.stderr) or _first_line(completed.stdout)}"
        )

    output = completed.stdout.lower()
    if "dry_run" not in output or "true" not in output:
        return f"{_relative(example.path)}:{example.line_number}: dry-run output did not confirm dry_run true"
    return None


def _build_command(command: str) -> list[str]:
    tokens = shlex.split(command, posix=True)
    if not tokens:
        raise ValueError("empty command")
    if tokens[0] == "modemctl":
        return [sys.executable, "-m", "cellular_modem.cli", *tokens[1:]]
    if len(tokens) >= 2 and tokens[:2] == ["python", "examples/send_sms.py"]:
        return [sys.executable, str(ROOT / "examples" / "send_sms.py"), *tokens[2:]]
    raise ValueError(f"unsupported dry-run command: {command}")


def _pythonpath() -> str:
    src = str(ROOT / "src")
    existing = os.environ.get("PYTHONPATH")
    return src if not existing else os.pathsep.join([src, existing])


def _first_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def _relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


if __name__ == "__main__":
    raise SystemExit(main())

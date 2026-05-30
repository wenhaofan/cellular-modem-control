"""Validate local Markdown links without requiring network access."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = ("*.md", ".github/**/*.md", "docs/**/*.md", "skills/**/*.md")
IGNORED_SCHEMES = ("http://", "https://", "mailto:")
LINK_RE = re.compile(r"!?\[[^\]\n]+\]\(([^)\n]+)\)")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate local Markdown links.")
    parser.add_argument("paths", nargs="*", type=Path, help="Markdown files or directories to check.")
    args = parser.parse_args(argv)

    files = _collect_markdown_files(args.paths)
    errors: list[str] = []
    for path in files:
        errors.extend(_check_file(path))

    if errors:
        for error in errors:
            print(f"link check: {error}", file=sys.stderr)
        return 1

    print(f"validated local links in {len(files)} markdown file(s)")
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


def _check_file(path: Path) -> list[str]:
    text = _strip_fenced_code(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in LINK_RE.finditer(line):
            target = _extract_target(match.group(1))
            if _is_external_or_anchor(target):
                continue
            errors.extend(_check_target(path, line_number, target))
    return errors


def _strip_fenced_code(text: str) -> str:
    stripped_lines: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            stripped_lines.append("")
            continue
        stripped_lines.append("" if in_fence else line)
    return "\n".join(stripped_lines)


def _extract_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<"):
        end = target.find(">")
        if end != -1:
            return target[1:end].strip()
    return target.split(maxsplit=1)[0]


def _is_external_or_anchor(target: str) -> bool:
    lower = target.lower()
    return not target or lower.startswith(IGNORED_SCHEMES) or target.startswith("#")


def _check_target(source: Path, line_number: int, target: str) -> list[str]:
    path_part, _separator, _fragment = target.partition("#")
    local_path = (source.parent / unquote(path_part)).resolve(strict=False)
    try:
        local_path.relative_to(ROOT)
    except ValueError:
        return [f"{_relative(source)}:{line_number}: link escapes repository: {target}"]
    if not local_path.exists():
        return [f"{_relative(source)}:{line_number}: missing link target: {target}"]
    return []


def _relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


if __name__ == "__main__":
    raise SystemExit(main())

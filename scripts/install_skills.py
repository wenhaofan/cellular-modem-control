"""Install bundled Codex skills into a local Codex skills directory."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SKILLS = ROOT / "skills"


def main(argv: list[str] | None = None) -> int:
    available = _discover_skills(SOURCE_SKILLS)
    parser = argparse.ArgumentParser(description="Install bundled Codex skills.")
    parser.add_argument(
        "--target",
        type=Path,
        default=_default_target(),
        help="Codex skills directory. Defaults to $CODEX_HOME/skills or ~/.codex/skills.",
    )
    parser.add_argument(
        "--skill",
        action="append",
        choices=available,
        dest="selected_skills",
        help="Install only this skill. Repeat to install multiple skills. Defaults to all bundled skills.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned changes without writing files.")
    args = parser.parse_args(argv)

    if not available:
        print(f"no skill folders found under {_display(SOURCE_SKILLS)}", file=sys.stderr)
        return 1

    target_root = args.target.expanduser().resolve(strict=False)
    selected = args.selected_skills or available
    try:
        plans = [_build_plan(skill_name, target_root) for skill_name in selected]
    except ValueError as exc:
        print(f"skill install: {exc}", file=sys.stderr)
        return 2

    action = "would install" if args.dry_run else "installing"
    print(f"{action} {len(plans)} skill(s) to {_display(target_root)}")

    if args.dry_run:
        for plan in plans:
            _print_plan("dry-run", plan)
        return 0

    if target_root.exists() and not target_root.is_dir():
        print(f"skill install: target is not a directory: {_display(target_root)}", file=sys.stderr)
        return 2
    target_root.mkdir(parents=True, exist_ok=True)

    for plan in plans:
        _install(plan)
        _print_plan("installed", plan)
    return 0


def _default_target() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    base = Path(codex_home) if codex_home else Path.home() / ".codex"
    return base / "skills"


def _discover_skills(source_root: Path) -> list[str]:
    if not source_root.is_dir():
        return []
    return sorted(path.name for path in source_root.iterdir() if path.is_dir() and (path / "SKILL.md").is_file())


def _build_plan(skill_name: str, target_root: Path) -> tuple[str, Path, Path]:
    source_root = SOURCE_SKILLS.resolve(strict=True)
    source = (source_root / skill_name).resolve(strict=True)
    destination = (target_root / skill_name).resolve(strict=False)

    _ensure_inside(source, source_root, "source")
    _ensure_inside(destination, target_root, "destination")
    _ensure_no_overlap(source, destination)
    return skill_name, source, destination


def _install(plan: tuple[str, Path, Path]) -> None:
    _skill_name, source, destination = plan
    if destination.is_symlink() or destination.is_file():
        destination.unlink()
    elif destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))


def _ensure_inside(path: Path, root: Path, label: str) -> None:
    if path != root and not path.is_relative_to(root):
        raise ValueError(f"{label} path is outside expected root: {_display(path)}")


def _ensure_no_overlap(source: Path, destination: Path) -> None:
    if source == destination or source.is_relative_to(destination) or destination.is_relative_to(source):
        raise ValueError(
            "source and destination overlap; choose a target outside the repository skills directory "
            f"for {_display(source)}"
        )


def _print_plan(prefix: str, plan: tuple[str, Path, Path]) -> None:
    skill_name, _source, destination = plan
    print(f"{prefix}: {skill_name} -> {_display(destination)}")


def _display(path: Path) -> str:
    return str(path)


if __name__ == "__main__":
    raise SystemExit(main())

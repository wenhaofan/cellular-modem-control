"""Validate built source and wheel distributions."""

from __future__ import annotations

import argparse
import tarfile
import zipfile
from pathlib import Path

SOURCE_REQUIRED = [
    "README.md",
    "README.en.md",
    "LICENSE",
    "CHANGELOG.md",
    "SUPPORT.md",
    ".github/workflows/ci.yml",
    ".github/workflows/release.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/profile_request.yml",
    "docs/api.md",
    "docs/compatibility.md",
    "docs/release.md",
    "docs/skills.md",
    "examples/read_only_smoke.py",
    "scripts/check.py",
    "scripts/check_cli_examples.py",
    "scripts/check_docs_safety.py",
    "scripts/check_install.py",
    "scripts/check_links.py",
    "scripts/install.ps1",
    "scripts/install.sh",
    "scripts/install_skills.py",
    "scripts/check_version.py",
    "scripts/check_skills.py",
    "skills/cellular-at-modem/SKILL.md",
    "skills/quectel-modem/SKILL.md",
    "tests/test_cli.py",
]

WHEEL_REQUIRED = [
    "cellular_modem/__init__.py",
    "cellular_modem/py.typed",
    "cellular_modem/ports.py",
    "quectel_modem/__init__.py",
    "quectel_modem/py.typed",
    "quectel_modem/ports.py",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate built distribution contents.")
    parser.add_argument("dist_dir", nargs="?", default="dist", help="Directory containing built distributions.")
    args = parser.parse_args(argv)

    dist_dir = Path(args.dist_dir)
    sdists = sorted(dist_dir.glob("*.tar.gz"))
    wheels = sorted(dist_dir.glob("*.whl"))

    errors: list[str] = []
    if len(sdists) != 1:
        errors.append(f"expected exactly one sdist in {dist_dir}, found {len(sdists)}")
    if len(wheels) != 1:
        errors.append(f"expected exactly one wheel in {dist_dir}, found {len(wheels)}")

    if not errors:
        errors.extend(_check_sdist(sdists[0]))
        errors.extend(_check_wheel(wheels[0]))

    if errors:
        for error in errors:
            print(f"dist check: {error}")
        return 1

    print(f"validated {sdists[0].name} and {wheels[0].name}")
    return 0


def _check_sdist(path: Path) -> list[str]:
    with tarfile.open(path, "r:gz") as archive:
        names = _strip_root(archive.getnames())
    return _missing(path.name, names, SOURCE_REQUIRED)


def _check_wheel(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
    return _missing(path.name, names, WHEEL_REQUIRED)


def _strip_root(names: list[str]) -> set[str]:
    stripped: set[str] = set()
    for name in names:
        parts = name.split("/", 1)
        if len(parts) == 2:
            stripped.add(parts[1])
    return stripped


def _missing(archive_name: str, names: set[str], required: list[str]) -> list[str]:
    return [f"{archive_name} missing {item}" for item in required if item not in names]


if __name__ == "__main__":
    raise SystemExit(main())

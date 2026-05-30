"""Validate release version consistency."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "cellular_modem"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate project version consistency.")
    parser.add_argument("--tag", help="Explicit release tag to validate, for example v0.1.0.")
    parser.add_argument("--require-tag", action="store_true", help="Require a matching tag from --tag or GitHub env.")
    args = parser.parse_args(argv)

    version = _project_version()
    expected_tag = f"v{version}"
    errors: list[str] = []

    package_version = _package_version()
    if package_version != version:
        errors.append(f"{PACKAGE_NAME}.__version__ is {package_version!r}, expected {version!r}")

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if f"## [{version}]" not in changelog:
        errors.append(f"CHANGELOG.md is missing a section for {version}")

    actual_tag = args.tag or _github_tag()
    if actual_tag and actual_tag != expected_tag:
        errors.append(f"release tag is {actual_tag!r}, expected {expected_tag!r}")
    elif args.require_tag and not actual_tag:
        errors.append(f"release tag is required; expected {expected_tag}")

    if errors:
        for error in errors:
            print(f"version check: {error}", file=sys.stderr)
        return 1

    print(f"validated version {version}")
    return 0


def _project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as file:
        pyproject = tomllib.load(file)
    return str(pyproject["project"]["version"])


def _package_version() -> str:
    sys.path.insert(0, str(ROOT / "src"))
    import cellular_modem

    return cellular_modem.__version__


def _github_tag() -> str | None:
    if os.getenv("GITHUB_REF_TYPE") == "tag":
        return os.getenv("GITHUB_REF_NAME")
    return None


if __name__ == "__main__":
    raise SystemExit(main())

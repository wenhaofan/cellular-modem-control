"""Run the local quality gate used by maintainers."""

from __future__ import annotations

import argparse
import glob
import shutil
import subprocess
import sys

CHECKS = {
    "version": [[sys.executable, "scripts/check_version.py"]],
    "docs": [[sys.executable, "scripts/check_docs_safety.py"]],
    "links": [[sys.executable, "scripts/check_links.py"]],
    "security": [[sys.executable, "-m", "ruff", "check", "--select", "S", "."]],
    "tests": [
        [sys.executable, "-m", "coverage", "run", "-m", "unittest", "discover", "-s", "tests"],
        [sys.executable, "-m", "coverage", "report"],
    ],
    "ruff": [[sys.executable, "-m", "ruff", "check", "."]],
    "mypy": [[sys.executable, "-m", "mypy"]],
    "skills": [[sys.executable, "scripts/check_skills.py"]],
    "build": [
        [sys.executable, "-m", "build"],
        [sys.executable, "scripts/check_dist.py"],
        [sys.executable, "scripts/check_install.py"],
        [sys.executable, "-m", "twine", "check", "dist/*"],
    ],
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local project checks.")
    parser.add_argument(
        "checks",
        nargs="*",
        metavar="check",
        help=f"Subset of checks to run. Choices: {', '.join(sorted(CHECKS))}. Defaults to all checks.",
    )
    parser.add_argument("--skip-build", action="store_true", help="Skip package build and twine metadata check.")
    args = parser.parse_args(argv)

    invalid = sorted(set(args.checks) - set(CHECKS))
    if invalid:
        parser.error(f"unknown checks: {', '.join(invalid)}")

    selected = args.checks or list(CHECKS)
    if args.skip_build:
        selected = [check for check in selected if check != "build"]

    for check in selected:
        print(f"==> {check}", flush=True)
        for command in CHECKS[check]:
            result = _run(command)
            if result != 0:
                return result
    return 0


def _run(command: list[str]) -> int:
    executable = command[0]
    if shutil.which(executable) is None and executable != sys.executable:
        print(f"missing executable: {executable}", file=sys.stderr)
        return 127
    expanded = _expand_globs(command)
    print("+ " + " ".join(expanded), flush=True)
    completed = subprocess.run(expanded, shell=False)
    return completed.returncode


def _expand_globs(command: list[str]) -> list[str]:
    expanded: list[str] = []
    for item in command:
        if any(char in item for char in "*?["):
            matches = sorted(glob.glob(item))
            expanded.extend(matches or [item])
        else:
            expanded.append(item)
    return expanded


if __name__ == "__main__":
    raise SystemExit(main())

"""Install the built wheel into a temporary virtual environment."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate that the built wheel installs and exposes its CLI.")
    parser.add_argument("dist_dir", nargs="?", default="dist", help="Directory containing the built wheel.")
    args = parser.parse_args(argv)

    wheels = sorted(Path(args.dist_dir).glob("*.whl"))
    if len(wheels) != 1:
        print(f"install check: expected exactly one wheel in {args.dist_dir}, found {len(wheels)}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="cellular-modem-install-") as temp_dir:
        env_dir = Path(temp_dir) / "venv"
        venv.EnvBuilder(with_pip=True).create(env_dir)
        python = _venv_python(env_dir)
        modemctl = _venv_script(env_dir, "modemctl")

        commands = [
            [str(python), "-m", "pip", "install", "--no-deps", str(wheels[0])],
            [str(python), "-c", "import cellular_modem; print(cellular_modem.__version__)"],
            [str(python), "-m", "cellular_modem.cli", "--help"],
            [str(modemctl), "--help"],
        ]
        for command in commands:
            print("+ " + " ".join(command), flush=True)
            completed = subprocess.run(command, env=_command_env(), shell=False)
            if completed.returncode != 0:
                return completed.returncode

    print(f"validated wheel install for {wheels[0].name}")
    return 0


def _venv_python(env_dir: Path) -> Path:
    return env_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def _venv_script(env_dir: Path, name: str) -> Path:
    suffix = ".exe" if sys.platform == "win32" else ""
    return env_dir / ("Scripts" if sys.platform == "win32" else "bin") / f"{name}{suffix}"


def _command_env() -> dict[str, str]:
    return {**os.environ, "PIP_DISABLE_PIP_VERSION_CHECK": "1"}


if __name__ == "__main__":
    raise SystemExit(main())

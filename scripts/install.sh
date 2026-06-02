#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}
TARGET_SKILLS=""
SKIP_PACKAGE=0
SKIP_SKILLS=0
DRY_RUN=0

usage() {
    cat <<'EOF'
Usage: scripts/install.sh [options]

Options:
  --python PATH          Python interpreter to use. Defaults to $PYTHON or python3.
  --target-skills DIR   Codex skills directory. Defaults to $CODEX_HOME/skills or ~/.codex/skills.
  --skip-package        Do not create .venv or install the Python package.
  --skip-skills         Do not install bundled Codex skills.
  --dry-run             Show planned package and skill installation actions.
  -h, --help            Show this help.
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --python)
            PYTHON=$2
            shift 2
            ;;
        --target-skills)
            TARGET_SKILLS=$2
            shift 2
            ;;
        --skip-package)
            SKIP_PACKAGE=1
            shift
            ;;
        --skip-skills)
            SKIP_SKILLS=1
            shift
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

run_skill_install() {
    python_path=$1
    preview=${2:-0}

    if [ -n "$TARGET_SKILLS" ] && [ "$preview" -eq 1 ]; then
        "$python_path" "$ROOT/scripts/install_skills.py" --target "$TARGET_SKILLS" --dry-run
    elif [ -n "$TARGET_SKILLS" ]; then
        "$python_path" "$ROOT/scripts/install_skills.py" --target "$TARGET_SKILLS"
    elif [ "$preview" -eq 1 ]; then
        "$python_path" "$ROOT/scripts/install_skills.py" --dry-run
    else
        "$python_path" "$ROOT/scripts/install_skills.py"
    fi
}

cd "$ROOT"

if [ "$DRY_RUN" -eq 1 ]; then
    if [ "$SKIP_PACKAGE" -eq 0 ]; then
        echo "dry-run: would create or refresh .venv"
        echo "dry-run: would install the package with pip install -e ."
    fi
    if [ "$SKIP_SKILLS" -eq 0 ]; then
        run_skill_install "$PYTHON" 1
    fi
    exit 0
fi

if [ "$SKIP_PACKAGE" -eq 0 ]; then
    "$PYTHON" -m venv "$ROOT/.venv"
    VENV_PYTHON="$ROOT/.venv/bin/python"
    "$VENV_PYTHON" -m pip install --upgrade pip
    "$VENV_PYTHON" -m pip install -e .
else
    VENV_PYTHON=$PYTHON
fi

if [ "$SKIP_SKILLS" -eq 0 ]; then
    run_skill_install "$VENV_PYTHON" 0
fi

echo "installed cellular-modem-control"

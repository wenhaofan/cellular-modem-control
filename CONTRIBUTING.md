# Contributing

Thanks for helping make cellular-modem-control more useful across modem
vendors and operating systems.

## Development Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

On Linux/macOS:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Before Submitting

Run the same checks used by CI:

```bash
python -m unittest discover -s tests
ruff check .
mypy
python -m build
```

## Hardware-Safe Contributions

- Unit tests must not require a real modem by default.
- Do not send SMS, place calls, delete messages, or change audio settings in
  automated tests.
- Add vendor behavior through profiles instead of hard-coding it into the
  generic modem API.
- Prefer standard AT commands when they exist.
- Document any vendor-specific command with the module family and manual source
  it came from.

## Commit Scope

Keep changes focused. A profile addition, parser fix, CLI behavior change, or
documentation update should each be reviewable on its own.

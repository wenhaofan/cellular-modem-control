"""Backward-compatible CLI module."""

from cellular_modem.cli import main

if __name__ == "__main__":
    raise SystemExit(main())

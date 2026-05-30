"""Backward-compatible imports for the older quectel_modem package name."""

from cellular_modem import *  # noqa: F401,F403

from .modem import Modem as Modem

__all__ = [name for name in globals() if not name.startswith("_")]

"""Encoding helpers for modem text mode."""

from __future__ import annotations


def needs_ucs2(value: str) -> bool:
    """Return True when text cannot be safely sent as plain ASCII/GSM text."""

    return any(ord(char) > 0x7F for char in value)


def encode_ucs2(value: str) -> str:
    """Encode a string as uppercase UCS2 hex for AT+CSCS="UCS2"."""

    return value.encode("utf-16-be").hex().upper()


def decode_ucs2(value: str) -> str:
    """Decode UCS2 hex, returning the original value if it is not valid UCS2."""

    compact = "".join(value.split())
    if len(compact) < 4 or len(compact) % 4 != 0:
        return value
    try:
        return bytes.fromhex(compact).decode("utf-16-be")
    except (ValueError, UnicodeDecodeError):
        return value


def maybe_decode_ucs2(value: str) -> str:
    """Decode likely UCS2 hex while leaving normal modem text untouched."""

    compact = "".join(value.split())
    if not compact:
        return value
    if len(compact) % 4 != 0:
        return value
    if any(char not in "0123456789abcdefABCDEF" for char in compact):
        return value
    return decode_ucs2(compact)

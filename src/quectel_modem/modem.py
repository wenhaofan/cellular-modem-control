"""Quectel compatibility wrapper around the generic modem API."""

from cellular_modem.modem import CallInfo, SMSMessage
from cellular_modem.modem import Modem as _GenericModem


class Modem(_GenericModem):
    def __init__(self, *args, profile="quectel", **kwargs):
        super().__init__(*args, profile=profile, **kwargs)


__all__ = ["CallInfo", "Modem", "SMSMessage"]

"""Vendor profiles layered on top of standard cellular AT commands."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModemProfile:
    """Command profile for common 3GPP AT commands and vendor extensions."""

    name: str = "generic"
    basic_init_commands: tuple[str, ...] = ("AT", "ATE0", "AT+CMEE=2")
    caller_id_commands: tuple[str, ...] = ("AT+CLIP=1", "AT+CRC=1")
    event_commands: tuple[str, ...] = ("AT+CLIP=1", "AT+CNMI=2,1,0,0,0")
    supports_ucs2_sms: bool = True
    supports_standard_audio_controls: bool = True

    def dial_command(self, number: str) -> str:
        return f"ATD{number};"

    def answer_command(self) -> str:
        return "ATA"

    def hangup_command(self) -> str:
        return "ATH"

    def dtmf_command(self, digits: str, duration: int | None = None) -> str:
        suffix = f",{duration}" if duration is not None else ""
        return f'AT+VTS="{digits}"{suffix}'

    def speaker_volume_command(self, level: int) -> str:
        return f"AT+CLVL={level}"

    def microphone_mute_command(self, enabled: bool) -> str:
        return f"AT+CMUT={1 if enabled else 0}"


GENERIC_PROFILE = ModemProfile()

QUECTEL_PROFILE = ModemProfile(
    name="quectel",
    # Keep the standard profile for Quectel until model-specific audio routing
    # such as QDAI/QAUDCH is needed.
)

PROFILES = {
    GENERIC_PROFILE.name: GENERIC_PROFILE,
    QUECTEL_PROFILE.name: QUECTEL_PROFILE,
}


def get_profile(profile: str | ModemProfile | None) -> ModemProfile:
    if profile is None:
        return GENERIC_PROFILE
    if isinstance(profile, ModemProfile):
        return profile
    key = profile.lower()
    if key not in PROFILES:
        valid = ", ".join(sorted(PROFILES))
        raise ValueError(f"unknown modem profile {profile!r}; valid profiles: {valid}")
    return PROFILES[key]

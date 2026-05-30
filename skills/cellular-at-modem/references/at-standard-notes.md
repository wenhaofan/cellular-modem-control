# AT Standard Notes

AT command support is layered:

- Hayes/V.250-style basics: `AT`, `ATE0`, final results such as `OK`/`ERROR`.
- 3GPP modem control: common commands such as `AT+CGMI`, `AT+CGMM`, `AT+CGMR`,
  `AT+CGSN`, `AT+CPIN?`, `AT+CSQ`, `ATD`, `ATA`, `ATH`, `AT+CLCC`, `AT+VTS`.
- 3GPP SMS: `AT+CMGF`, `AT+CSCS`, `AT+CSMP`, `AT+CMGS`, `AT+CMGL`, `AT+CMGR`,
  `AT+CMGD`, and unsolicited indications through `AT+CNMI`.
- Vendor extensions: Quectel `Q*`, SIMCom `C*`/vendor commands, Sierra/Telit/
  u-blox-specific commands, audio routing, band locking, and diagnostic modes.

Prefer a standard command when one exists. Add a profile extension only when a
module needs a different command or extra setup.

Use `modemctl smoke --json` for issue reports and hardware validation. It runs
only read-only checks and redacts identifiers by default.

## Common Core Commands

- `AT` checks command responsiveness.
- `ATE0` disables echo for easier parsing.
- `AT+CMEE=2` enables verbose errors.
- `ATI`, `AT+CGMI`, `AT+CGMM`, `AT+CGMR`, `AT+CGSN` identify the module.
- `AT+CPIN?` checks SIM readiness.
- `AT+CSQ` checks RSSI/BER.
- `AT+CMGF=1` selects SMS text mode.
- `AT+CSCS="GSM"` is suitable for ASCII/GSM text.
- `AT+CSCS="UCS2"` plus `AT+CSMP=17,167,0,8` is commonly used for Unicode SMS.
- `ATD<number>;` starts a voice call.
- `ATA` answers.
- `ATH` hangs up.
- `AT+CLCC` lists current calls.
- `AT+VTS="123#"` sends DTMF.
- `AT+CLIP=1` enables caller ID indications.
- `AT+CNMI=2,1,0,0,0` enables new SMS indications.

## Audio Boundary

Do not assume live voice audio is available through the serial AT port. Verify
the module's exposed OS audio device or hardware pins before promising voice
capture/playback.

# Compatibility

This project targets a standards-first AT command core with vendor-specific
behavior isolated behind profiles.

## Standards Basis

The generic profile is based on common Hayes-style AT behavior and 3GPP modem
command families:

- 3GPP TS 27.007: AT command set for User Equipment (UE).
- 3GPP TS 27.005: DTE-DCE interface for SMS and Cell Broadcast Service.

The 3GPP 27-series index lists TS 27.005 for SMS/CBS and TS 27.007 for UE AT
commands:
<https://www.3gpp.org/dynareport?code=27-series.htm>

The 3GPP portal entry for TS 27.007 identifies it as the AT command set for UE:
<https://portal.3gpp.org/desktopmodules/Specifications/SpecificationDetails.aspx?specificationId=1515>

Standards do not guarantee that every module, firmware, carrier profile, or USB
interface implements every command in the same way. Treat the generic profile as
the common baseline and vendor profiles as documented exceptions.

## Support Tiers

| Tier | Meaning | Evidence required |
| --- | --- | --- |
| Generic AT core | Expected to work on modules implementing the standard command shape. | No-hardware unit tests and parser fixtures. |
| Smoke-tested hardware | A real module has passed read-only open/init/info/SIM/signal/ATI checks. | Redacted `modemctl smoke` output with OS, port, model, and firmware. |
| Vendor profile | Module-specific behavior differs from the generic profile and is encoded in a profile. | Public manual reference, no-hardware tests, and hardware smoke output when possible. |
| Experimental | A command can be reached through `modemctl raw` but is not part of a stable profile. | Manual notes only; no compatibility promise. |

## Current Matrix

| Vendor/model | Profile | OS/port tested | Status | Notes |
| --- | --- | --- | --- | --- |
| Quectel EC600N | `generic` | Windows, `COM8` | Smoke-tested hardware | Revision `EC600NCNLAR03A06M08`; SIM ready; RSSI 26; identifiers redacted. |
| Quectel EC600N | `quectel` | Not separately validated | Profile alias | Currently reuses the generic profile until model-specific behavior is added. |
| Other 3GPP-style modems | `generic` | Not hardware-validated in this repository | Generic AT core | Use `modemctl smoke` and open an issue with redacted output if behavior differs. |

## Operation Expectations

| Operation | Generic profile expectation | Common source of variation |
| --- | --- | --- |
| Module identity | `ATI`, `AT+CGMI`, `AT+CGMM`, `AT+CGMR`, `AT+CGSN` | Identifier formatting and firmware strings. |
| Port probing | `AT`, `ATI` after pyserial port enumeration | Multi-interface USB modules, debug/NMEA ports, non-modem serial devices. |
| SIM information | `AT+CPIN?`, `AT+CIMI`, `AT+CCID`, `AT+COPS?`, `AT+CNUM` | Identifier redaction, unsupported ICCID or phone-number commands, carrier provisioning. |
| Signal quality | `AT+CSQ` | RSSI mapping, LTE/5G extended metrics. |
| SMS text mode | `AT+CMGF=1`, `AT+CSCS`, `AT+CMGS`, `AT+CMGL`, `AT+CMGR`, `AT+CMGD` | Storage selection and UCS2 handling. |
| SMS PDU mode | `AT+CMGF=0` | Full PDU encoding/decoding is not yet a high-level helper; use `raw` or add parser support. |
| Basic call state | `ATD`, `ATA`, `ATH`, `AT+CLCC` | Voice service availability and carrier restrictions. |
| DTMF and audio controls | `AT+VTS`, `AT+CLVL`, `AT+CMUT` | Often vendor-specific or unsupported. |
| Live call audio | Outside the serial AT stream | USB Audio, PCM/I2S, or analog wiring. |

## Adding Compatibility

1. Start with `modemctl probe --json`, then
   `modemctl --port auto --profile generic smoke --format markdown`.
2. Keep identifiers and carrier data redacted.
3. Use `modemctl raw "<command>" --dry-run` when discussing a command plan.
4. Add parser or command tests before changing the generic profile.
5. Add vendor-specific behavior through `src/cellular_modem/profiles.py`.
6. Document the module family, firmware behavior, and public manual reference.

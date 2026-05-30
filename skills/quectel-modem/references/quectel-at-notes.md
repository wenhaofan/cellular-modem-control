# Quectel AT Notes

Use these notes as reminders, not as a replacement for the exact module AT
manual. Quectel EC/EG/RG/BG modules differ in audio routing, USB interface
layout, and supported proprietary commands.

## Baseline Probe

- `AT` checks command responsiveness.
- `ATE0` disables echo for easier parsing.
- `AT+CMEE=2` enables verbose errors.
- `ATI`, `AT+CGMI`, `AT+CGMM`, `AT+CGMR`, `AT+CGSN` identify the module.
- `AT+CPIN?` checks SIM readiness.
- `AT+CSQ` checks RSSI/BER.

## SMS

- `AT+CMGF=1` selects text mode.
- `AT+CSCS="GSM"` is suitable for ASCII/GSM text.
- `AT+CSCS="UCS2"` plus `AT+CSMP=17,167,0,8` is commonly used for Unicode SMS.
- `AT+CMGS="<number>"`, wait for `>`, send body, then Ctrl+Z sends SMS.
- `AT+CMGL="ALL"` lists messages.
- `AT+CMGR=<index>` reads a message.
- `AT+CMGD=<index>` deletes a message.

## Calls And Events

- `ATD<number>;` starts a voice call.
- `ATA` answers.
- `ATH` hangs up.
- `AT+CLCC` lists current calls.
- `AT+VTS="123#"` sends DTMF.
- `AT+CLIP=1` enables caller ID indications.
- `AT+CNMI=2,1,0,0,0` enables new SMS indications.

## Audio Control

- `AT+CLVL=<0-100>` sets speaker volume on modules that support it.
- `AT+CMUT=1` mutes microphone; `AT+CMUT=0` unmutes.
- Live audio usually requires USB Audio, PCM/I2S, or analog audio pins. Do not
  promise audio streaming over the AT serial port without confirming the exact
  module manual and OS audio device exposure.

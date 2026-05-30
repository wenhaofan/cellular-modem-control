# Architecture

cellular-modem-control separates the project into four layers:

1. `SerialTransport`: byte and line I/O over pyserial.
2. `ATClient`: command/response handling, final result parsing, SMS prompt
   handling, timeouts, and unsolicited event reading.
3. `Modem`: high-level modem actions such as info, signal, SMS, calls, DTMF,
   and monitoring.
4. `ModemProfile`: vendor-specific command choices layered over the standard
   modem API.

The default profile is `generic`. Vendor profiles should only override command
construction or setup behavior where standard commands are insufficient.

## Hardware Boundary

The serial AT port is treated as a control channel. Live voice audio normally
uses a separate USB Audio, PCM/I2S, or analog path. Audio routing belongs in a
vendor profile only after the exact command is documented for a module family.

## Error Model

- `ATTimeout` means no final result arrived before the deadline.
- `ATError` means the modem returned an error final result and the caller asked
  to raise on errors.
- CLI commands return non-zero for command failures and print errors to stderr.

## Compatibility Layer

`quectel_modem` remains as an import and module alias for early users of the
Quectel-specific prototype. New code should import from `cellular_modem`.

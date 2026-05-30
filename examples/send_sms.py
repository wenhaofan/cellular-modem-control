"""Send one SMS through a modem.

Sending SMS can incur carrier charges. Use this only with a test number you
control.
"""

from __future__ import annotations

import argparse

from cellular_modem import Modem


def main() -> int:
    parser = argparse.ArgumentParser(description="Send one SMS through an AT-command modem.")
    parser.add_argument("number")
    parser.add_argument("text")
    parser.add_argument("--port", default="COM8")
    parser.add_argument("--profile", default="generic")
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--encoding", choices=["auto", "gsm", "ucs2"], default="auto")
    args = parser.parse_args()

    with Modem(port=args.port, baudrate=args.baudrate, timeout=args.timeout, profile=args.profile) as modem:
        modem.initialize()
        reference = modem.send_sms(args.number, args.text, encoding=args.encoding)

    print(f"message_reference: {reference}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

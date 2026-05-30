"""Print a read-only modem smoke report.

This example does not send SMS, place calls, or mutate modem storage.
"""

from __future__ import annotations

import argparse

from cellular_modem import report_to_markdown, run_read_only_smoke


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a read-only modem smoke check.")
    parser.add_argument("--port", default="COM8")
    parser.add_argument("--profile", default="generic")
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument("--timeout", type=float, default=1.0)
    args = parser.parse_args()

    report = run_read_only_smoke(
        port=args.port,
        profile=args.profile,
        baudrate=args.baudrate,
        timeout=args.timeout,
    )
    print(report_to_markdown(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

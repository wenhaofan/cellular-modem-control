import unittest

from cellular_modem.at import ATResponse
from cellular_modem.smoke import report_to_dict, report_to_markdown, run_read_only_smoke


class FakeSmokeModem:
    def __init__(self, port, baudrate, timeout, profile, fail_open=False):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.profile = profile
        self.fail_open = fail_open
        self.closed = False
        self.initialized = False

    def open(self):
        if self.fail_open:
            raise OSError("port unavailable")
        return self

    def close(self):
        self.closed = True

    def initialize(self):
        self.initialized = True

    def info(self):
        return {
            "manufacturer": "Quectel",
            "model": "EC600N",
            "revision": "test",
            "imei": "123456789012345",
        }

    def sim_status(self):
        return "READY"

    def signal_quality(self):
        return {"rssi": 25, "dbm": -63, "ber": 99}

    def raw(self, command, timeout=5.0):
        return ATResponse(command=command, lines=["Quectel", "EC600N"], final="OK")


class FakeSmokeFactory:
    def __init__(self, fail_open=False):
        self.fail_open = fail_open
        self.instance = None

    def __call__(self, port, baudrate, timeout, profile):
        self.instance = FakeSmokeModem(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
            profile=profile,
            fail_open=self.fail_open,
        )
        return self.instance


class SmokeTests(unittest.TestCase):
    def test_smoke_report_redacts_sensitive_identifiers(self):
        factory = FakeSmokeFactory()

        report = run_read_only_smoke(port="COM8", profile="generic", modem_factory=factory)
        payload = report_to_dict(report)

        self.assertTrue(report.ok)
        self.assertTrue(payload["sensitive_redacted"])
        self.assertTrue(factory.instance.closed)
        info = payload["checks"][2]["value"]
        self.assertEqual(info["imei"], "12***45")

    def test_smoke_report_can_include_sensitive_values(self):
        report = run_read_only_smoke(
            port="COM8",
            profile="generic",
            show_sensitive=True,
            modem_factory=FakeSmokeFactory(),
        )
        payload = report_to_dict(report)

        self.assertFalse(payload["sensitive_redacted"])
        self.assertEqual(payload["checks"][2]["value"]["imei"], "123456789012345")

    def test_open_failure_is_reported_without_raising(self):
        report = run_read_only_smoke(port="COM8", profile="generic", modem_factory=FakeSmokeFactory(fail_open=True))
        payload = report_to_dict(report)

        self.assertFalse(report.ok)
        self.assertEqual(payload["checks"][0]["name"], "open")
        self.assertIn("OSError", payload["checks"][0]["error"])

    def test_no_init_marks_initialize_as_skipped(self):
        factory = FakeSmokeFactory()

        report = run_read_only_smoke(port="COM8", profile="generic", initialize=False, modem_factory=factory)
        payload = report_to_dict(report)

        self.assertFalse(factory.instance.initialized)
        self.assertEqual(payload["checks"][1]["value"], "SKIPPED")

    def test_markdown_report_is_issue_ready(self):
        report = run_read_only_smoke(port="COM8", profile="generic", modem_factory=FakeSmokeFactory())

        markdown = report_to_markdown(report)

        self.assertIn("# Modem Smoke Report", markdown)
        self.assertIn("| `info` | PASS |", markdown)
        self.assertIn("12***45", markdown)
        self.assertNotIn("123456789012345", markdown)


if __name__ == "__main__":
    unittest.main()

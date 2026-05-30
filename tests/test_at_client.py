import unittest

from cellular_modem.at import ATClient, ATError


class FakeTransport:
    def __init__(self, lines):
        self.lines = list(lines)
        self.written_lines = []
        self.written_bytes = []
        self.reset_count = 0

    def open(self):
        return None

    def close(self):
        return None

    def reset_input(self):
        self.reset_count += 1

    def write_line(self, line):
        self.written_lines.append(line)

    def write_bytes(self, data):
        self.written_bytes.append(data)

    def read_line(self):
        if not self.lines:
            return None
        return self.lines.pop(0)

    def read_until_prompt(self, timeout):
        return b"\r\n> "


class ATClientTests(unittest.TestCase):
    def test_command_strips_echo_and_returns_payload(self):
        client = ATClient(FakeTransport(["AT+CSQ", "+CSQ: 26,99", "OK"]))

        response = client.command("AT+CSQ")

        self.assertEqual(response.lines, ["+CSQ: 26,99"])
        self.assertEqual(response.final, "OK")

    def test_command_raises_on_error_final(self):
        client = ATClient(FakeTransport(["AT+CPIN?", "+CME ERROR: SIM not inserted"]))

        with self.assertRaises(ATError):
            client.command("AT+CPIN?")

    def test_command_with_prompt_sends_ctrl_z(self):
        client = ATClient(FakeTransport(["+CMGS: 1", "OK"]))

        response = client.command_with_prompt('AT+CMGS="+123"', b"hello")

        self.assertEqual(response.final, "OK")
        self.assertEqual(client.transport.written_bytes, [b"hello\x1a"])


if __name__ == "__main__":
    unittest.main()

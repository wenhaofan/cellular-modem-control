import unittest

from cellular_modem.at import ATClient, ATError, ATResponse, ATTimeout, SerialTransport


class FakeTransport:
    def __init__(self, lines):
        self.lines = list(lines)
        self.written_lines = []
        self.written_bytes = []
        self.reset_count = 0
        self.open_count = 0
        self.close_count = 0

    def open(self):
        self.open_count += 1
        return None

    def close(self):
        self.close_count += 1
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


class FakeSerial:
    def __init__(self, readline_values=None, read_values=None):
        self.is_open = True
        self.readline_values = list(readline_values or [])
        self.read_values = list(read_values or [])
        self.written = []
        self.flush_count = 0
        self.reset_count = 0
        self.close_count = 0

    def close(self):
        self.close_count += 1
        self.is_open = False

    def reset_input_buffer(self):
        self.reset_count += 1

    def write(self, data):
        self.written.append(data)

    def flush(self):
        self.flush_count += 1

    def readline(self):
        if not self.readline_values:
            return b""
        return self.readline_values.pop(0)

    def read(self, size):
        if not self.read_values:
            return b""
        return self.read_values.pop(0)


class ATClientTests(unittest.TestCase):
    def test_context_manager_opens_and_closes_transport(self):
        transport = FakeTransport([])

        with ATClient(transport) as client:
            self.assertIs(client.transport, transport)

        self.assertEqual(transport.open_count, 1)
        self.assertEqual(transport.close_count, 1)

    def test_command_strips_echo_and_returns_payload(self):
        client = ATClient(FakeTransport(["AT+CSQ", "+CSQ: 26,99", "OK"]))

        response = client.command("AT+CSQ")

        self.assertEqual(response.lines, ["+CSQ: 26,99"])
        self.assertEqual(response.final, "OK")

    def test_command_can_return_error_final_without_raising(self):
        client = ATClient(FakeTransport(["ERROR"]))

        response = client.command("AT+FAIL", raise_on_error=False)

        self.assertEqual(response, ATResponse(command="AT+FAIL", lines=[], final="ERROR"))

    def test_command_raises_on_error_final(self):
        client = ATClient(FakeTransport(["AT+CPIN?", "+CME ERROR: SIM not inserted"]))

        with self.assertRaises(ATError) as raised:
            client.command("AT+CPIN?")

        self.assertEqual(raised.exception.response.final, "+CME ERROR: SIM not inserted")
        self.assertIn("AT+CPIN?", str(raised.exception))

    def test_command_times_out_when_no_final_line_arrives(self):
        client = ATClient(FakeTransport([]))

        with self.assertRaises(ATTimeout):
            client.command("ATI", timeout=0)

    def test_command_with_prompt_sends_ctrl_z(self):
        client = ATClient(FakeTransport(["+CMGS: 1", "OK"]))

        response = client.command_with_prompt('AT+CMGS="+123"', b"hello")

        self.assertEqual(response.final, "OK")
        self.assertEqual(client.transport.written_bytes, [b"hello\x1a"])

    def test_command_with_prompt_raises_on_error_after_payload(self):
        client = ATClient(FakeTransport(["+CMS ERROR: 500"]))

        with self.assertRaises(ATError):
            client.command_with_prompt('AT+CMGS="+123"', b"hello")

        self.assertEqual(client.transport.written_bytes, [b"hello\x1a"])

    def test_read_unsolicited_skips_blank_lines(self):
        client = ATClient(FakeTransport(["", "RING"]))

        self.assertEqual(list(client.read_unsolicited(timeout=0.001)), ["RING"])


class SerialTransportTests(unittest.TestCase):
    def test_write_line_encodes_ascii_carriage_return_and_flushes(self):
        serial = FakeSerial()
        transport = SerialTransport("COM8")
        transport._serial = serial

        transport.write_line("ATI")

        self.assertEqual(serial.written, [b"ATI\r"])
        self.assertEqual(serial.flush_count, 1)

    def test_read_line_decodes_and_strips_crlf(self):
        serial = FakeSerial(readline_values=[b"+CSQ: 20,99\r\n", b""])
        transport = SerialTransport("COM8")
        transport._serial = serial

        self.assertEqual(transport.read_line(), "+CSQ: 20,99")
        self.assertIsNone(transport.read_line())

    def test_reset_and_close_delegate_to_serial_port(self):
        serial = FakeSerial()
        transport = SerialTransport("COM8")
        transport._serial = serial

        transport.reset_input()
        self.assertTrue(transport.is_open)
        transport.close()

        self.assertEqual(serial.reset_count, 1)
        self.assertEqual(serial.close_count, 1)
        self.assertFalse(transport.is_open)

    def test_read_until_prompt_returns_buffer_when_prompt_arrives(self):
        serial = FakeSerial(read_values=[b"\r", b"\n", b">"])
        transport = SerialTransport("COM8")
        transport._serial = serial

        self.assertEqual(transport.read_until_prompt(timeout=1), b"\r\n>")

    def test_read_until_prompt_times_out(self):
        serial = FakeSerial()
        transport = SerialTransport("COM8")
        transport._serial = serial

        with self.assertRaises(ATTimeout):
            transport.read_until_prompt(timeout=0)

    def test_operations_require_open_serial_port(self):
        transport = SerialTransport("COM8")

        with self.assertRaises(RuntimeError):
            transport.read_line()


if __name__ == "__main__":
    unittest.main()

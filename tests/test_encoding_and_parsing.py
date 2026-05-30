import unittest

from cellular_modem.encoding import decode_ucs2, encode_ucs2, maybe_decode_ucs2, needs_ucs2
from cellular_modem.modem import _parse_clcc, _parse_cmgl, _parse_cmgr
from cellular_modem.profiles import get_profile


class EncodingTests(unittest.TestCase):
    def test_ucs2_roundtrip(self):
        value = "hello 你好"
        self.assertTrue(needs_ucs2(value))
        self.assertEqual(decode_ucs2(encode_ucs2(value)), value)

    def test_maybe_decode_leaves_plain_text(self):
        self.assertEqual(maybe_decode_ucs2("hello"), "hello")


class ParsingTests(unittest.TestCase):
    def test_parse_cmgl(self):
        messages = _parse_cmgl(
            [
                '+CMGL: 1,"REC READ","002B003100320033","","32/05/27,10:11:12+32"',
                "4F60597D",
            ]
        )
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].index, 1)
        self.assertEqual(messages[0].sender, "+123")
        self.assertEqual(messages[0].text, "你好")

    def test_parse_cmgr(self):
        message = _parse_cmgr(
            2,
            [
                '+CMGR: "REC UNREAD","002B003100320033","","32/05/27,10:11:12+32"',
                "00680069",
            ],
        )
        self.assertEqual(message.index, 2)
        self.assertEqual(message.text, "hi")

    def test_parse_clcc(self):
        calls = _parse_clcc(['+CLCC: 1,0,0,0,0,"+123",145'])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].number, "+123")


class ProfileTests(unittest.TestCase):
    def test_generic_profile_commands(self):
        profile = get_profile("generic")
        self.assertEqual(profile.dial_command("+123"), "ATD+123;")
        self.assertEqual(profile.dtmf_command("12#", duration=5), 'AT+VTS="12#",5')


if __name__ == "__main__":
    unittest.main()

import unittest

from cellular_modem.at import ATResponse
from cellular_modem.modem import Modem


class FakeClient:
    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.commands = []
        self.prompt_commands = []

    def command(self, command, timeout=5.0, ok_final=("OK",), raise_on_error=True):
        self.commands.append(
            {
                "command": command,
                "timeout": timeout,
                "ok_final": ok_final,
                "raise_on_error": raise_on_error,
            }
        )
        if self.responses:
            return self.responses.pop(0)
        return ATResponse(command=command, lines=[], final="OK")

    def command_with_prompt(self, command, payload, timeout=30.0, ok_final=("OK",), raise_on_error=True):
        self.prompt_commands.append(
            {
                "command": command,
                "payload": payload,
                "timeout": timeout,
                "ok_final": ok_final,
                "raise_on_error": raise_on_error,
            }
        )
        if self.responses:
            return self.responses.pop(0)
        return ATResponse(command=command, lines=["+CMGS: 1"], final="OK")

    def read_unsolicited(self, timeout=None):
        yield from ["RING", '+CMTI: "SM",1']


def modem_with_client(client):
    modem = Modem(port="unused")
    modem.client = client
    return modem


class ModemHighLevelTests(unittest.TestCase):
    def test_initialize_uses_profile_command_order(self):
        client = FakeClient()
        modem = modem_with_client(client)

        modem.initialize()

        self.assertEqual(
            [item["command"] for item in client.commands],
            ["AT", "ATE0", "AT+CMEE=2", "AT+CLIP=1", "AT+CRC=1"],
        )
        self.assertFalse(client.commands[-1]["raise_on_error"])

    def test_signal_quality_unknown_rssi_has_no_dbm(self):
        client = FakeClient([ATResponse("AT+CSQ", ["+CSQ: 99,99"], "OK")])
        modem = modem_with_client(client)

        signal = modem.signal_quality()

        self.assertEqual(signal, {"rssi": 99, "dbm": None, "ber": 99})

    def test_sim_info_reads_common_identifiers_and_redacts_by_default(self):
        client = FakeClient(
            [
                ATResponse("AT+CPIN?", ["+CPIN: READY"], "OK"),
                ATResponse("AT+CIMI", ["460001234567890"], "OK"),
                ATResponse("AT+CCID", ["+CCID: 89860012345678901234"], "OK"),
                ATResponse("AT+COPS?", ['+COPS: 0,0,"Carrier",7'], "OK"),
                ATResponse("AT+CNUM", ['+CNUM: "line","+8613800138000",145'], "OK"),
            ]
        )
        modem = modem_with_client(client)

        info = modem.sim_info()

        self.assertEqual(info["status"], "READY")
        self.assertEqual(info["imsi"], "46***90")
        self.assertEqual(info["iccid"], "89***34")
        self.assertEqual(info["operator"], {"mode": "0", "format": "0", "name": "Carrier", "access_technology": "7"})
        self.assertEqual(info["numbers"], [{"alpha": "line", "number": "+8***00", "type": "145"}])

    def test_sms_mode_can_query_and_set_text_or_pdu(self):
        client = FakeClient(
            [
                ATResponse("AT+CMGF?", ["+CMGF: 0"], "OK"),
                ATResponse("AT+CMGF=1", [], "OK"),
                ATResponse("AT+CMGF=0", [], "OK"),
            ]
        )
        modem = modem_with_client(client)

        self.assertEqual(modem.sms_mode(), "pdu")
        modem.set_sms_mode("text")
        modem.set_sms_pdu_mode()

        self.assertEqual([item["command"] for item in client.commands], ["AT+CMGF?", "AT+CMGF=1", "AT+CMGF=0"])

    def test_send_ascii_sms_uses_gsm_text_mode(self):
        client = FakeClient(
            [
                ATResponse("AT+CMGF=1", [], "OK"),
                ATResponse('AT+CSCS="GSM"', [], "OK"),
                ATResponse("AT+CSMP=17,167,0,0", [], "OK"),
                ATResponse('AT+CMGS="+123"', ["+CMGS: 7"], "OK"),
            ]
        )
        modem = modem_with_client(client)

        reference = modem.send_sms("+123", "hello", encoding="gsm")

        self.assertEqual(reference, 7)
        self.assertEqual(
            [item["command"] for item in client.commands],
            ["AT+CMGF=1", 'AT+CSCS="GSM"', "AT+CSMP=17,167,0,0"],
        )
        self.assertEqual(client.prompt_commands[0]["command"], 'AT+CMGS="+123"')
        self.assertEqual(client.prompt_commands[0]["payload"], b"hello")

    def test_send_ucs2_sms_encodes_number_and_text(self):
        client = FakeClient(
            [
                ATResponse("AT+CMGF=1", [], "OK"),
                ATResponse('AT+CSCS="UCS2"', [], "OK"),
                ATResponse("AT+CSMP=17,167,0,8", [], "OK"),
                ATResponse('AT+CMGS="002B003100320033"', ["+CMGS: 8"], "OK"),
            ]
        )
        modem = modem_with_client(client)

        reference = modem.send_sms("+123", "你好", encoding="auto")

        self.assertEqual(reference, 8)
        self.assertEqual(
            [item["command"] for item in client.commands],
            ["AT+CMGF=1", 'AT+CSCS="UCS2"', "AT+CSMP=17,167,0,8"],
        )
        self.assertEqual(client.prompt_commands[0]["command"], 'AT+CMGS="002B003100320033"')
        self.assertEqual(client.prompt_commands[0]["payload"], b"4F60597D")

    def test_speaker_volume_bounds_are_checked_before_command(self):
        client = FakeClient()
        modem = modem_with_client(client)

        with self.assertRaises(ValueError):
            modem.set_speaker_volume(101)

        self.assertEqual(client.commands, [])

    def test_monitor_events_delegates_to_client(self):
        client = FakeClient()
        modem = modem_with_client(client)

        self.assertEqual(list(modem.monitor_events(seconds=1)), ["RING", '+CMTI: "SM",1'])


if __name__ == "__main__":
    unittest.main()

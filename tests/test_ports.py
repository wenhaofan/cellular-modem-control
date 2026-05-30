import unittest
from types import SimpleNamespace
from unittest.mock import patch

from cellular_modem import SerialPortInfo, list_serial_ports


class PortDiscoveryTests(unittest.TestCase):
    def test_list_serial_ports_normalizes_pyserial_objects(self):
        fake_port = SimpleNamespace(device="COM8", description="USB Serial Port", hwid="USB VID:PID=1234:5678")

        with patch("serial.tools.list_ports.comports", return_value=[fake_port]):
            ports = list_serial_ports()

        self.assertEqual(
            ports,
            [SerialPortInfo(device="COM8", description="USB Serial Port", hwid="USB VID:PID=1234:5678")],
        )


if __name__ == "__main__":
    unittest.main()

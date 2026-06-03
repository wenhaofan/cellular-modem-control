import unittest
from types import SimpleNamespace
from unittest.mock import patch

from cellular_modem import SerialPortInfo, SerialPortProbe, detect_serial_port, list_serial_ports


class PortDiscoveryTests(unittest.TestCase):
    def test_list_serial_ports_normalizes_pyserial_objects(self):
        fake_port = SimpleNamespace(device="COM8", description="USB Serial Port", hwid="USB VID:PID=1234:5678")

        with patch("serial.tools.list_ports.comports", return_value=[fake_port]):
            ports = list_serial_ports()

        self.assertEqual(
            ports,
            [SerialPortInfo(device="COM8", description="USB Serial Port", hwid="USB VID:PID=1234:5678")],
        )

    def test_detect_serial_port_returns_first_responsive_probe(self):
        ports = [
            SerialPortInfo("COM7", "Bluetooth serial", "BTHENUM"),
            SerialPortInfo("COM8", "Quectel USB AT Port", "USB"),
        ]
        probes = {
            "COM7": SerialPortProbe("COM7", "Bluetooth serial", "BTHENUM", False, "ATI", error="timeout"),
            "COM8": SerialPortProbe("COM8", "Quectel USB AT Port", "USB", True, "ATI", final="OK", lines=["Quectel"]),
        }

        with (
            patch("cellular_modem.ports.list_serial_ports", return_value=ports),
            patch(
                "cellular_modem.ports._probe_one_port",
                side_effect=lambda port, **_kwargs: probes[port.device],
            ) as probe,
        ):
            port = detect_serial_port(baudrate=9600, timeout=0.2)

        self.assertEqual(port, "COM8")
        probe.assert_called_once()
        self.assertEqual(probe.call_args.args[0].device, "COM8")

    def test_detect_serial_port_reports_no_responsive_ports(self):
        ports = [SerialPortInfo("COM7", "debug", "USB")]
        probe = SerialPortProbe("COM7", "debug", "USB", False, "ATI", error="timeout")

        with (
            patch("cellular_modem.ports.list_serial_ports", return_value=ports),
            patch("cellular_modem.ports._probe_one_port", return_value=probe),
            self.assertRaisesRegex(RuntimeError, "no AT-responsive modem"),
        ):
            detect_serial_port()


if __name__ == "__main__":
    unittest.main()

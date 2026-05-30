import unittest

import cellular_modem
import quectel_modem
import quectel_modem.at
import quectel_modem.cli
import quectel_modem.encoding
import quectel_modem.profiles
import quectel_modem.smoke


class CompatibilityTests(unittest.TestCase):
    def test_quectel_modem_exports_compatible_modem(self):
        self.assertTrue(issubclass(quectel_modem.Modem, cellular_modem.Modem))

    def test_quectel_wrapper_defaults_to_quectel_profile(self):
        modem = quectel_modem.Modem(port="unused")

        self.assertEqual(modem.profile.name, "quectel")

    def test_compatibility_modules_import(self):
        self.assertIs(quectel_modem.cli.main, cellular_modem.cli.main)
        self.assertIs(quectel_modem.profiles.get_profile, cellular_modem.get_profile)
        self.assertIs(quectel_modem.smoke.run_read_only_smoke, cellular_modem.run_read_only_smoke)


if __name__ == "__main__":
    unittest.main()

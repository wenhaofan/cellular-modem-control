import tempfile
import unittest
from pathlib import Path

from scripts import check_cli_examples


class CheckCliExamplesTests(unittest.TestCase):
    def test_extracts_only_safe_dry_run_examples(self) -> None:
        with tempfile.TemporaryDirectory(dir=check_cli_examples.ROOT) as tmpdir:
            path = Path(tmpdir) / "examples.md"
            path.write_text(
                "\n".join(
                    [
                        "```bash",
                        'modemctl --port COM8 sms-send "+123" "hello" --dry-run',
                        'modemctl --port COM8 sms-send "+123" "hello"',
                        'python examples/send_sms.py --port COM8 "+123" "hello" --dry-run',
                        "```",
                    ]
                ),
                encoding="utf-8",
            )

            examples = check_cli_examples._extract_examples(path)

        self.assertEqual([example.command for example in examples], [
            'modemctl --port COM8 sms-send "+123" "hello" --dry-run',
            'python examples/send_sms.py --port COM8 "+123" "hello" --dry-run',
        ])

    def test_builds_modemctl_command_through_python_module(self) -> None:
        command = check_cli_examples._build_command("modemctl --port COM8 call-hangup --dry-run")

        self.assertEqual(command[:3], [check_cli_examples.sys.executable, "-m", "cellular_modem.cli"])
        self.assertEqual(command[3:], ["--port", "COM8", "call-hangup", "--dry-run"])

    def test_builds_send_sms_example_command(self) -> None:
        command = check_cli_examples._build_command('python examples/send_sms.py --port COM8 "+123" "hello" --dry-run')

        self.assertEqual(command[0], check_cli_examples.sys.executable)
        self.assertEqual(command[1], str(check_cli_examples.ROOT / "examples" / "send_sms.py"))
        self.assertEqual(command[2:], ["--port", "COM8", "+123", "hello", "--dry-run"])

    def test_runs_documented_dry_run_example_without_opening_modem(self) -> None:
        example = check_cli_examples.Example(
            path=check_cli_examples.ROOT / "README.md",
            line_number=1,
            command='modemctl --port COM8 sms-send "+123" "hello" --dry-run',
        )

        error = check_cli_examples._run_example(example)

        self.assertIsNone(error)


if __name__ == "__main__":
    unittest.main()

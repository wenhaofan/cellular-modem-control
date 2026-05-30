import importlib.util
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "install_skills.py"


def _load_install_skills():
    spec = importlib.util.spec_from_file_location("install_skills", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


INSTALL_SKILLS = _load_install_skills()


def _run_main(args: list[str]) -> tuple[int, str, str]:
    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = INSTALL_SKILLS.main(args)
    return code, stdout.getvalue(), stderr.getvalue()


class InstallSkillsTests(unittest.TestCase):
    def test_dry_run_does_not_write_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "skills"
            code, output, _error = _run_main(["--target", str(target), "--dry-run"])

            self.assertEqual(code, 0)
            self.assertIn("would install 2 skill(s)", output)
            self.assertFalse(target.exists())

    def test_install_refreshes_skill_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "skills"

            code, _output, _error = _run_main(["--target", str(target), "--skill", "cellular-at-modem"])
            self.assertEqual(code, 0)
            self.assertTrue((target / "cellular-at-modem" / "SKILL.md").is_file())

            stale_file = target / "cellular-at-modem" / "stale.txt"
            stale_file.write_text("remove me", encoding="utf-8")

            code, _output, _error = _run_main(["--target", str(target), "--skill", "cellular-at-modem"])

            self.assertEqual(code, 0)
            self.assertFalse(stale_file.exists())

    def test_refuses_repository_skills_as_target(self) -> None:
        code, _output, error = _run_main(["--target", str(INSTALL_SKILLS.SOURCE_SKILLS), "--dry-run"])

        self.assertEqual(code, 2)
        self.assertIn("source and destination overlap", error)


if __name__ == "__main__":
    unittest.main()

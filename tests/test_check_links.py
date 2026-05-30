import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_links.py"


def _load_check_links():
    spec = importlib.util.spec_from_file_location("check_links", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECK_LINKS = _load_check_links()


class CheckLinksTests(unittest.TestCase):
    def test_validates_existing_relative_link(self) -> None:
        errors = CHECK_LINKS._check_file(Path("README.md").resolve())

        self.assertEqual(errors, [])

    def test_ignores_links_inside_fenced_code_blocks(self) -> None:
        with tempfile.TemporaryDirectory(dir=CHECK_LINKS.ROOT) as tmpdir:
            path = Path(tmpdir) / "sample.md"
            path.write_text("```markdown\n[missing](missing.md)\n```\n", encoding="utf-8")

            errors = CHECK_LINKS._check_file(path)

        self.assertEqual(errors, [])

    def test_reports_missing_relative_link(self) -> None:
        with tempfile.TemporaryDirectory(dir=CHECK_LINKS.ROOT) as tmpdir:
            path = Path(tmpdir) / "sample.md"
            path.write_text("[missing](missing.md)\n", encoding="utf-8")

            errors = CHECK_LINKS._check_file(path)

        self.assertEqual(len(errors), 1)
        self.assertIn("missing link target: missing.md", errors[0])

    def test_reports_links_that_escape_repository(self) -> None:
        with tempfile.TemporaryDirectory(dir=CHECK_LINKS.ROOT) as tmpdir:
            path = Path(tmpdir) / "sample.md"
            path.write_text("[outside](../../outside.md)\n", encoding="utf-8")

            errors = CHECK_LINKS._check_file(path)

        self.assertEqual(len(errors), 1)
        self.assertIn("link escapes repository: ../../outside.md", errors[0])


if __name__ == "__main__":
    unittest.main()

# Release Process

This project is pre-1.0. Before publishing a release:

1. Update `CHANGELOG.md`.
2. Confirm `pyproject.toml` has the target version.
3. Run:

   ```bash
   python -m unittest discover -s tests
   ruff check .
   mypy
   python -m build
   twine check dist/*
   ```

4. Confirm the source distribution contains docs, skills, tests, and CI files:

   ```bash
   python -m tarfile -l dist/cellular_modem_control-0.1.0.tar.gz
   ```

5. Create a signed git tag:

   ```bash
   git tag -s v0.1.0 -m "v0.1.0"
   ```

6. Publish to TestPyPI first, then PyPI after a clean install test.

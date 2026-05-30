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

4. Create a signed git tag:

   ```bash
   git tag -s v0.1.0 -m "v0.1.0"
   ```

5. Publish to TestPyPI first, then PyPI after a clean install test.

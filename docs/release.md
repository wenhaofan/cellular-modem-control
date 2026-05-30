# Release Process

This project is pre-1.0. Releases are built by `.github/workflows/release.yml`.
Before publishing a release:

1. Update `CHANGELOG.md`.
2. Confirm `pyproject.toml` has the target version.
3. Confirm version metadata and changelog agree:

   ```bash
   python scripts/check_version.py
   ```

4. Run:

   ```bash
   python scripts/check.py
   ```

   If a modem is available, also run a read-only smoke check:

   ```bash
   modemctl --port COM8 --profile generic smoke --json
   ```

5. Confirm the distribution content check passes:

   ```bash
   python scripts/check_dist.py
   ```

6. Create a signed git tag:

   ```bash
   git tag -s v0.1.0 -m "v0.1.0"
   python scripts/check_version.py --tag v0.1.0
   ```

7. Push the tag and create a GitHub release from that tag. Publishing the GitHub
   release runs the release workflow and publishes to PyPI through trusted
   publishing.

## TestPyPI

Use the manual `workflow_dispatch` trigger in the release workflow with
`repository=testpypi` before publishing a public release. After it finishes,
install from TestPyPI in a clean environment and run a read-only command:

```bash
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ cellular-modem-control
modemctl --help
```

## Trusted Publishing

Configure PyPI and TestPyPI trusted publishers before the first hosted release:

- Workflow: `.github/workflows/release.yml`
- PyPI environment: `pypi`
- TestPyPI environment: `testpypi`
- Package name: `cellular-modem-control`

The workflow does not require an API token when trusted publishing is
configured.

The PyPI publish path requires a tag matching `v<pyproject version>`. TestPyPI
publishing can be run manually from a branch for pre-release package checks.

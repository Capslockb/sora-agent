# Repository pytest CI

The repository-wide pytest workflow is defined at
`.github/workflows/tests.yml`. It runs on pushes and pull requests targeting
`main` with Python 3.12 and 3.13, installs the project with
`pip install -e ".[dev]"`, and executes `python -m pytest -v`.

Activation is tracked in Issue #12. Until the workflow change is merged and an
exact-head run succeeds on the resulting `main` commit, do not describe `main`
or runtime/security changes as automatically pytest-validated.

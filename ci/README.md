# CI workflow — one step to activate

`tests.yml` in this folder is a finished GitHub Actions workflow staged on
`main`. GitHub does not execute workflow files outside `.github/workflows/`.
The API credential used for repository maintenance cannot move it there because
it lacks the `workflow` permission.

**To activate with the GitHub web editor:**

1. Open `ci/tests.yml` on the `main` branch.
2. Click the pencil (edit), then "Rename file" and change the path to
   `.github/workflows/tests.yml`.
3. Commit the move directly to `main`.
4. Delete `ci/README.md` after the workflow file is active.

Alternatively from a checkout with appropriately scoped credentials:

```sh
mkdir -p .github/workflows
git mv ci/tests.yml .github/workflows/tests.yml
git rm ci/README.md
git commit -m "ci: activate pytest workflow"
git push
```

The staged workflow is configured to run `pytest` on pushes and pull requests
targeting `main` with Python 3.12 and 3.13, installing the project through
`pip install -e ".[dev]"`.

Until the move is completed and an exact-head Actions run succeeds, current
`main` and pull requests must not be described as automatically pytest-validated.
Activation and first-run evidence are tracked in Issue #12.

# CI workflow — one step to activate

`tests.yml` in this folder is the finished GitHub Actions workflow, staged
here because the API token used to author it lacks the `workflow` scope
required to write under `.github/workflows/` directly.

**To activate (30 seconds, web UI):**

1. Open `ci/tests.yml` on the `main` branch after merging this PR.
2. Click the pencil (edit), then "Rename file" and change the path to
   `.github/workflows/tests.yml` (this moves the file).
3. Commit the change directly to `main`.

Alternatively from a checkout:

```sh
mkdir -p .github/workflows
git mv ci/tests.yml .github/workflows/tests.yml
git rm ci/README.md
git commit -m "ci: activate pytest workflow"
git push
```

The workflow runs `pytest` on every push and PR to `main` (Python 3.12 and
3.13), installing the project with `pip install -e ".[dev]"` — the same
setup used to verify 24/24 tests green on `main` after #4.

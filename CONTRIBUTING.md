# Contributing

Thanks for your interest in contributing to **dg_kit**.

## Development Setup
1. Create and activate a virtual environment.
2. Install dev dependencies:
```bash
uv sync --group dev
```

## Quality Checks
Run the full local checks:
```bash
./scripts/ci.sh
```

## Coding Standards
- Use `ruff` for linting and formatting.
- Keep changes focused and small where possible.
- Add tests for new behavior or bug fixes.

## Commit and PRs
- Use a feature branch per issue (branch created from the issue).
- Branch naming convention:
  - `feature/<issue-id>-short-slug`
  - `fix/<issue-id>-short-slug`
  - `chore/<issue-id>-short-slug`
- Open a PR against `main`.
- Describe the change clearly and link the issue (e.g., `Closes #123`).
- Ensure CI is green before requesting review.

## Versioning
We follow Semantic Versioning (`MAJOR.MINOR.PATCH`).  
If your change affects the public API or behavior, note it in the PR description.

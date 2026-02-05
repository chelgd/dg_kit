#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root_dir"

echo "==> Ruff lint"
ruff check .

echo "==> Ruff format check"
ruff format --check .

echo "==> Pyright"
pyright

echo "==> Pytest"
pytest

echo "==> Pre-commit"
pre-commit run --all-files

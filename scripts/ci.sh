#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root_dir"

run_cmd() {
  if command -v uv >/dev/null 2>&1; then
    uv run "$@"
  else
    "$@"
  fi
}

echo "==> Ruff autofix"
run_cmd ruff check --fix .

echo "==> Ruff lint"
run_cmd ruff check .

echo "==> Ruff format check"
run_cmd ruff format .

#echo "==> Pyright"
#run_cmd pyright

#echo "==> Pytest"
#run_cmd pytest

#echo "==> Pre-commit"
#run_cmd pre-commit run --all-files

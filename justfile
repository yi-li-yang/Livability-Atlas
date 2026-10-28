# Every command in this repository runs through just: `just` lists them.
# Recipes use no shell syntax beyond `cd x; command`, so they run in PowerShell and sh alike.

set windows-shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-Command"]
set export

PYTHONUTF8 := "1"

default:
    @just --list

# Install every dependency and the git hooks
setup:
    cd pipeline; uv sync
    cd pipeline; uv run pre-commit install

# Everything CI checks: lint, types, tests, the catalogue, and the factor explorer's tests
check: lint types test validate explorer

# Lint and check formatting
lint:
    cd pipeline; uv run ruff check .
    cd pipeline; uv run ruff format --check .

# Type-check
types:
    cd pipeline; uv run pyright

# Run the tests
test:
    cd pipeline; uv run pytest

# Check the factor catalogue
validate:
    cd pipeline; uv run atlas validate

# Regenerate every generated file from its source (never edit those by hand)
generate:
    cd pipeline; uv run atlas schemas

# Run the factor explorer's tests
explorer:
    node --test "docs/factors/*.test.mjs"

# Copy the catalogue into the factor explorer after an edit to catalogue/*.yaml
docs:
    node docs/factors/embed-catalogue.mjs

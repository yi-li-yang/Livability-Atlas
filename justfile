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
    cd web; npm ci

# Everything CI checks: lint, types, tests, the catalogue, and the factor explorer's tests
check: lint types test validate explorer

# Lint and check formatting
lint:
    cd pipeline; uv run ruff check .
    cd pipeline; uv run ruff format --check .
    cd web; npm run lint

# Type-check
types:
    cd pipeline; uv run pyright
    cd web; npm run types

# Run the tests
test:
    cd pipeline; uv run pytest
    cd web; npm test

# Check the factor catalogue
validate:
    cd pipeline; uv run atlas validate

# Regenerate every generated file from its source (never edit those by hand)
generate:
    cd pipeline; uv run atlas schemas
    cd web; npm run generate

# Build the web app
build:
    cd web; npm run build

# Build the web app, then run its end-to-end test (it downloads a browser the first time)
e2e: build
    cd web; npm run e2e

# Start the web app
dev:
    cd web; npm run dev

# Run the factor explorer's tests
explorer:
    node --test "docs/factors/*.test.mjs"

# Copy the catalogue into the factor explorer after an edit to catalogue/*.yaml
docs:
    node docs/factors/embed-catalogue.mjs

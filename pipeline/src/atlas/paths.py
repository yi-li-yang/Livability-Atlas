"""Where the repository's folders are, found from this file's place in the package."""

from pathlib import Path

# src/atlas/paths.py -> the repository root is three folders up.
REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOGUE_DIR = REPO_ROOT / "catalogue"
SCHEMAS_DIR = REPO_ROOT / "shared" / "schemas"

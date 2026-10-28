"""Where the repository's folders are, found from this file's place in the package."""

import os
from pathlib import Path

# src/atlas/paths.py -> the repository root is three folders up.
REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOGUE_DIR = REPO_ROOT / "catalogue"
SCHEMAS_DIR = REPO_ROOT / "shared" / "schemas"


def data_dir() -> Path:
    """The folder for raw, interim and published data. `ATLAS_DATA_DIR` overrides it."""
    return Path(os.environ.get("ATLAS_DATA_DIR") or REPO_ROOT / "data")

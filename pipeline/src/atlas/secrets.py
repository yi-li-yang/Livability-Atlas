"""Keys and tokens for the services that need one, kept out of the repository.

A secret is read from the environment, else from a line `NAME=value` of the `.env` file at the
repository root, which git ignores. Nothing here prints a value.
"""

import os
from pathlib import Path

from atlas.paths import REPO_ROOT


def secret(name: str, root: Path = REPO_ROOT) -> str:
    """The value of the secret `name`. Raises an error that names it, and never shows a value."""
    if value := os.environ.get(name):
        return value
    env_file = root / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.strip().removeprefix("export ").partition("=")
            if separator and key.strip() == name and value.strip().strip("\"'"):
                return value.strip().strip("\"'")
    raise RuntimeError(f"{name} is not set: put `{name}=...` in the .env file at the repo root")

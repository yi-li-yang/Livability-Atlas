"""Downloads raw data into `data/raw`, caching each file with its checksum beside it."""

import hashlib
from pathlib import Path

import requests

CHUNK = 1 << 20


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, target: Path) -> str:
    """Saves `url` to `target` unless it is already there and matches its recorded checksum.

    Returns the file's SHA-256, which is also written to `<target>.sha256`. The file is written to
    a temporary name first, so a failed download leaves no partial file.
    """
    checksum_file = target.with_name(target.name + ".sha256")
    if target.exists() and checksum_file.exists():
        recorded = checksum_file.read_text(encoding="utf-8").strip()
        if _sha256(target) == recorded:
            return recorded
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".part")
    try:
        with requests.get(url, stream=True, timeout=120) as reply:
            reply.raise_for_status()
            with partial.open("wb") as file:
                for chunk in reply.iter_content(CHUNK):
                    file.write(chunk)
        partial.replace(target)
    finally:
        partial.unlink(missing_ok=True)
    digest = _sha256(target)
    checksum_file.write_text(digest + "\n", encoding="utf-8", newline="\n")
    return digest

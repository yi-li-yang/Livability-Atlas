"""One request to TfL's Unified API, which answers without a key at a modest rate."""

import time
from typing import Any

import requests

API = "https://api.tfl.gov.uk/"
RETRIES = 8


def get(path: str, missing: bool = False) -> Any:
    """The JSON that the API answers to `path`, waiting and trying again when TfL asks to slow
    down. With `missing`, an answer that there is nothing (400 or 404) gives None."""
    for attempt in range(RETRIES):
        reply = requests.get(API + path, timeout=120)
        if reply.status_code == 429:
            time.sleep(15.0 * (attempt + 1))
            continue
        if missing and reply.status_code in (400, 404):
            return None
        reply.raise_for_status()
        return reply.json()
    raise RuntimeError(f"TfL kept refusing {path}")

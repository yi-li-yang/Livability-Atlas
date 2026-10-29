"""Boundaries from the ONS's ArcGIS services, in British National Grid.

The ONS serves its geographies as feature services that answer a query for what touches a box,
a page at a time. The result is kept as a GeoJSON file named by the box, so that a build asks
once.
"""

import hashlib
import json
from pathlib import Path

import requests

PAGE = 1000  # the services send at most this many features at a time

Bounds = tuple[float, float, float, float]


def fetch_features(data_dir: Path, name: str, service: str, field: str, bounds: Bounds) -> Path:
    """Downloads the areas of a service that touch `bounds` (x min, y min, x max, y max, in metres
    of British National Grid), with their `field`, to `data/raw/census/<name>-<key>.geojson` once,
    and returns the file. A failed download leaves no file."""
    key = hashlib.sha256(json.dumps(bounds).encode("utf-8")).hexdigest()[:10]
    target = data_dir / "raw" / "census" / f"{name}-{key}.geojson"
    if target.exists():
        return target
    features: list[dict] = []
    while True:
        reply = requests.get(
            service,
            params={
                "where": "1=1",
                "geometry": ",".join(str(round(b)) for b in bounds),
                "geometryType": "esriGeometryEnvelope",
                "inSR": 27700,
                "outSR": 27700,
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": field,
                "returnGeometry": "true",
                "resultOffset": len(features),
                "resultRecordCount": PAGE,
                "f": "geojson",
            },
            timeout=120,
        )
        reply.raise_for_status()
        body = reply.json()
        batch = body["features"]
        features += batch
        if not batch or not body.get("properties", {}).get("exceededTransferLimit"):
            break
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".part")
    partial.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}),
        encoding="utf-8",
        newline="\n",
    )
    partial.replace(target)
    return target

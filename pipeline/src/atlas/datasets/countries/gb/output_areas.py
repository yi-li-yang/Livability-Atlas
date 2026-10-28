"""The 2021 output areas of England and Wales (dataset `ons-output-area-boundaries`).

The ONS's generalised, clipped boundaries (BGC), served by its ArcGIS service in British National
Grid. Open Government Licence v3.0, with OS data under Crown copyright.
"""

import hashlib
import json
from pathlib import Path
from typing import cast

import geopandas as gpd
import requests

SERVICE = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Output_Areas_2021_EW_BGC_V2/FeatureServer/0/query"
)
PAGE = 1000  # the service sends at most this many features at a time

Bounds = tuple[float, float, float, float]


def fetch(data_dir: Path, bounds: Bounds) -> Path:
    """Downloads the output areas that touch `bounds` (x min, y min, x max, y max, in metres of
    British National Grid) to `data/raw/census/`, once, and returns the GeoJSON file."""
    key = hashlib.sha256(json.dumps(bounds).encode("utf-8")).hexdigest()[:10]
    target = data_dir / "raw" / "census" / f"output-areas-{key}.geojson"
    if target.exists():
        return target
    features: list[dict] = []
    while True:
        reply = requests.get(
            SERVICE,
            params={
                "where": "1=1",
                "geometry": ",".join(str(round(b)) for b in bounds),
                "geometryType": "esriGeometryEnvelope",
                "inSR": 27700,
                "outSR": 27700,
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "OA21CD",
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


def read_boundaries(path: Path) -> gpd.GeoDataFrame:
    """The output areas as a table with `OA21CD` and a geometry in British National Grid."""
    areas = gpd.read_file(path).set_crs("EPSG:27700", allow_override=True)
    return cast(gpd.GeoDataFrame, areas[["OA21CD", "geometry"]])

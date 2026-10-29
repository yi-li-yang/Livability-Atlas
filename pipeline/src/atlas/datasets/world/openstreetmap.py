"""OpenStreetMap's streets, paths and places (dataset `openstreetmap`).

Geofabrik's extract of Greater London, refreshed daily. The first download is kept, so a build
reads the same file until it is deleted. Open Database Licence 1.0, with attribution.
"""

from pathlib import Path

import osmium
import pandas as pd

from atlas.fetch import download

# One extract per region: the region's id picks it.
EXTRACTS = {
    "london": "https://download.geofabrik.de/europe/united-kingdom/england/greater-london-latest.osm.pbf",
}


def fetch(data_dir: Path, region_id: str) -> Path:
    """Downloads the region's extract to `data/raw/osm/` once, and returns it."""
    target = data_dir / "raw" / "osm" / f"{region_id.replace('london', 'greater-london')}.osm.pbf"
    download(EXTRACTS[region_id], target)
    return target


# The tags that mark the places we count, and the tag keys we keep for them.
PLACE_KEYS = ("amenity", "shop", "leisure")
KEPT_TAGS = ("name", "brand", "cuisine", *PLACE_KEYS)
# What the places of each key are, among the tags of OpenStreetMap.
PLACE_VALUES = {
    "amenity": {"restaurant", "cafe", "fast_food", "pub", "bar", "pharmacy", "library"},
    "shop": {"supermarket", "convenience", "greengrocer", "bakery", "butcher"},
    "leisure": {"fitness_centre"},
}


class _Places(osmium.SimpleHandler):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict[str, object]] = []

    def _keep(self, tags, lng: float, lat: float) -> None:
        wanted = {key: tags.get(key) for key in KEPT_TAGS}
        if not any(wanted[key] in values for key, values in PLACE_VALUES.items()):
            return
        self.rows.append({"lng": lng, "lat": lat, **wanted})

    def node(self, n) -> None:
        if len(n.tags) and n.location.valid():
            self._keep(n.tags, n.location.lon, n.location.lat)

    def way(self, w) -> None:
        if not len(w.tags):
            return
        nodes = [n for n in w.nodes if n.location.valid()]
        if len(nodes) > 1 and nodes[0].ref == nodes[-1].ref:
            nodes = nodes[:-1]  # a closed outline names its first node twice
        if nodes:
            lng = sum(n.lon for n in nodes) / len(nodes)
            lat = sum(n.lat for n in nodes) / len(nodes)
            self._keep(w.tags, lng, lat)


def read_places(path: Path) -> pd.DataFrame:
    """The places of the kinds we count in an OpenStreetMap file (`.osm.pbf` or `.osm`), as a
    table with `lng`, `lat`, `name`, `brand`, `cuisine`, `amenity`, `shop` and `leisure`. A
    building's place is the middle of its outline."""
    handler = _Places()
    handler.apply_file(str(path), locations=True)
    return pd.DataFrame(handler.rows, columns=["lng", "lat", *KEPT_TAGS])


def places(data_dir: Path, region_id: str) -> pd.DataFrame:
    """The region's places, read from its extract once. Reading takes about a minute, so the table
    is kept beside the extract, named by the first characters of the extract's checksum: a new
    extract has new places."""
    extract = fetch(data_dir, region_id)
    checksum = extract.with_name(extract.name + ".sha256").read_text(encoding="utf-8").strip()
    kept = extract.with_name(f"places-{region_id}-{checksum[:12]}.parquet")
    if kept.exists():
        return pd.read_parquet(kept)
    table = read_places(extract)
    table.to_parquet(kept)
    return table

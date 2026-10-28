"""OpenStreetMap's streets, paths and places (dataset `openstreetmap`).

Geofabrik's extract of Greater London, refreshed daily. The first download is kept, so a build
reads the same file until it is deleted. Open Database Licence 1.0, with attribution.
"""

from pathlib import Path

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

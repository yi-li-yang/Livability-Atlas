"""The planning data of the Department for Levelling Up's platform, planning.data.gov.uk
(datasets `historic-england-listed-buildings`, `conservation-areas` and the nature sites).

One CSV for each dataset, for all of England, rebuilt every day. The listed buildings are
Historic England's National Heritage List, and the conservation areas are the local authorities'.
Open Government Licence v3.0.
"""

import re
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.csv as pacsv
import shapely

from atlas.fetch import download

URL = "https://files.planning.data.gov.uk/dataset/{dataset}.csv"
BLOCK = 1 << 28  # an outline can be several megabytes of text, more than a default block
POINT = re.compile(r"POINT \(\s*(-?[\d.]+)\s+(-?[\d.]+)\s*\)")


def fetch(data_dir: Path, dataset: str) -> Path:
    """Downloads the dataset's CSV to `data/raw/planning/` once, and returns it. The file is
    rebuilt daily: delete it to get the newest."""
    path = data_dir / "raw" / "planning" / f"{dataset}.csv"
    download(URL.format(dataset=dataset), path)
    return path


def _read(path: Path, columns: list[str]) -> dict[str, np.ndarray]:
    table = pacsv.read_csv(
        path,
        read_options=pacsv.ReadOptions(block_size=BLOCK),
        convert_options=pacsv.ConvertOptions(
            include_columns=columns, column_types={c: pa.string() for c in columns}
        ),
    )
    return {c: np.array(table[c].to_pylist(), dtype=object) for c in columns}


def _points(texts: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The longitude and latitude of each `POINT (lng lat)`, NaN where there is none."""
    lng, lat = np.full(len(texts), np.nan), np.full(len(texts), np.nan)
    for i, text in enumerate(texts):
        found = POINT.match(text) if isinstance(text, str) else None
        if found:
            lng[i], lat[i] = float(found.group(1)), float(found.group(2))
    return lng, lat


def _ended(texts: np.ndarray) -> np.ndarray:
    return np.array([isinstance(t, str) and t.strip() != "" for t in texts])


def _inside(lng: np.ndarray, lat: np.ndarray, box: tuple[float, float, float, float]) -> np.ndarray:
    west, south, east, north = box
    with np.errstate(invalid="ignore"):
        return (lng >= west) & (lng <= east) & (lat >= south) & (lat <= north)


def read_listed_buildings(path: Path, box: tuple[float, float, float, float]) -> pd.DataFrame:
    """The listed buildings in `box` (west, south, east, north, in degrees) that are still
    listed, with their `lng` and `lat`. A terrace listed house by house counts house by house."""
    table = _read(path, ["end-date", "point"])
    lng, lat = _points(table["point"])
    keep = _inside(lng, lat, box) & ~_ended(table["end-date"])
    return pd.DataFrame({"lng": lng[keep], "lat": lat[keep]})


def read_areas(path: Path, box: tuple[float, float, float, float]) -> gpd.GeoDataFrame:
    """The areas of an outline dataset (conservation areas, nature reserves) whose point is in
    `box`, as polygons in degrees (EPSG:4326). An area with no outline is left out."""
    table = _read(path, ["end-date", "geometry", "point"])
    lng, lat = _points(table["point"])
    drawn = np.array([isinstance(g, str) and g.strip() != "" for g in table["geometry"]])
    keep = _inside(lng, lat, box) & ~_ended(table["end-date"]) & drawn
    outlines = shapely.from_wkt(table["geometry"][keep].tolist())
    return gpd.GeoDataFrame({"geometry": outlines}, geometry="geometry", crs="EPSG:4326")

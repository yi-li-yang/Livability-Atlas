"""Spike S1: can the PTAL grid be mapped to hex cells? Throwaway code, never imported by `atlas`.

Run from `pipeline/` with `uv run python notebooks/s1_ptal_to_hex.py` after putting the
unzipped 2015 PTAL files in `data/raw/ptal/`. It prints the numbers that
docs/spikes/S1-ptal.md reports.
"""

import json

import h3
import numpy as np
import openpyxl
import pandas as pd
import pyogrio
import shapely
from pyproj import Transformer
from shapely.ops import unary_union

from atlas.paths import data_dir

RESOLUTION = 9
RAW = data_dir() / "raw" / "ptal"
# The access index limits of the PTAL bands (TfL's Connectivity Assessment Guide).
BAND_LIMITS = [
    (0.0, "0"),
    (2.5, "1a"),
    (5.0, "1b"),
    (10.0, "2"),
    (15.0, "3"),
    (20.0, "4"),
    (25.0, "5"),
    (40.0, "6a"),
    (float("inf"), "6b"),
]


def band(index: float) -> str:
    if index <= 0:
        return "0"
    for limit, name in BAND_LIMITS[1:]:
        if index <= limit:
            return name
    return "6b"


def read_grid() -> pd.DataFrame:
    sheet = openpyxl.load_workbook(next(RAW.glob("*Grid Values*.xlsx")), read_only=True).worksheets[
        0
    ]
    rows = sheet.iter_rows(values_only=True)
    header = next(rows)
    return pd.DataFrame(list(rows), columns=list(header))


def main() -> None:
    grid = read_grid()
    to_wgs84 = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
    lng, lat = to_wgs84.transform(grid["X"].to_numpy(), grid["Y"].to_numpy())
    grid["cell"] = [h3.latlng_to_cell(a, o, RESOLUTION) for a, o in zip(lat, lng, strict=True)]
    result: dict[str, object] = {
        "grid points": len(grid),
        "spacing check, first x steps": grid["X"].diff().dropna().mode().tolist(),
    }

    # What the PTAL2015 code means: the access index range of each code.
    codes = grid.groupby("PTAL2015")["AI2015"].agg(["min", "max", "count"])
    result["code ranges"] = codes.round(2).reset_index().to_dict("records")

    per_cell = grid.groupby("cell")["AI2015"].agg(["mean", "min", "max", "count"])
    per_cell["band"] = per_cell["mean"].map(band)
    result["cells with grid points"] = len(per_cell)
    result["points per cell, quantiles"] = (
        per_cell["count"].quantile([0, 0.05, 0.25, 0.5, 0.75, 1]).to_dict()
    )

    # Every cell that the contours cover, with or without a grid point.
    contours = pyogrio.read_dataframe(next(RAW.glob("*Contours*.TAB"))).set_crs(
        "EPSG:27700", allow_override=True
    )
    outline = unary_union(contours.to_crs("EPSG:4326").geometry.tolist())
    polygons = [outline] if outline.geom_type == "Polygon" else list(outline.geoms)
    covered: set[str] = set()
    for polygon in polygons:
        covered |= set(
            h3.h3shape_to_cells(
                h3.LatLngPoly([(y, x) for x, y in polygon.exterior.coords]), RESOLUTION
            )
        )
    result["cells under the contours"] = len(covered)
    result["covered cells with no grid point"] = len(covered - set(per_cell.index))
    result["grid-point cells outside the contours"] = len(set(per_cell.index) - covered)

    # How much a cell's points disagree: bands at the cell's lowest and highest point.
    spread = per_cell.assign(low=per_cell["min"].map(band), high=per_cell["max"].map(band))
    result["cells whose points all share one band"] = float(
        (spread["low"] == spread["high"]).mean()
    )
    result["median access index spread within a cell"] = float(
        (per_cell["max"] - per_cell["min"]).median()
    )

    # Mean-of-points band against the band of the grid point nearest to the cell's centre.
    centres = np.array([h3.cell_to_latlng(c) for c in per_cell.index])
    to_osgb = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
    cx, cy = to_osgb.transform(centres[:, 1], centres[:, 0])
    tree = shapely.STRtree(shapely.points(grid["X"].to_numpy(), grid["Y"].to_numpy()))
    nearest = tree.nearest(shapely.points(cx, cy))
    centre_band = grid["AI2015"].to_numpy()[nearest]
    agree = np.array([band(v) for v in centre_band]) == per_cell["band"].to_numpy()
    result["mean band equals the band at the cell centre"] = float(agree.mean())
    result["mean band within one band of the centre's"] = float(
        np.mean(
            [
                abs(_order(band(v)) - _order(b)) <= 1
                for v, b in zip(centre_band, per_cell["band"], strict=True)
            ]
        )
    )
    result["band counts of cells"] = per_cell["band"].value_counts().to_dict()

    # The band that covers most of the cell (the catalogue's current wording) against the mean's.
    grid["band"] = grid["AI2015"].map(band)
    shares = grid.groupby(["cell", "band"]).size().rename("n").reset_index()
    top = shares.sort_values("n", ascending=False).drop_duplicates("cell").set_index("cell")
    modal = top["band"].reindex(per_cell.index)
    tied = shares.merge(top["n"].rename("top"), left_on="cell", right_index=True)
    tied = tied[tied["n"] == tied["top"]].groupby("cell").size()
    result["cells where two or more bands tie for most common"] = float((tied > 1).mean())
    result["share of a cell's points in its most common band, mean"] = float(
        (top["n"] / per_cell["count"]).mean()
    )
    result["cells where the most common band covers more than half the points"] = float(
        (top["n"] / per_cell["count"] > 0.5).mean()
    )
    result["most common band equals the mean's band"] = float((modal == per_cell["band"]).mean())
    result["most common band equals the band at the centre"] = float(
        (modal.to_numpy() == np.array([band(v) for v in centre_band])).mean()
    )
    print(json.dumps(result, indent=2, default=float))


def _order(name: str) -> int:
    return [b for _, b in BAND_LIMITS].index(name)


if __name__ == "__main__":
    main()

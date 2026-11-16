"""ESA WorldCover's land cover map, 10 m, 2021 (dataset `esa-worldcover`): one class for each
10 m pixel of the world, such as tree cover (10), built-up (50) and permanent water (80). Licence:
Creative Commons Attribution 4.0 (CC BY 4.0).

The map comes in tiles of 3 degrees, each a GeoTIFF on Amazon S3 that anyone can download. The
release is pinned in the address.
"""

import math
from pathlib import Path

import h3
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import from_bounds
from scipy.spatial import KDTree

from atlas.fetch import download

URL = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/{name}"
NAME = "ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
TILE = 3  # degrees


def tile_names(box: tuple[float, float, float, float]) -> list[str]:
    """The names of the tiles that cover `box` (west, south, east, north, in degrees): a tile is
    named for its south-west corner, such as `N51W003`. Those in the west come first."""
    west, south, east, north = box
    names = []
    for lat in range(math.floor(south / TILE) * TILE, math.floor(north / TILE) * TILE + 1, TILE):
        for lng in range(math.floor(west / TILE) * TILE, math.floor(east / TILE) * TILE + 1, TILE):
            names.append(
                f"{'N' if lat >= 0 else 'S'}{abs(lat):02d}{'E' if lng >= 0 else 'W'}{abs(lng):03d}"
            )
    return names


def fetch(data_dir: Path, box: tuple[float, float, float, float]) -> list[Path]:
    """Downloads the tiles that cover `box` to `data/raw/worldcover/` once each (about 100 MB a
    tile), and returns them."""
    paths = []
    for tile in tile_names(box):
        name = NAME.format(tile=tile)
        target = data_dir / "raw" / "worldcover" / name
        download(URL.format(name=name), target)
        paths.append(target)
    return paths


def class_shares(
    paths: list[Path], cells: list[str], classes: dict[str, int], stride: int = 3
) -> pd.DataFrame:
    """The percent of each cell's pixels in each class of `classes` (a name for each class code).

    A pixel belongs to the cell whose centre is nearest, among `cells`, if it is within a cell's
    reach of it. Every `stride`th pixel is read, in each direction. A cell with no pixel in the
    tiles has no value.
    """
    resolution = h3.get_resolution(cells[0])
    centres = np.array([h3.cell_to_latlng(c) for c in cells])
    shrink = math.cos(math.radians(float(centres[:, 0].mean())))
    reach = h3.average_hexagon_edge_length(resolution, unit="m") / 111_320.0  # degrees of latitude
    tree = KDTree(np.column_stack([centres[:, 0], centres[:, 1] * shrink]))
    total = np.zeros(len(cells))
    counts = {name: np.zeros(len(cells)) for name in classes}
    margin = 2 * reach
    area = (
        centres[:, 1].min() - margin,
        centres[:, 0].min() - margin,
        centres[:, 1].max() + margin,
        centres[:, 0].max() + margin,
    )
    for path in paths:
        with rasterio.open(path) as tile:
            west = max(area[0], tile.bounds.left)
            south = max(area[1], tile.bounds.bottom)
            east = min(area[2], tile.bounds.right)
            north = min(area[3], tile.bounds.top)
            if west >= east or south >= north:
                continue
            window = from_bounds(west, south, east, north, transform=tile.transform)
            window = window.round_offsets().round_lengths()
            rows, cols = max(int(window.height) // stride, 1), max(int(window.width) // stride, 1)
            data = tile.read(1, window=window, out_shape=(rows, cols))
            scale_x, scale_y = window.width / cols, window.height / rows
            xs = (
                tile.transform.c
                + (window.col_off + (np.arange(cols) + 0.5) * scale_x) * tile.transform.a
            )
            ys = (
                tile.transform.f
                + (window.row_off + (np.arange(rows) + 0.5) * scale_y) * tile.transform.e
            )
        lng, lat = np.meshgrid(xs, ys)
        distance, owner = tree.query(np.column_stack([lat.ravel(), (lng * shrink).ravel()]))
        near = distance <= reach
        flat = data.ravel()
        total += np.bincount(owner[near], minlength=len(cells))
        for name, code in classes.items():
            hit = near & (flat == code)
            counts[name] += np.bincount(owner[hit], minlength=len(cells))
    with np.errstate(invalid="ignore", divide="ignore"):
        shares = {
            name: np.where(total > 0, 100.0 * n / total, np.nan) for name, n in counts.items()
        }
    return pd.DataFrame(shares, index=cells)

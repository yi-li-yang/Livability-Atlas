"""Modelled daytime noise from roads, railways and airports in England, from Defra's strategic noise
maps of Round 4 (datasets `defra-road-noise`, `defra-rail-noise` and `defra-airport-noise`). Open
Government Licence v3.0.

Each map is the level LAeq,16h, the average sound level from 07:00 to 23:00 in 2022, on a 10 m
grid at 4 m above ground, served by Defra's WCS in tiles that are kept in `data/raw/noise/`. The
maps stop at 40 dB. A pixel below that, or with no value, counts as 40 dB.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
import requests

TILE = 10_000  # metres: the size of a tile asked of the service
ORIGIN = (3_000, 5_000)  # a corner of the tile grid: Greater London's tiles start at 503000, 155000
PIXEL = 10.0
FLOOR = 40.0  # the maps' cut-off: anything below counts as this
HUGE = 1e30  # a value this large is the airport maps' "no value"


@dataclass(frozen=True)
class Source:
    wcs: str
    coverage: str


SOURCES = {
    "road": Source(
        "https://environment.data.gov.uk/spatialdata/road-noise-all-metrics-england-round-4/wcs",
        "562c9d56-7c2d-4d42-83bb-578d6e97a517__Road_Noise_LAeq16hr_England_Round_4_All",
    ),
    "rail": Source(
        "https://environment.data.gov.uk/spatialdata/noise-data/wcs",
        "3fb3c2d7-292c-4e0a-bd5b-d8e4e1fe2947__Rail_Noise_LAeq16hr_England_Round_4_All",
    ),
    "aircraft": Source(
        "https://environment.data.gov.uk/spatialdata/airport-noise-all-metrics-england-round-4/wcs",
        "dac9cba4-abe7-43bd-b8e9-8a83da52edd8__Airport_Noise_ALL_LAeq16hr",
    ),
}


def fetch(data_dir: Path, kind: str, bounds: tuple[float, float, float, float]) -> list[Path]:
    """The tiles of one kind of noise that cover `bounds` (west, south, east, north, in metres of
    British National Grid). A tile is downloaded once and kept."""
    source = SOURCES[kind]
    folder = data_dir / "raw" / "noise"
    west, south, east, north = bounds
    paths = []
    first_x = ORIGIN[0] + int((west - ORIGIN[0]) // TILE) * TILE
    first_y = ORIGIN[1] + int((south - ORIGIN[1]) // TILE) * TILE
    for x in range(first_x, int(east) + 1, TILE):
        for y in range(first_y, int(north) + 1, TILE):
            path = folder / f"{kind}-laeq16-{x}-{y}.tif"
            if not path.exists():
                folder.mkdir(parents=True, exist_ok=True)
                reply = requests.get(
                    source.wcs,
                    params={
                        "service": "WCS",
                        "version": "2.0.1",
                        "request": "GetCoverage",
                        "coverageId": source.coverage,
                        "format": "image/tiff",
                        "subset": [f"E({x},{x + TILE})", f"N({y},{y + TILE})"],
                    },
                    timeout=300,
                )
                reply.raise_for_status()
                path.write_bytes(reply.content)
            paths.append(path)
    return paths


@dataclass
class Levels:
    """Noise levels on a grid of 10 m pixels: `values[row][column]`, rows running southwards from
    `north`. A place the tiles do not cover has no level."""

    west: float
    north: float
    values: np.ndarray

    def at(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """The level (dB) of the pixel that holds each place, or `nan` outside the tiles."""
        column = np.floor((x - self.west) / PIXEL).astype(np.int64)
        row = np.floor((self.north - y) / PIXEL).astype(np.int64)
        inside = (column >= 0) & (column < self.values.shape[1])
        inside &= (row >= 0) & (row < self.values.shape[0])
        found = np.full(len(x), np.nan)
        found[inside] = self.values[row[inside], column[inside]]
        return found


def read_levels(paths: list[Path]) -> Levels:
    """The tiles joined into one grid. Every tile lines up with a 10 m grid."""
    tiles = []
    for path in paths:
        with rasterio.open(path) as file:
            level = file.read(1).astype(np.float32)
            tiles.append((file.bounds.left, file.bounds.top, level))
    west = min(left for left, _, _ in tiles)
    north = max(top for _, top, _ in tiles)
    east = max(left + level.shape[1] * PIXEL for left, _, level in tiles)
    south = min(top - level.shape[0] * PIXEL for _, top, level in tiles)
    values = np.full((round((north - south) / PIXEL), round((east - west) / PIXEL)), np.nan, "f4")
    for left, top, level in tiles:
        level = np.where((level < FLOOR) | (level > HUGE) | np.isnan(level), FLOOR, level)
        row, column = round((north - top) / PIXEL), round((left - west) / PIXEL)
        values[row : row + level.shape[0], column : column + level.shape[1]] = level
    return Levels(west=west, north=north, values=values)

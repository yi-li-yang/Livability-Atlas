"""The Environment Agency's flood risk for England (datasets `ea-flood-risk-rivers-sea` and
`ea-flood-risk-surface-water`), from the National Flood Risk Assessment 2 (NaFRA2).

The agency serves the risk in four bands as a map (a WMS) and not as polygons. Each band has its
own flat colour, so this draws the area that a region covers in tiles at 10 m a pixel, and reads the
band off each pixel's colour. A pixel with no colour at all lies outside every band, which is
safe: the bands start at "very low", under 1 in 1000 a year. Outlines and the soft edges of
polygons are not a band and are left out. Open Government Licence v3.0.
"""

import hashlib
import io
import json
import time
from collections.abc import Iterator
from dataclasses import dataclass
from math import ceil
from pathlib import Path

import numpy as np
import requests
from PIL import Image

Bounds = tuple[float, float, float, float]

# The classes of a pixel. A band's higher number is a higher risk.
NONE, VERY_LOW, LOW, MEDIUM, HIGH = 0, 1, 2, 3, 4
UNKNOWN = 255
BANDS = {
    HIGH: (85, 91, 157),  # 1 in 30 a year or more
    MEDIUM: (154, 159, 222),  # 1 in 100 to 1 in 30
    LOW: (195, 224, 255),  # 1 in 1000 to 1 in 100
    VERY_LOW: (200, 247, 255),  # under 1 in 1000
}
TOLERANCE = 3  # levels of a colour channel

RESOLUTION = 10  # metres a pixel
TILE = 2000  # pixels along a side of one request

SERVICES = {
    "rivers-and-sea": ("nafra2-risk-of-flooding-from-rivers-and-sea", "rofrs_4band"),
    "surface-water": ("nafra2-risk-of-flooding-from-surface-water", "rofsw"),
}
ROOT = "https://environment.data.gov.uk/spatialdata"


@dataclass
class Mosaic:
    """The class of every pixel over an area. `x` is its west edge and `y` its north edge, in metres
    of British National Grid, and row 0 is the northernmost."""

    classes: np.ndarray
    x: float
    y: float
    resolution: float

    def at(self, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
        """The class at each point, or UNKNOWN for a point outside the mosaic."""
        cols = np.floor((xs - self.x) / self.resolution).astype(int)
        rows = np.floor((self.y - ys) / self.resolution).astype(int)
        inside = (rows >= 0) & (rows < self.classes.shape[0]) & (cols >= 0)
        inside &= cols < self.classes.shape[1]
        out = np.full(xs.shape, UNKNOWN, dtype=np.uint8)
        out[inside] = self.classes[rows[inside], cols[inside]]
        return out


@dataclass
class Tile:
    """One request: the pixels it fills, and the box it asks for."""

    row: int
    col: int
    rows: int
    cols: int
    x: float  # south-west corner, in metres
    y: float


def shape(bounds: Bounds, resolution: float = RESOLUTION) -> tuple[int, int]:
    """The rows and columns of pixels that cover `bounds`."""
    return (
        ceil((bounds[3] - bounds[1]) / resolution),
        ceil((bounds[2] - bounds[0]) / resolution),
    )


def tiles(bounds: Bounds, resolution: float = RESOLUTION, size: int = TILE) -> Iterator[Tile]:
    """The requests that together cover `bounds`, in tiles of at most `size` pixels a side."""
    rows, cols = shape(bounds, resolution)
    for row in range(0, rows, size):
        for col in range(0, cols, size):
            height, width = min(size, rows - row), min(size, cols - col)
            yield Tile(
                row=row,
                col=col,
                rows=height,
                cols=width,
                x=bounds[0] + col * resolution,
                y=bounds[3] - (row + height) * resolution,
            )


def classify(rgba: np.ndarray) -> np.ndarray:
    """The class of each pixel of an image (rows, columns, RGBA) in the service's colours."""
    out = np.full(rgba.shape[:2], UNKNOWN, dtype=np.uint8)
    rgb, alpha = rgba[..., :3].astype(int), rgba[..., 3]
    for band, colour in BANDS.items():
        near = (np.abs(rgb - np.array(colour)) <= TOLERANCE).all(axis=-1) & (alpha == 255)
        out[near] = band
    out[alpha == 0] = NONE
    return out


def _get_tile(service: str, layer: str, tile: Tile, resolution: float) -> np.ndarray:
    box = (tile.x, tile.y, tile.x + tile.cols * resolution, tile.y + tile.rows * resolution)
    params = {
        "service": "WMS",
        "version": "1.3.0",
        "request": "GetMap",
        "layers": layer,
        "styles": "",
        "crs": "EPSG:27700",
        "bbox": ",".join(str(round(b, 3)) for b in box),
        "width": tile.cols,
        "height": tile.rows,
        "format": "image/png",
        "transparent": "true",
    }
    last: Exception | None = None
    for attempt in range(4):
        try:
            reply = requests.get(f"{ROOT}/{service}/wms", params=params, timeout=300)
            reply.raise_for_status()
            if not reply.headers.get("content-type", "").startswith("image/"):
                kind = reply.headers.get("content-type")
                raise ValueError(f"the service sent {kind}, not a map")
            return np.asarray(Image.open(io.BytesIO(reply.content)).convert("RGBA"))
        except (requests.RequestException, ValueError) as error:
            last = error
            time.sleep(2**attempt)
    raise RuntimeError(f"could not get a flood risk map from {service}: {last}")


def fetch(data_dir: Path, which: str, bounds: Bounds, resolution: float = RESOLUTION) -> Mosaic:
    """The classes of the area in `bounds` for `which` ("rivers-and-sea" or "surface-water").

    The tiles are downloaded once, and the classified mosaic is kept in `data/raw/ea-flood/`.
    """
    service, layer = SERVICES[which]
    key = hashlib.sha256(json.dumps([bounds, resolution]).encode("utf-8")).hexdigest()[:10]
    target = data_dir / "raw" / "ea-flood" / f"{which}-{key}.npz"
    x, y = float(bounds[0]), float(bounds[3])
    if target.exists():
        with np.load(target) as saved:
            return Mosaic(classes=saved["classes"], x=x, y=y, resolution=resolution)
    rows, cols = shape(bounds, resolution)
    classes = np.full((rows, cols), UNKNOWN, dtype=np.uint8)
    for tile in tiles(bounds, resolution):
        picture = _get_tile(service, layer, tile, resolution)
        classes[tile.row : tile.row + tile.rows, tile.col : tile.col + tile.cols] = classify(
            picture[: tile.rows, : tile.cols]
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".part.npz")
    np.savez_compressed(partial, classes=classes)
    partial.replace(target)
    return Mosaic(classes=classes, x=x, y=y, resolution=resolution)

"""London's modelled air pollution, from the London Atmospheric Emissions Inventory 2022 (dataset
`laei`), by the Greater London Authority and Transport for London.

The Datastore states no licence for it ("Not Specified"), so it stays out of public builds. The
download's CSV holds one table per pollutant (`x`, `y` in metres of British National Grid, and
`conc` in µg/m³), on a 20 m grid.
"""

import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from atlas.fetch import download

URL = "https://data.london.gov.uk/download/2lg5g/7jy/LAEI2022-Concentrations-Data-CSV.zip"
STEP = 20.0  # metres between points


@dataclass
class Grid:
    """Concentrations on a regular grid: `values[row][column]`, `nan` where there is no point."""

    x0: float
    y0: float
    values: np.ndarray

    def at(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """The value of the nearest point to each place, or `nan` outside the grid."""
        column = np.rint((x - self.x0) / STEP).astype(np.int64)
        row = np.rint((y - self.y0) / STEP).astype(np.int64)
        inside = (column >= 0) & (column < self.values.shape[1])
        inside &= (row >= 0) & (row < self.values.shape[0])
        found = np.full(len(x), np.nan)
        found[inside] = self.values[row[inside], column[inside]]
        return found


def fetch(data_dir: Path) -> Path:
    """Downloads the CSV files to `data/raw/laei/` once (about 180 MB), and returns the zip."""
    target = data_dir / "raw" / "laei" / "LAEI2022-Concentrations-Data-CSV.zip"
    download(URL, target)
    return target


def read_concentrations(path: Path, pollutant: str) -> Grid:
    """The grid of one pollutant's annual mean concentration: `NO2` or `PM25`, among others."""
    with zipfile.ZipFile(path) as archive, archive.open(f"CSV/LAEI2022_V1_{pollutant}.csv") as file:
        table = pd.read_csv(file, dtype={"x": np.float64, "y": np.float64, "conc": np.float32})
    xs, ys = table["x"].to_numpy(), table["y"].to_numpy()
    x0, y0 = float(xs.min()), float(ys.min())
    column = np.rint((xs - x0) / STEP).astype(np.int64)
    row = np.rint((ys - y0) / STEP).astype(np.int64)
    values = np.full((int(row.max()) + 1, int(column.max()) + 1), np.nan, dtype=np.float32)
    values[row, column] = table["conc"].to_numpy()
    return Grid(x0=x0, y0=y0, values=values)

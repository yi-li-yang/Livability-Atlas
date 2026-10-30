"""Road collisions that injured someone, reported to the police of Great Britain (dataset
`dft-stats19`).

The Department for Transport's road safety data (STATS19): one file of collisions a year, each
with its place and its severity (fatal, serious or slight). Open Government Licence v3.0. The
police record a collision when it is reported to them; slight injuries are reported less reliably
than serious ones, so only fatal and serious collisions are counted.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.csv as pacsv

from atlas.fetch import download

YEARS = (2022, 2023, 2024)  # the latest three full years
FATAL, SERIOUS = 1, 2


def url(year: int) -> str:
    return (
        "https://data.dft.gov.uk/road-accidents-safety-data/"
        f"dft-road-casualty-statistics-collision-{year}.csv"
    )


def fetch(data_dir: Path, years: tuple[int, ...] = YEARS) -> list[Path]:
    """Downloads each year's file (about 20 MB) to `data/raw/dft/` once, and returns them."""
    paths = []
    for year in years:
        target = data_dir / "raw" / "dft" / f"collisions-{year}.csv"
        download(url(year), target)
        paths.append(target)
    return paths


def read_collisions(paths: list[Path]) -> pd.DataFrame:
    """The fatal and serious collisions with their `Longitude` and `Latitude`. A collision with no
    place is left out."""
    longitudes, latitudes = [], []
    for path in paths:
        table = pacsv.read_csv(
            path,
            convert_options=pacsv.ConvertOptions(
                include_columns=["longitude", "latitude", "collision_severity"],
                column_types={
                    "longitude": pa.float64(),
                    "latitude": pa.float64(),
                    "collision_severity": pa.int64(),
                },
            ),
        )
        severity = table["collision_severity"].to_numpy(zero_copy_only=False)
        longitude = table["longitude"].to_numpy(zero_copy_only=False)
        latitude = table["latitude"].to_numpy(zero_copy_only=False)
        keep = np.isin(severity, [FATAL, SERIOUS]) & ~np.isnan(longitude) & ~np.isnan(latitude)
        longitudes.append(longitude[keep])
        latitudes.append(latitude[keep])
    return pd.DataFrame(
        {"Longitude": np.concatenate(longitudes), "Latitude": np.concatenate(latitudes)}
    )

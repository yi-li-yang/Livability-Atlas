"""The stops and stations of Great Britain, from the Department for Transport's NaPTAN (dataset
`naptan`). Open Government Licence v3.0."""

from pathlib import Path

import pandas as pd

from atlas.fetch import download

URL = "https://naptan.api.dft.gov.uk/v1/access-nodes?dataFormat=csv"
# The stop types of stations: rail station entrances and the metro (Tube, DLR, tram) ones.
STATION_TYPES = ("RLY", "MET")


def fetch(data_dir: Path) -> Path:
    """Downloads the national file to `data/raw/naptan/` once (about 100 MB), and returns it."""
    target = data_dir / "raw" / "naptan" / "naptan.csv"
    download(URL, target)
    return target


def read_stations(path: Path) -> pd.DataFrame:
    """The active station entrances, with their `Longitude` and `Latitude`."""
    frame = pd.read_csv(
        path, usecols=["StopType", "Status", "Longitude", "Latitude"], encoding="utf-8"
    )
    is_station = frame["StopType"].isin(list(STATION_TYPES)) & (frame["Status"] == "active")
    stations = frame.loc[is_station, ["Longitude", "Latitude"]].dropna()
    return stations.reset_index(drop=True)

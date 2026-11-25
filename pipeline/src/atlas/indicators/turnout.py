"""Election turnout: the share of a ward's electors who voted, joined to the ward's boundary by its
borough and name, and given to each hex cell whose centre lies in the ward.
"""

import re
from collections.abc import Mapping
from typing import cast

import geopandas as gpd
import numpy as np
import pandas as pd

from atlas.spatial.grid import cell_centres_bng


def name_key(name: str) -> str:
    """A ward's or a borough's name in a form that two spellings of it share: lower case, "&" as
    "and", no apostrophes or full stops, single spaces."""
    text = str(name).lower().replace("&", " and ")
    text = re.sub(r"['’‘`´.]", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def by_ward(results: pd.DataFrame, wards: gpd.GeoDataFrame) -> pd.Series:
    """Each ward's turnout in % (ballot papers at the count over the electorate), indexed by its
    code; NaN for a ward with no result, such as the City of London's."""
    found = {
        (name_key(b), name_key(w)): 100.0 * ballots / electorate
        for b, w, ballots, electorate in results[
            ["borough", "ward", "ballots", "electorate"]
        ].itertuples(index=False)
        if electorate > 0
    }
    keys = zip(wards["LAD22NM"].map(name_key), wards["WD22NM"].map(name_key), strict=True)
    return pd.Series([found.get(k, np.nan) for k in keys], index=wards["WD22CD"].to_numpy())


def by_cell(wards: gpd.GeoDataFrame, turnout: Mapping[str, float], cells: list[str]) -> np.ndarray:
    """The turnout of the ward that each cell's centre lies in; NaN outside every ward, or in a
    ward with none."""
    centres = cell_centres_bng(cells)
    points = gpd.GeoDataFrame(
        {"cell": range(len(cells))},
        geometry=gpd.points_from_xy(centres[:, 0], centres[:, 1]),
        crs="EPSG:27700",
    )
    areas = cast(gpd.GeoDataFrame, wards[["WD22CD", "geometry"]])
    joined = gpd.sjoin(points, areas, how="left", predicate="within")
    joined = joined.drop_duplicates("cell").sort_values("cell")
    return np.array([turnout.get(code, np.nan) for code in joined["WD22CD"]], dtype=float)

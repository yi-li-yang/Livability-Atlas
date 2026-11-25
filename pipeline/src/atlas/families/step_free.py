"""Transport: the walk to the nearest station that is step-free from the street to every platform
(`step-free-access`), from TfL's station topology (`tfl_stationdata`), and for the stations that it
does not hold, served by National Rail alone, from OpenStreetMap's `wheelchair=yes`. See the
indicator's method in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
from scipy.spatial import KDTree

from atlas.datasets.cities.london import tfl_stationdata
from atlas.datasets.world import openstreetmap
from atlas.families import Context, Family
from atlas.indicators.transport import place_stops


def step_free_places(stations: pd.DataFrame) -> pd.DataFrame:
    """The stations whose every platform is step-free from the street, with a place (`Easting`,
    `Northing`); a station without one is left out."""
    found = stations.loc[stations["all_step_free"]].dropna(subset=["Latitude", "Longitude"])
    return place_stops(pd.DataFrame(found))


# An OpenStreetMap station this near a station of TfL's is the same station, or one TfL covers.
SAME_STATION_METRES = 300


def beyond_tfl(osm: pd.DataFrame, tfl: pd.DataFrame) -> pd.DataFrame:
    """The OpenStreetMap stations (`lng`, `lat`, `wheelchair`) tagged `wheelchair=yes` that lie
    more than `SAME_STATION_METRES` from every station of TfL's (`Latitude`, `Longitude`), with a
    place (`Easting`, `Northing`)."""
    tagged = osm.loc[osm["wheelchair"] == "yes"].rename(
        columns={"lat": "Latitude", "lng": "Longitude"}
    )
    if tagged.empty:
        return place_stops(pd.DataFrame(tagged))
    ours = place_stops(pd.DataFrame(tfl.dropna(subset=["Latitude", "Longitude"])))
    theirs = place_stops(pd.DataFrame(tagged))
    metres, _ = KDTree(ours[["Easting", "Northing"]].to_numpy()).query(
        theirs[["Easting", "Northing"]].to_numpy()
    )
    return theirs.loc[np.asarray(metres) > SAME_STATION_METRES]


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    stations = tfl_stationdata.read_stations(*tfl_stationdata.fetch(ctx.data_dir))
    others = beyond_tfl(openstreetmap.stations(ctx.data_dir, ctx.region_id), stations)
    where = ["Easting", "Northing"]
    places = pd.DataFrame(
        pd.concat([step_free_places(stations)[where], others[where]], ignore_index=True)
    )
    return {"step-free-access": ctx.walk_to_nearest(places)}


# TfL's topology covers London's stations only.
FAMILY = Family("step_free", columns, regions=("london",))

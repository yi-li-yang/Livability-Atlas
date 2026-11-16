import h3
import numpy as np
import pandas as pd
from pyproj import Transformer

from atlas.catalogue.load import load_catalogue
from atlas.datasets.cities.london import tfl_lines
from atlas.families import Context, Family, discover, run
from atlas.families import night_services as family
from atlas.paths import CATALOGUE_DIR

CELL = h3.latlng_to_cell(51.5136, -0.1337, 9)
LAT, LNG = h3.cell_to_latlng(CELL)


def stops() -> pd.DataFrame:
    def row(kind, line, stop):
        return {"kind": kind, "line": line, "stop": stop, "Latitude": LAT, "Longitude": LNG}

    return pd.DataFrame(
        [
            row("bus", "n29", "b1"),
            row("bus", "n29", "b2"),  # a route counts once
            row("bus", "n9", "b1"),
            row("bus", "29", "b1"),  # a day route is not a night route
            row("bus", "nx", "b1"),  # not "n" and a number
            row("rail", "central", "r1"),
            row("rail", "elizabeth", "r1"),  # no night service
            row("rail", "windrush", "r1"),
        ]
    )


class Network:
    """Every stop is within reach of every cell; it records the walks it was asked for."""

    def __init__(self):
        self.asked = []

    def places_within(self, places, origins, minutes):
        self.asked.append(minutes)
        return [np.arange(len(places)) for _ in origins]


def context(tmp_path, network) -> Context:
    region = load_catalogue(CATALOGUE_DIR).regions["london"]
    return Context("london", region, [CELL], tmp_path, pd.DataFrame(), network)  # type: ignore[arg-type]


def test_night_routes_and_night_lines_within_a_walk_are_counted_together(tmp_path, monkeypatch):
    monkeypatch.setattr(tfl_lines, "fetch", lambda data_dir: tmp_path / "stops.parquet")
    monkeypatch.setattr(tfl_lines, "read_stops", lambda path: stops())
    network = Network()
    out = family.columns(context(tmp_path, network))
    assert out == {"night-services": [4]}  # n29, n9, central and windrush
    assert network.asked == [family.BUS_MINUTES, family.RAIL_MINUTES]


def test_a_family_for_one_region_does_not_run_in_another(tmp_path):
    ran = []
    only_london = Family("a", lambda ctx: ran.append("a") or {"one": [1]}, regions=("london",))
    anywhere = Family("b", lambda ctx: ran.append("b") or {"two": [2]})
    region = load_catalogue(CATALOGUE_DIR).regions["london"]
    ctx = Context("manchester", region, [CELL], tmp_path, pd.DataFrame(), None)  # type: ignore[arg-type]
    columns, _ = run([only_london, anywhere], ctx)
    assert list(columns) == ["two"] and ran == ["b"]
    ctx = Context("london", region, [CELL], tmp_path, pd.DataFrame(), None)  # type: ignore[arg-type]
    columns, _ = run([only_london, anywhere], ctx)
    assert list(columns) == ["one", "two"]


def test_the_family_is_for_london_only_and_is_in_the_catalogue():
    found = {f.name: f for f in discover()}
    assert found["night_services"].regions == ("london",)
    ids = {n.id for n in _leaves(load_catalogue(CATALOGUE_DIR).factors.factors)}
    assert "night-services" in ids


def _leaves(nodes):
    for node in nodes:
        if node.children is None:
            yield node
        else:
            yield from _leaves(node.children)


TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)

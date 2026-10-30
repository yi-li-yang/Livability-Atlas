import geopandas as gpd
import h3
import pandas as pd
import pytest
from shapely.geometry import box

from atlas.catalogue.load import load_catalogue
from atlas.datasets.countries.gb import planning_data
from atlas.families import Context, discover
from atlas.families import nature as family
from atlas.indicators.coverage import share_inside
from atlas.paths import CATALOGUE_DIR

CELL = h3.latlng_to_cell(51.5136, -0.1337, 9)
LAT, LNG = h3.cell_to_latlng(CELL)


def test_a_buffer_widens_the_area_that_is_measured():
    from pyproj import Transformer

    x, y = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True).transform(LNG, LAT)
    north = box(x - 2000, y + 300, x + 2000, y + 5000)  # a site 300 m north of the centre
    plain = share_inside([north], [CELL])[CELL]
    wide = share_inside([north], [CELL], buffer=800)[CELL]
    assert plain < wide < 100  # the cell itself is mostly clear of it, and its surroundings are not


def test_the_family_reads_the_four_kinds_of_site_and_measures_800_m_around(tmp_path, monkeypatch):
    region = load_catalogue(CATALOGUE_DIR).regions["london"]
    ctx = Context("london", region, [CELL], tmp_path, pd.DataFrame(), None)  # type: ignore[arg-type]
    asked = []
    monkeypatch.setattr(
        planning_data,
        "fetch",
        lambda data_dir, dataset: asked.append(dataset) or tmp_path / dataset,
    )
    around = box(-2.0, 50.0, 2.0, 52.0)  # covers the cell, in degrees
    monkeypatch.setattr(
        planning_data,
        "read_areas",
        lambda path, box_: gpd.GeoDataFrame(
            {"geometry": [around]}, geometry="geometry", crs="EPSG:4326"
        ),
    )
    out = family.columns(ctx)
    assert out["nature-sites"] == [pytest.approx(100.0)]
    assert asked == family.DATASETS


def test_no_site_in_reach_gives_0(tmp_path, monkeypatch):
    region = load_catalogue(CATALOGUE_DIR).regions["london"]
    ctx = Context("london", region, [CELL], tmp_path, pd.DataFrame(), None)  # type: ignore[arg-type]
    monkeypatch.setattr(planning_data, "fetch", lambda data_dir, dataset: tmp_path / dataset)
    monkeypatch.setattr(
        planning_data,
        "read_areas",
        lambda path, box_: gpd.GeoDataFrame({"geometry": []}, geometry="geometry", crs="EPSG:4326"),
    )
    assert family.columns(ctx) == {"nature-sites": [0.0]}


def test_the_family_is_found_and_its_indicator_is_in_the_catalogue():
    assert "nature" in {f.name for f in discover()}
    ids = {n.id for n in _leaves(load_catalogue(CATALOGUE_DIR).factors.factors)}
    assert "nature-sites" in ids


def _leaves(nodes):
    for node in nodes:
        if node.children is None:
            yield node
        else:
            yield from _leaves(node.children)

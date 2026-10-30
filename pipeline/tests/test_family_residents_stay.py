import geopandas as gpd
import h3
import pandas as pd
import pytest
from pyproj import Transformer
from shapely.geometry import Polygon
from shapely.ops import transform

from atlas.catalogue.load import load_catalogue
from atlas.datasets.countries.gb import census_migrant
from atlas.families import Context, discover
from atlas.families import residents_stay as family
from atlas.paths import CATALOGUE_DIR

CELL = h3.latlng_to_cell(51.5136, -0.1337, 9)
TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True).transform


def write_table(tmp_path, rows: list[str]):
    import zipfile

    header = (
        "date,geography,geography code,"
        "Migrant indicator: Total: All usual residents; measures: Value,"
        "Migrant indicator: Address one year ago is the same as the address of enumeration; "
        "measures: Value,"
        "Migrant indicator: Address one year ago is student term-time or boarding school address "
        "in the UK; measures: Value"
    )
    path = tmp_path / "ts019.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("census2021-ts019-oa.csv", header + "\n" + "\n".join(rows) + "\n")
    return path


def test_the_counts_are_the_residents_and_those_at_the_same_address_a_year_before(tmp_path):
    path = write_table(tmp_path, ["2021,E1,E1,271,253,0", "2021,E2,E2,100,60,5"])
    counts = census_migrant.read_counts(path)
    assert list(counts.columns) == ["residents", "same_address"]
    assert counts.loc["E1"].tolist() == [271, 253] and counts.index.name == "OA21CD"


def test_the_table_is_fetched_once_to_the_census_folder(tmp_path, monkeypatch):
    asked = []
    monkeypatch.setattr(census_migrant, "download", lambda url, target: asked.append(url))
    path = census_migrant.fetch(tmp_path)
    assert path == tmp_path / "raw" / "census" / "census2021-ts019.zip"
    assert asked[0].endswith("census2021-ts019.zip")


def test_a_cell_takes_the_share_of_its_residents_who_were_at_the_same_address(
    tmp_path, monkeypatch
):
    outline = transform(TO_BNG, Polygon([(lng, lat) for lat, lng in h3.cell_to_boundary(CELL)]))
    areas = gpd.GeoDataFrame({"OA21CD": ["o1"]}, geometry=[outline], crs="EPSG:27700")
    monkeypatch.setattr(census_migrant, "fetch", lambda data_dir: tmp_path / "x.zip")
    monkeypatch.setattr(
        census_migrant,
        "read_counts",
        lambda path: pd.DataFrame({"residents": [200.0], "same_address": [150.0]}, index=["o1"]),
    )
    region = load_catalogue(CATALOGUE_DIR).regions["london"]
    ctx = Context("london", region, [CELL], tmp_path, pd.DataFrame(), None)  # type: ignore[arg-type]
    ctx.__dict__["areas"] = areas  # stands in for the cached property
    out = family.columns(ctx)
    assert out["residents-stay"] == [pytest.approx(75.0)]


def test_a_cell_with_no_residents_has_no_value(tmp_path, monkeypatch):
    outline = transform(TO_BNG, Polygon([(lng, lat) for lat, lng in h3.cell_to_boundary(CELL)]))
    areas = gpd.GeoDataFrame({"OA21CD": ["o1"]}, geometry=[outline], crs="EPSG:27700")
    monkeypatch.setattr(census_migrant, "fetch", lambda data_dir: tmp_path / "x.zip")
    monkeypatch.setattr(
        census_migrant,
        "read_counts",
        lambda path: pd.DataFrame({"residents": [0.0], "same_address": [0.0]}, index=["o1"]),
    )
    region = load_catalogue(CATALOGUE_DIR).regions["london"]
    ctx = Context("london", region, [CELL], tmp_path, pd.DataFrame(), None)  # type: ignore[arg-type]
    ctx.__dict__["areas"] = areas
    assert family.columns(ctx) == {"residents-stay": [None]}


def test_the_family_is_found_and_its_indicator_is_in_the_catalogue():
    assert "residents_stay" in {f.name for f in discover()}
    ids = {n.id for n in _leaves(load_catalogue(CATALOGUE_DIR).factors.factors)}
    assert "residents-stay" in ids


def _leaves(nodes):
    for node in nodes:
        if node.children is None:
            yield node
        else:
            yield from _leaves(node.children)

import gzip

import h3
import numpy as np
import pandas as pd
import pytest
from pyproj import Transformer

from atlas.catalogue.load import load_catalogue
from atlas.datasets.countries.gb import dfe_ks4, gias
from atlas.families import Context, discover
from atlas.families import school_results as family
from atlas.paths import CATALOGUE_DIR

CELL = h3.latlng_to_cell(51.5136, -0.1337, 9)
HEADER = "time_period,version,school_urn,breakdown,pupil_count,attainment8_average"


def write(tmp_path, rows: list[str]):
    path = tmp_path / "ks4.csv.gz"
    with gzip.open(path, "wt", encoding="utf-8") as file:
        file.write(HEADER + "\n" + "\n".join(rows) + "\n")
    return path


def test_the_results_are_the_latest_final_year_of_the_total_of_each_school(tmp_path):
    path = write(
        tmp_path,
        [
            "202425,Final,100001,Total,200,50.5",
            "202425,Final,100001,Boys,100,48.0",  # a breakdown, not the school's total
            "202324,Final,100001,Total,210,40.0",  # an earlier year
            "202526,Provisional,100001,Total,205,55.0",  # not final yet
            "202425,Final,100002,Total,150,z",  # the DfE gives no score
            "202425,Final,100003,Total,c,45.0",  # no pupil count: the school is kept, with none
        ],
    )
    found = dfe_ks4.read_attainment(path)
    assert found.loc[100001, "attainment8"] == pytest.approx(50.5)
    assert found.loc[100001, "pupils"] == 200
    assert 100002 not in found.index
    assert np.isnan(found.loc[100003, "pupils"])


def test_the_results_are_read_whether_or_not_the_download_left_the_file_compressed(tmp_path):
    rows = ["202425,Final,100001,Total,200,50.5"]
    plain = tmp_path / "plain.csv.gz"  # the HTTP library unpacks what the API compresses
    plain.write_text("\n".join([HEADER, *rows]) + "\n", encoding="utf-8")
    packed = write(tmp_path, rows)
    assert dfe_ks4.read_attainment(plain).loc[100001, "attainment8"] == pytest.approx(50.5)
    assert dfe_ks4.read_attainment(packed).loc[100001, "attainment8"] == pytest.approx(50.5)


def test_the_file_is_fetched_once_and_kept_as_the_api_sends_it(tmp_path, monkeypatch):
    asked = []
    monkeypatch.setattr(dfe_ks4, "download", lambda url, target: asked.append(url))
    path = dfe_ks4.fetch(tmp_path)
    assert path == tmp_path / "raw" / "dfe" / "ks4-schools.csv.gz"
    assert asked[0].endswith("/csv") and dfe_ks4.DATA_SET in asked[0]


def context(tmp_path) -> Context:
    region = load_catalogue(CATALOGUE_DIR).regions["london"]
    return Context("london", region, [CELL], tmp_path, pd.DataFrame(), None)  # type: ignore[arg-type]


def schools(urns, secondary) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "URN": urns,
            "Easting": [530000.0] * len(urns),
            "Northing": [180000.0] * len(urns),
            "primary": [not s for s in secondary],
            "secondary": secondary,
        }
    )


def attainment(rows) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["URN", "attainment8", "pupils"]).set_index("URN")


def patch(monkeypatch, tmp_path, register, results):
    monkeypatch.setattr(gias, "fetch", lambda data_dir: tmp_path / "g.csv")
    monkeypatch.setattr(gias, "read_schools", lambda path: register)
    monkeypatch.setattr(dfe_ks4, "fetch", lambda data_dir: tmp_path / "k.gz")
    monkeypatch.setattr(dfe_ks4, "read_attainment", lambda path: results)


def test_a_cell_takes_the_pupil_weighted_mean_of_the_secondary_schools_in_reach(
    tmp_path, monkeypatch
):
    patch(
        monkeypatch,
        tmp_path,
        schools([1, 2, 3, 4], [True, True, True, False]),
        attainment([(1, 60.0, 300.0), (2, 40.0, 100.0), (3, 50.0, 100.0), (4, 99.0, 100.0)]),
    )
    ctx = context(tmp_path)
    out = family.columns(ctx)
    assert out["school-league-tables"] == [pytest.approx((60 * 300 + 40 * 100 + 50 * 100) / 500)]


def test_a_cell_with_fewer_than_three_schools_with_results_has_no_value(tmp_path, monkeypatch):
    patch(
        monkeypatch,
        tmp_path,
        schools([1, 2, 3], [True, True, True]),
        attainment([(1, 60.0, 300.0), (2, 40.0, 100.0)]),  # the third has no results
    )
    assert family.columns(context(tmp_path)) == {"school-league-tables": [None]}


def test_a_school_beyond_3_km_is_out_of_reach(tmp_path, monkeypatch):
    register = schools([1, 2, 3, 4], [True] * 4)
    register.loc[3, "Easting"] += 20000.0  # far away
    patch(
        monkeypatch,
        tmp_path,
        register,
        attainment([(1, 60.0, 100.0), (2, 50.0, 100.0), (3, 40.0, 100.0), (4, 99.0, 100.0)]),
    )
    # the far school (4) is left out, so the three near ones give (60 + 50 + 40) / 3
    assert family.columns(context(tmp_path))["school-league-tables"] == [pytest.approx(50.0)]


def test_a_school_with_no_pupil_count_counts_as_the_mean_of_the_others(tmp_path, monkeypatch):
    patch(
        monkeypatch,
        tmp_path,
        schools([1, 2, 3], [True, True, True]),
        attainment([(1, 60.0, 100.0), (2, 40.0, 100.0), (3, 50.0, float("nan"))]),
    )
    assert family.columns(context(tmp_path))["school-league-tables"] == [pytest.approx(50.0)]


def test_the_family_is_found_and_its_indicator_is_in_the_catalogue():
    assert "school_results" in {f.name for f in discover()}
    ids = {n.id for n in _leaves(load_catalogue(CATALOGUE_DIR).factors.factors)}
    assert "school-league-tables" in ids


def _leaves(nodes):
    for node in nodes:
        if node.children is None:
            yield node
        else:
            yield from _leaves(node.children)


TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)

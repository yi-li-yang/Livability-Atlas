import json

import pytest

from atlas.datasets.countries.gb import bres, ons_lsoa


def test_jobs_are_read_from_every_page_and_indexed_by_area_code(tmp_path):
    first, second = tmp_path / "one.csv", tmp_path / "two.csv"
    first.write_text(
        '"GEOGRAPHY_CODE","OBS_VALUE"\n"E01000001",1500\n"E01000002",\n', encoding="utf-8"
    )
    second.write_text('"GEOGRAPHY_CODE","OBS_VALUE"\n"E01000003",75\n', encoding="utf-8")
    jobs = bres.read_jobs([first, second])
    assert jobs.to_dict() == {"E01000001": 1500.0, "E01000003": 75.0}  # a suppressed area is out
    assert jobs.index.name == "LSOA11CD"


def test_the_table_is_fetched_in_pages_of_the_anonymous_limit(tmp_path, monkeypatch):
    asked = []
    monkeypatch.setattr(bres, "download", lambda url, target: asked.append((url, target.name)))
    files = bres.fetch(tmp_path)
    assert [u.rsplit("recordoffset=", 1)[1] for u, _ in asked] == ["0", "25000"]
    assert [f.name for f in files] == ["bres-jobs-lsoa-2024-1.csv", "bres-jobs-lsoa-2024-2.csv"]
    assert "date=2024" in asked[0][0] and "TYPE151" in asked[0][0]


def test_lsoas_are_read_in_british_national_grid(tmp_path):
    path = tmp_path / "lsoa.geojson"
    square = [
        [[530000, 180000], [530100, 180000], [530100, 180100], [530000, 180100], [530000, 180000]]
    ]
    feature = {
        "type": "Feature",
        "properties": {"LSOA11CD": "E01000001", "other": 1},
        "geometry": {"type": "Polygon", "coordinates": square},
    }
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": [feature]}), encoding="utf-8"
    )
    areas = ons_lsoa.read_boundaries(path)
    assert list(areas.columns) == ["LSOA11CD", "geometry"]
    assert areas.crs is not None and areas.crs.to_epsg() == 27700
    assert areas.geometry.iloc[0].area == pytest.approx(10_000)

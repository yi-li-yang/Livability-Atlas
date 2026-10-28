import json
import zipfile
from pathlib import Path

import h3
import pyarrow.parquet as pq
from openpyxl import Workbook
from pyproj import Transformer
from shapely.geometry import box
from typer.testing import CliRunner

from atlas import build as build_module
from atlas.build import build_region
from atlas.cli import app
from atlas.datasets.cities.london import ptal
from atlas.datasets.countries.gb import ons_regions

TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
AREA = box(-0.150, 51.505, -0.125, 51.520)  # part of the West End


def synthetic_boundary(tmp_path: Path) -> Path:
    path = tmp_path / "London.geojson"
    feature = {
        "type": "Feature",
        "properties": {ons_regions.NAME_FIELD: "London"},
        "geometry": AREA.__geo_interface__,
    }
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": [feature]}), encoding="utf-8"
    )
    return path


def synthetic_grid(tmp_path: Path) -> Path:
    """A 100 m grid over AREA: band 3 in the west, band 5 in the east."""
    x0, y0 = TO_BNG.transform(AREA.bounds[0], AREA.bounds[1])
    x1, y1 = TO_BNG.transform(AREA.bounds[2], AREA.bounds[3])
    workbook = Workbook()
    sheet = workbook.create_sheet("Query1")
    sheet.append(["ID", "X", "Y", "AI2015", "PTAL2015"])
    number = 0
    x = x0 - 200
    while x < x1 + 200:
        y = y0 - 200
        while y < y1 + 200:
            number += 1
            sheet.append([number, round(x), round(y), 10, 3 if x < (x0 + x1) / 2 else 5])
            y += 100
        x += 100
    path = tmp_path / "grid.xlsx"
    workbook.save(path)
    return path


def use_synthetic_data(monkeypatch, tmp_path):
    boundary, grid = synthetic_boundary(tmp_path), synthetic_grid(tmp_path)
    monkeypatch.setattr(build_module.ons_regions, "fetch", lambda name, data_dir: boundary)
    monkeypatch.setattr(build_module.ptal, "fetch", lambda data_dir: grid)


def test_a_region_is_built_into_a_bundle(monkeypatch, tmp_path):
    use_synthetic_data(monkeypatch, tmp_path)
    bundle = build_region("london", data_dir=tmp_path / "data")
    assert bundle.parent.parent == tmp_path / "data" / "published"
    table = pq.read_table(bundle / "cells.parquet")
    cells = table["cell"].to_pylist()
    assert 20 <= len(cells) <= 60 and cells == sorted(cells)
    assert {h3.get_resolution(c) for c in cells} == {9}
    bands = set(table["service_level"].to_pylist())
    assert bands == {"3", "5"}


def test_building_twice_gives_the_same_bundle(monkeypatch, tmp_path):
    use_synthetic_data(monkeypatch, tmp_path)
    first = build_region("london", data_dir=tmp_path / "one")
    second = build_region("london", data_dir=tmp_path / "two")
    assert first.name == second.name
    assert (first / "cells.parquet").read_bytes() == (second / "cells.parquet").read_bytes()
    assert (first / "manifest.json").read_bytes() == (second / "manifest.json").read_bytes()


def test_a_cell_without_a_grid_point_has_no_value(monkeypatch, tmp_path):
    """Outside TfL's grid there is no PTAL: that is missing, and not band 0."""
    use_synthetic_data(monkeypatch, tmp_path)
    wide = box(-0.30, 51.40, 0.0, 51.60)
    boundary = tmp_path / "London.geojson"
    feature = {
        "type": "Feature",
        "properties": {ons_regions.NAME_FIELD: "London"},
        "geometry": wide.__geo_interface__,
    }
    boundary.write_text(
        json.dumps({"type": "FeatureCollection", "features": [feature]}), encoding="utf-8"
    )
    bundle = build_region("london", data_dir=tmp_path / "data")
    values = pq.read_table(bundle / "cells.parquet")["service_level"].to_pylist()
    assert None in values and "3" in values and "0" not in values


def test_the_command_builds_a_region_and_says_where(monkeypatch, tmp_path):
    use_synthetic_data(monkeypatch, tmp_path)
    result = CliRunner().invoke(app, ["build", "london", "--data-dir", str(tmp_path / "data")])
    assert result.exit_code == 0, result.output
    assert "cells" in result.output and "published" in result.output


def test_a_region_the_catalogue_does_not_have_is_an_error(tmp_path):
    result = CliRunner().invoke(app, ["build", "atlantis", "--data-dir", str(tmp_path)])
    assert result.exit_code == 1
    assert "atlantis" in result.output


def test_the_boundary_query_asks_for_one_region_in_longitude_and_latitude():
    url = ons_regions.url("London")
    assert "outSR=4326" in url and "f=geojson" in url
    assert "RGN25NM%3D%27London%27" in url
    assert "%27%27" in ons_regions.url("St. John's")  # a quote in a name is doubled


def test_the_ptal_release_is_unzipped_after_it_is_fetched(monkeypatch, tmp_path):
    source = tmp_path / "release.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("2015  PTALs Grid Values 280515.xlsx", b"workbook")
        archive.writestr("2015  PTALs Contours 280515.MAP", b"map")

    def fake_download(url, target):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        return "digest"

    monkeypatch.setattr(ptal, "download", fake_download)
    path = ptal.fetch(tmp_path)
    assert path.name == "2015  PTALs Grid Values 280515.xlsx" and path.read_bytes() == b"workbook"

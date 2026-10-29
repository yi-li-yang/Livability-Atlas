import datetime
import json
import zipfile
from pathlib import Path

import h3
import numpy as np
import pandas as pd
import pytest
from openpyxl import Workbook

from atlas.datasets.countries.gb import mhclg_council_tax, ons_local_authorities, ons_rents
from atlas.indicators import housing

ODS_NS = (
    'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
    'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
    'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"'
)


def ods_cell(value) -> str:
    if value is None:
        return "<table:table-cell/>"
    if isinstance(value, (int, float)):
        shown = f"{value:,.2f}"
        return (
            f'<table:table-cell office:value-type="float" office:value="{value}">'
            f"<text:p>{shown}</text:p></table:table-cell>"
        )
    return (
        f'<table:table-cell office:value-type="string"><text:p>{value}</text:p></table:table-cell>'
    )


def council_tax_file(tmp_path: Path, rows: list[list]) -> Path:
    """A workbook in the layout of MHCLG's Tables 1 to 9: a sheet `Table_9` with a title, a note,
    a header row and one row for each authority."""
    sheet = [["Table 9: Area council tax"], ["This worksheet contains 1 table."], *rows]
    body = "".join(
        "<table:table-row>" + "".join(ods_cell(v) for v in row) + "</table:table-row>"
        for row in sheet
    )
    other = "<table:table-row><table:table-cell/></table:table-row>"
    content = (
        f'<?xml version="1.0" encoding="UTF-8"?><office:document-content {ODS_NS}>'
        f"<office:body><office:spreadsheet>"
        f'<table:table table:name="Table_8a">{other}</table:table>'
        f'<table:table table:name="Table_9">{body}</table:table>'
        f"</office:spreadsheet></office:body></office:document-content>"
    )
    path = tmp_path / "tables.ods"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("content.xml", content)
    return path


HEADER = [
    "E Code",
    "ONS Code",
    "Authority",
    "Region",
    "Class",
    "Area",
    "Band A",
    "Band B",
    "Band C",
    "Band D",
]


class TestCouncilTax:
    def test_reads_the_band_d_of_each_authority_by_its_ons_code(self, tmp_path):
        path = council_tax_file(
            tmp_path,
            [
                HEADER,
                [
                    "E5011",
                    "E09000007",
                    "Camden",
                    "L",
                    "ILB",
                    "Inner London",
                    1471.7,
                    1716.98,
                    1962.27,
                    2207.55,
                ],
                [
                    "E5010",
                    "E09000001",
                    "City of London",
                    "L",
                    "ILB",
                    "Inner London",
                    886.37,
                    1034.1,
                    1181.83,
                    1329.56,
                ],
                ["E6348a", "[z]", "A police function", "NW", "PCC", "x", 1.0, 2.0, 3.0, 4.0],
            ],
        )
        assert mhclg_council_tax.read_band_d(path) == {"E09000007": 2207.55, "E09000001": 1329.56}

    def test_a_workbook_without_the_table_is_an_error(self, tmp_path):
        path = tmp_path / "x.ods"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(
                "content.xml",
                f"<office:document-content {ODS_NS}><office:body/></office:document-content>",
            )
        with pytest.raises(KeyError, match="Table_9"):
            mhclg_council_tax.read_band_d(path)

    def test_the_file_is_fetched_once(self, tmp_path, monkeypatch):
        asked = []
        monkeypatch.setattr(
            mhclg_council_tax, "download", lambda url, target: asked.append(target.name)
        )
        assert mhclg_council_tax.fetch(tmp_path).name == "Tables_1-9_2026-27.ods"
        assert asked == ["Tables_1-9_2026-27.ods"]


def rents_file(tmp_path: Path, rows: list[tuple]) -> Path:
    """A workbook in the layout of the ONS's price index of private rents: a sheet `Table 1`
    with two lines of text, a header row, and rows of time period, area code, area name, region,
    index, monthly change, annual change and rental price."""
    book = Workbook()
    cover = book.active
    assert cover is not None
    cover.title = "Cover sheet"
    sheet = book.create_sheet("Table 1")
    sheet.append(["Price Index of Private Rents"])
    sheet.append(["This worksheet contains one table."])
    sheet.append(
        [
            "Time period",
            "Area code",
            "Area name",
            "Region or country name",
            "Index",
            "Monthly change",
            "Annual change",
            "Rental price",
        ]
    )
    for row in rows:
        sheet.append(list(row))
    path = tmp_path / "pipr.xlsx"
    book.save(path)
    return path


class TestRents:
    def test_reads_the_latest_months_rent_of_each_area(self, tmp_path):
        d = datetime.datetime
        path = rents_file(
            tmp_path,
            [
                (d(2026, 8, 1), "E09000002", "Barking and Dagenham", "London", 100, 1, 2, 1690),
                (d(2026, 9, 1), "E09000002", "Barking and Dagenham", "London", 101, 1, 2, 1700),
                (d(2026, 9, 1), "E09000007", "Camden", "London", 100, 1, 2, 2900),
                (d(2026, 9, 1), "K02000001", "United Kingdom", "[z]", 100, "[x]", "[x]", 1400),
            ],
        )
        rents = ons_rents.read_rents(path)
        assert rents == {"E09000002": 1700.0, "E09000007": 2900.0, "K02000001": 1400.0}

    def test_an_area_whose_latest_month_has_no_price_takes_its_last_price(self, tmp_path):
        d = datetime.datetime
        path = rents_file(
            tmp_path,
            [
                (d(2026, 8, 1), "E09000001", "City of London", "London", 100, 1, 2, 2500),
                (d(2026, 9, 1), "E09000001", "City of London", "London", 100, 1, 2, "[x]"),
            ],
        )
        assert ons_rents.read_rents(path) == {"E09000001": 2500.0}

    def test_the_file_is_fetched_once(self, tmp_path, monkeypatch):
        asked = []
        monkeypatch.setattr(
            ons_rents, "download", lambda url, target: asked.append((url, target.name))
        )
        assert ons_rents.fetch(tmp_path).name == "pipr.xlsx"
        assert "priceindexofprivaterents" in asked[0][0]


def square(west, south, east, north):
    return {
        "type": "Polygon",
        "coordinates": [
            [[west, south], [east, south], [east, north], [west, north], [west, south]]
        ],
    }


def boroughs_file(tmp_path: Path) -> Path:
    features = [
        {
            "type": "Feature",
            "properties": {"LAD25CD": "E09000007", "LAD25NM": "Camden"},
            "geometry": square(-0.20, 51.50, -0.12, 51.60),
        },
        {
            "type": "Feature",
            "properties": {"LAD25CD": "E09000033", "LAD25NM": "Westminster"},
            "geometry": square(-0.12, 51.50, -0.05, 51.60),
        },
    ]
    path = tmp_path / "london.geojson"
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}), encoding="utf-8"
    )
    return path


class TestBoroughs:
    def test_each_cell_belongs_to_the_borough_that_holds_its_centre(self, tmp_path):
        west = h3.latlng_to_cell(51.55, -0.16, 9)
        east = h3.latlng_to_cell(51.55, -0.08, 9)
        outside = h3.latlng_to_cell(51.40, -0.30, 9)
        found = ons_local_authorities.borough_of(boroughs_file(tmp_path), [west, east, outside])
        assert found == {west: "E09000007", east: "E09000033", outside: None}

    def test_the_query_asks_for_the_regions_authorities_in_longitude_and_latitude(self):
        url = ons_local_authorities.url("london")
        assert "LAD25CD" in url and "E09" in url and "outSR=4326" in url and "f=geojson" in url

    def test_the_file_is_fetched_once(self, tmp_path, monkeypatch):
        asked = []
        monkeypatch.setattr(
            ons_local_authorities, "download", lambda url, target: asked.append(target.name)
        )
        assert ons_local_authorities.fetch(tmp_path, "london").name == "london.geojson"
        assert asked == ["london.geojson"]


class TestByBorough:
    def test_a_cell_takes_the_value_of_its_borough(self):
        cells = ["a", "b", "c", "d"]
        owner = {"a": "E09000007", "b": "E09000007", "c": "E09000033", "d": None}
        values = {"E09000007": 2200.0, "E09000033": 2900.0}
        result = housing.by_borough(values, owner, cells)
        assert result["a"] == 2200.0 and result["c"] == 2900.0
        assert np.isnan(result["d"])  # in no borough

    def test_a_borough_without_a_value_gives_no_value(self):
        result = housing.by_borough({}, {"a": "E09000007"}, ["a"])
        assert isinstance(result, pd.Series) and np.isnan(result["a"])

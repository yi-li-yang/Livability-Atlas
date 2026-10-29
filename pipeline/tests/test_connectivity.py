import io
import zipfile
from pathlib import Path

import geopandas as gpd
import h3
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Polygon

from atlas.datasets.countries.gb import ofcom
from atlas.indicators import connectivity

FIXED_HEADER = (
    "output_area,All Premises,All Matched Premises,Gigabit availability (% premises),"
    "Number of premises with Gigabit availability"
)


def fixed_zip(tmp_path: Path, rows: list[str]) -> Path:
    """A file in the layout of Ofcom's fixed broadband download: a zip that holds, among others,
    a zip of the output area tables, which holds a table of residential premises."""
    inner = io.BytesIO()
    folder = "202507_fixed_oa_coverage_r01"
    with zipfile.ZipFile(inner, "w") as archive:
        archive.writestr(
            f"{folder}/202507_fixed_oa_res_coverage_r01.csv",
            "\n".join([FIXED_HEADER, *rows]) + "\n",
        )
        archive.writestr(f"{folder}/202507_fixed_oa_coverage_r01.csv", "not the table we want\n")
    path = tmp_path / "fixed.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "202507_fixed_coverage_r01/202507_fixed_oa_coverage_r01.zip", inner.getvalue()
        )
    return path


def mobile_zip(tmp_path: Path, rows: list[str]) -> Path:
    header = "laua,laua_name,5G_high_confidence_prem_out_3,5G_high_confidence_prem_out_4"
    path = tmp_path / "mobile.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "202507_mobile_coverage_r01/202507_mobile_coverage_laua_r01.csv",
            "\n".join([header, *rows]) + "\n",
        )
    return path


class TestFixed:
    def test_reads_the_homes_and_the_homes_with_gigabit_of_each_output_area(self, tmp_path):
        path = fixed_zip(tmp_path, ["E00000001,119,119,100,119", "E00000003,127,120,25,32"])
        homes = ofcom.read_fixed(path)
        assert homes.loc["E00000001"].tolist() == [119, 119]
        assert homes.loc["E00000003"].tolist() == [127, 32]
        assert list(homes.columns) == ["homes", "gigabit_homes"]

    def test_the_files_are_fetched_once(self, tmp_path, monkeypatch):
        asked = []
        monkeypatch.setattr(ofcom, "download", lambda url, target: asked.append(target.name))
        assert [p.name for p in ofcom.fetch(tmp_path)] == ["fixed.zip", "mobile.zip"]
        assert asked == ["fixed.zip", "mobile.zip"]


class TestMobile:
    def test_reads_the_share_of_premises_with_5g_from_all_four_networks(self, tmp_path):
        path = mobile_zip(tmp_path, ["E09000002,Barking,0.5,99.5", "E09000007,Camden,,"])
        found = ofcom.read_five_g(path)
        assert found["E09000002"] == pytest.approx(99.5)
        assert found["E09000007"] == 0.0  # Ofcom leaves a band with no premises empty


def square(x, y, size=500.0):
    return Polygon([(x, y), (x + size, y), (x + size, y + size), (x, y + size)])


class TestGigabitShare:
    def cells(self):
        soho = h3.latlng_to_cell(51.5136, -0.1337, 9)
        return [soho]

    def areas_over(self, cell: str, codes_and_fractions: list[tuple[str, float]]):
        """Output areas that split the cell by west-east strips of the given fractions."""
        boundary = gpd.GeoSeries(
            [Polygon([(lng, lat) for lat, lng in h3.cell_to_boundary(cell)])], crs="EPSG:4326"
        ).to_crs("EPSG:27700")
        west, south, east, north = boundary.total_bounds
        pieces, start = [], west
        for code, fraction in codes_and_fractions:
            end = start + fraction * (east - west)
            pieces.append(
                (code, Polygon([(start, south), (end, south), (end, north), (start, north)]))
            )
            start = end
        return gpd.GeoDataFrame(
            {"OA21CD": [c for c, _ in pieces]},
            geometry=[g for _, g in pieces],
            crs="EPSG:27700",
        )

    def test_it_is_the_share_of_the_cells_homes_that_can_get_gigabit(self):
        (cell,) = self.cells()
        areas = self.areas_over(cell, [("A", 0.5), ("B", 0.5)])  # two halves of the cell
        homes = pd.DataFrame(
            {"homes": [100.0, 100.0], "gigabit_homes": [100.0, 0.0]}, index=["A", "B"]
        )
        share = connectivity.gigabit_share(areas, homes, [cell])
        assert share[cell] == pytest.approx(50.0, abs=3.0)  # the hexagon's halves are not equal

    def test_an_area_with_more_homes_counts_for_more(self):
        (cell,) = self.cells()
        areas = self.areas_over(cell, [("A", 0.5), ("B", 0.5)])
        homes = pd.DataFrame(
            {"homes": [300.0, 100.0], "gigabit_homes": [300.0, 0.0]}, index=["A", "B"]
        )
        assert connectivity.gigabit_share(areas, homes, [cell])[cell] == pytest.approx(
            75.0, abs=3.0
        )

    def test_a_cell_with_no_homes_has_no_value(self):
        (cell,) = self.cells()
        far = h3.latlng_to_cell(51.40, -0.40, 9)
        areas = self.areas_over(cell, [("A", 1.0)])
        homes = pd.DataFrame({"homes": [100.0], "gigabit_homes": [90.0]}, index=["A"])
        share = connectivity.gigabit_share(areas, homes, [cell, far])
        assert share[cell] == pytest.approx(90.0) and np.isnan(share[far])


def test_a_share_never_goes_above_100_through_rounding(monkeypatch):
    cell = h3.latlng_to_cell(51.5136, -0.1337, 9)
    shared = {"homes": 100.0, "gigabit_homes": 100.00000000000001}  # as overlay areas can give

    def fake(areas, counts, cells):
        return pd.Series(shared[str(counts.name)], index=cells)

    monkeypatch.setattr(connectivity, "residents_by_cell", fake)
    homes = pd.DataFrame({"homes": [1.0], "gigabit_homes": [1.0]}, index=["A"])
    areas = gpd.GeoDataFrame({"OA21CD": ["A"]}, geometry=[square(0, 0)], crs="EPSG:27700")
    assert connectivity.gigabit_share(areas, homes, [cell])[cell] == 100.0

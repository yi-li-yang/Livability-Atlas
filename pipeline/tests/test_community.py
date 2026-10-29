import zipfile
from pathlib import Path

import geopandas as gpd
import h3
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Polygon

from atlas.datasets.countries.gb import census_ethnic_group
from atlas.indicators import community

HEADER = (
    "date,geography,geography code,Ethnic group: Total: All usual residents,"
    '"Ethnic group: Asian, Asian British or Asian Welsh",'
    '"Ethnic group: Asian, Asian British or Asian Welsh: Indian",'
    '"Ethnic group: Asian, Asian British or Asian Welsh: Other Asian",'
    "Ethnic group: White,"
    "Ethnic group: White: Irish,"
    "Ethnic group: White: Other White"
)


def census_zip(tmp_path: Path, rows: list[str]) -> Path:
    path = tmp_path / "census2021-ts021.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("census2021-ts021-oa.csv", "\n".join([HEADER, *rows]) + "\n")
        archive.writestr("census2021-ts021-lsoa.csv", "not the table we want\n")
    return path


class TestEthnicGroups:
    def test_reads_the_detailed_groups_of_each_output_area(self, tmp_path):
        path = census_zip(
            tmp_path,
            [
                "2021,E00000001,E00000001,100,30,20,10,70,5,65",
                "2021,E00000003,E00000003,10,0,0,0,10,10,0",
            ],
        )
        groups = census_ethnic_group.read_groups(path)
        assert groups.index.tolist() == ["E00000001", "E00000003"]
        assert groups.loc["E00000001"].to_dict() == {
            "Asian, Asian British or Asian Welsh: Indian": 20,
            "Asian, Asian British or Asian Welsh: Other Asian": 10,
            "White: Irish": 5,
            "White: Other White": 65,
        }

    def test_the_broad_groups_and_the_total_are_left_out(self, tmp_path):
        path = census_zip(tmp_path, ["2021,E00000001,E00000001,100,30,20,10,70,5,65"])
        names = census_ethnic_group.read_groups(path).columns
        assert "White" not in names and "Total: All usual residents" not in names

    def test_the_file_is_fetched_once(self, tmp_path, monkeypatch):
        asked = []
        monkeypatch.setattr(
            census_ethnic_group, "download", lambda url, target: asked.append(target.name)
        )
        assert census_ethnic_group.fetch(tmp_path).name == "census2021-ts021.zip"
        assert asked == ["census2021-ts021.zip"]


class TestSimpson:
    def test_one_group_alone_has_no_diversity(self):
        assert community.simpson(np.array([[50.0, 0.0, 0.0]]))[0] == pytest.approx(0.0)

    def test_an_even_split_over_n_groups_is_one_minus_one_over_n(self):
        assert community.simpson(np.array([[10.0, 10.0, 10.0, 10.0]]))[0] == pytest.approx(0.75)

    def test_a_place_with_no_residents_has_no_value(self):
        assert np.isnan(community.simpson(np.array([[0.0, 0.0]]))[0])

    def test_the_size_of_the_place_does_not_matter(self):
        small, large = community.simpson(np.array([[3.0, 1.0], [300.0, 100.0]]))
        assert small == pytest.approx(large)


def square_over(cell: str, west_fraction: float, east_fraction: float) -> Polygon:
    boundary = gpd.GeoSeries(
        [Polygon([(lng, lat) for lat, lng in h3.cell_to_boundary(cell)])], crs="EPSG:4326"
    ).to_crs("EPSG:27700")
    west, south, east, north = boundary.total_bounds
    start = west + west_fraction * (east - west)
    end = west + east_fraction * (east - west)
    return Polygon([(start, south), (end, south), (end, north), (start, north)])


class TestDiversity:
    def areas(self, cell: str) -> gpd.GeoDataFrame:
        return gpd.GeoDataFrame(
            {"OA21CD": ["A", "B"]},
            geometry=[square_over(cell, 0.0, 0.5), square_over(cell, 0.5, 1.0)],
            crs="EPSG:27700",
        )

    def test_a_cell_mixes_the_groups_of_the_output_areas_that_it_overlaps(self):
        cell = h3.latlng_to_cell(51.5136, -0.1337, 9)
        groups = pd.DataFrame({"one": [100.0, 0.0], "two": [0.0, 100.0]}, index=["A", "B"])
        index = community.diversity(self.areas(cell), groups, [cell])
        assert index[cell] == pytest.approx(0.5, abs=0.05)  # the hexagon's halves are not equal

    def test_a_cell_in_one_output_area_has_that_areas_index(self):
        cell = h3.latlng_to_cell(51.5136, -0.1337, 9)
        groups = pd.DataFrame({"one": [10.0, 10.0], "two": [10.0, 10.0]}, index=["A", "B"])
        assert community.diversity(self.areas(cell), groups, [cell])[cell] == pytest.approx(0.5)

    def test_a_cell_with_no_residents_has_no_value(self):
        cell = h3.latlng_to_cell(51.5136, -0.1337, 9)
        far = h3.latlng_to_cell(51.40, -0.40, 9)
        groups = pd.DataFrame({"one": [5.0, 5.0], "two": [5.0, 5.0]}, index=["A", "B"])
        index = community.diversity(self.areas(cell), groups, [cell, far])
        assert np.isnan(index[far])

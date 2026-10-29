import zipfile
from pathlib import Path

import geopandas as gpd
import h3
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Polygon

from atlas.datasets.countries.gb import (
    census_age,
    census_country_of_birth,
    census_ethnic_group,
    census_religion,
)
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


RELIGION_HEADER = (
    "date,geography,geography code,Religion: Total: All usual residents,Religion: No religion,"
    "Religion: Christian,Religion: Hindu,Religion: Not answered"
)


def religion_zip(tmp_path: Path, rows: list[str]) -> Path:
    path = tmp_path / "census2021-ts030.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("census2021-ts030-oa.csv", "\n".join([RELIGION_HEADER, *rows]) + "\n")
    return path


class TestReligion:
    def test_reads_the_residents_of_each_religion_in_each_output_area(self, tmp_path):
        path = religion_zip(tmp_path, ["2021,E00000001,E00000001,100,40,50,8,2"])
        groups = census_religion.read_groups(path)
        assert groups.loc["E00000001"].to_dict() == {
            "No religion": 40,
            "Christian": 50,
            "Hindu": 8,
            "Not answered": 2,
        }

    def test_the_file_is_fetched_once(self, tmp_path, monkeypatch):
        asked = []
        monkeypatch.setattr(census_religion, "download", lambda url, target: asked.append(1))
        assert census_religion.fetch(tmp_path).name == "census2021-ts030.zip"
        assert asked == [1]


class TestShares:
    def test_it_is_the_percentage_of_a_cells_residents_in_each_group(self):
        cell = h3.latlng_to_cell(51.5136, -0.1337, 9)
        areas = TestDiversity().areas(cell)
        groups = pd.DataFrame({"one": [30.0, 30.0], "two": [10.0, 10.0]}, index=["A", "B"])
        shares = community.shares(areas, groups, [cell])
        assert shares.loc[cell, "one"] == pytest.approx(75.0)
        assert shares.loc[cell, "two"] == pytest.approx(25.0)

    def test_a_cell_with_no_residents_has_no_shares(self):
        cell = h3.latlng_to_cell(51.5136, -0.1337, 9)
        far = h3.latlng_to_cell(51.40, -0.40, 9)
        areas = TestDiversity().areas(cell)
        groups = pd.DataFrame({"one": [1.0, 1.0], "two": [1.0, 1.0]}, index=["A", "B"])
        shares = community.shares(areas, groups, [cell, far])
        assert shares.loc[far].isna().all()

    def test_a_group_is_a_share_of_everyone_not_of_the_listed_options(self):
        cell = h3.latlng_to_cell(51.5136, -0.1337, 9)
        areas = TestDiversity().areas(cell)
        groups = pd.DataFrame({"one": [20.0, 20.0], "other": [80.0, 80.0]}, index=["A", "B"])
        assert community.shares(areas, groups, [cell]).loc[cell, "one"] == pytest.approx(20.0)


class TestCommunityOptions:
    def frames(self):
        cells = ["a", "b"]
        ethnic = pd.DataFrame(
            {
                "Asian, Asian British or Asian Welsh: Indian": [10.0, 20.0],
                "White: Irish": [1.0, 2.0],
            },
            index=cells,
        )
        religion = pd.DataFrame(
            {
                "Hindu": [5.0, 6.0],
                "No religion": [30.0, 40.0],
                "Not answered": [7.0, 8.0],
                "Other religion": [1.0, 1.0],
            },
            index=cells,
        )
        return ethnic, religion

    def test_each_group_is_an_option_under_its_census_table(self):
        options = community.community_options(*self.frames())
        assert [(o[0], o[1], o[2]) for o in options] == [
            ("ethnic-indian", "Indian", "Ethnic group"),
            ("ethnic-irish", "Irish", "Ethnic group"),
            ("religion-hindu", "Hindu", "Religion"),
            ("religion-no-religion", "No religion", "Religion"),
        ]

    def test_those_who_did_not_answer_and_other_religions_are_not_offered(self):
        ids = [o[0] for o in community.community_options(*self.frames())]
        assert "religion-not-answered" not in ids and "religion-other-religion" not in ids

    def test_an_option_carries_the_share_of_each_cell(self):
        options = community.community_options(*self.frames())
        assert options[0][3].tolist() == [10.0, 20.0]


BIRTH_HEADER = (
    "date,geography,geography code,Country of birth: Total; measures: Value,"
    "Country of birth: Europe; measures: Value,"
    "Country of birth: Europe: United Kingdom; measures: Value,"
    "Country of birth: Europe: EU countries; measures: Value,"
    "Country of birth: Europe: EU countries: European Union EU8; measures: Value,"
    "Country of birth: Europe: EU countries: All other EU countries; measures: Value,"
    "Country of birth: Africa; measures: Value,"
    "Country of birth: British Overseas ; measures: Value"
)
AGE_HEADER = (
    "date,geography,geography code,Age: Total,Age: Aged 4 years and under,"
    "Age: Aged 5 to 9 years,Age: Aged 10 to 14 years,Age: Aged 15 to 19 years,"
    "Age: Aged 20 to 24 years,Age: Aged 25 to 29 years,Age: Aged 30 to 34 years,"
    "Age: Aged 35 to 39 years,Age: Aged 40 to 44 years,Age: Aged 45 to 49 years,"
    "Age: Aged 50 to 54 years,Age: Aged 55 to 59 years,Age: Aged 60 to 64 years,"
    "Age: Aged 65 to 69 years,Age: Aged 70 to 74 years,Age: Aged 75 to 79 years,"
    "Age: Aged 80 to 84 years,Age: Aged 85 years and over"
)


def one_table_zip(tmp_path: Path, name: str, header: str, rows: list[str]) -> Path:
    path = tmp_path / f"{name}.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(f"{name}-oa.csv", "\n".join([header, *rows]) + "\n")
    return path


class TestCountryOfBirth:
    def test_it_reads_the_places_of_birth_that_nothing_is_split_from(self, tmp_path):
        path = one_table_zip(
            tmp_path, "census2021-ts004", BIRTH_HEADER, ["2021,E1,E1,100,70,50,20,12,8,25,5"]
        )
        groups = census_country_of_birth.read_groups(path)
        assert groups.loc["E1"].to_dict() == {
            "United Kingdom": 50,
            "European Union EU8": 12,
            "All other EU countries": 8,
            "Africa": 25,
            "British Overseas": 5,
        }  # Europe and the EU countries only add up what is under them, and so does the total

    def test_the_file_is_fetched_once(self, tmp_path, monkeypatch):
        asked = []
        monkeypatch.setattr(
            census_country_of_birth, "download", lambda url, target: asked.append(1)
        )
        assert census_country_of_birth.fetch(tmp_path).name == "census2021-ts004.zip"
        assert asked == [1]


class TestAge:
    def test_it_reads_the_residents_of_each_five_year_band(self, tmp_path):
        row = "2021,E1,E1,190," + ",".join(str(n) for n in range(1, 19))
        path = one_table_zip(tmp_path, "census2021-ts007a", AGE_HEADER, [row])
        bands = census_age.read_groups(path)
        assert bands.shape == (1, 18)
        assert bands.loc["E1", "Aged 4 years and under"] == 1
        assert bands.loc["E1", "Aged 85 years and over"] == 18

    def test_the_file_is_fetched_once(self, tmp_path, monkeypatch):
        asked = []
        monkeypatch.setattr(census_age, "download", lambda url, target: asked.append(1))
        assert census_age.fetch(tmp_path).name == "census2021-ts007a.zip"
        assert asked == [1]


class TestLifeStages:
    def test_the_bands_are_added_into_six_life_stages_that_cover_everyone(self):
        names = [
            "Aged 4 years and under", "Aged 5 to 9 years", "Aged 10 to 14 years",
            "Aged 15 to 19 years", "Aged 20 to 24 years", "Aged 25 to 29 years",
            "Aged 30 to 34 years", "Aged 35 to 39 years", "Aged 40 to 44 years",
            "Aged 45 to 49 years", "Aged 50 to 54 years", "Aged 55 to 59 years",
            "Aged 60 to 64 years", "Aged 65 to 69 years", "Aged 70 to 74 years",
            "Aged 75 to 79 years", "Aged 80 to 84 years", "Aged 85 years and over",
        ]  # fmt: skip
        bands = pd.DataFrame([np.arange(1, 19)], columns=names, index=["E1"])
        stages = community.life_stages(bands)
        assert stages.loc["E1"].to_dict() == {
            "Children under 15": 1 + 2 + 3,
            "Aged 15 to 24": 4 + 5,
            "Aged 25 to 34": 6 + 7,
            "Aged 35 to 49": 8 + 9 + 10,
            "Aged 50 to 64": 11 + 12 + 13,
            "Aged 65 and over": 14 + 15 + 16 + 17 + 18,
        }
        assert stages.loc["E1"].sum() == bands.loc["E1"].sum()


class TestMoreOptions:
    def test_birth_and_age_join_the_options_under_their_own_titles(self):
        cells = ["a", "b"]
        ethnic = pd.DataFrame({"White: Irish": [1.0, 2.0]}, index=cells)
        religion = pd.DataFrame({"Hindu": [5.0, 6.0]}, index=cells)
        birth = pd.DataFrame(
            {
                "United Kingdom": [60.0, 70.0],
                "European Union EU8": [3.0, 4.0],
                "British Overseas": [0.0, 0.1],
            },
            index=cells,
        )
        age = pd.DataFrame({"Children under 15": [18.0, 20.0]}, index=cells)
        options = community.community_options(ethnic, religion, birth=birth, age=age)
        found = [(o[0], o[1], o[2]) for o in options]
        assert ("born-united-kingdom", "Born in the United Kingdom", "Country of birth") in found
        assert (
            "born-european-union-eu8",
            "Born in the eastern EU (such as Poland)",
            "Country of birth",
        ) in found
        assert ("age-children-under-15", "Children under 15", "Age") in found
        assert not any("overseas" in option[0] for option in options)  # too few to rank
        assert options[-1][3].tolist() == [18.0, 20.0]

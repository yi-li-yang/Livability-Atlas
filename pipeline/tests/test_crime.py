import h3
import pandas as pd
import pytest
from pyproj import Transformer
from shapely.geometry import Polygon
from shapely.ops import transform

from atlas.indicators import crime

RESOLUTION = 9
TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True).transform
A = h3.latlng_to_cell(51.5136, -0.1337, RESOLUTION)  # Soho
B = next(c for c in h3.grid_ring(A, 1))
C = next(c for c in h3.grid_ring(A, 4))  # four steps from A: outside any 2-step pool of A or B


def polygon(cell: str):
    """A hex cell's outline in British National Grid, as an output area's boundary would be."""
    ring = [(lng, lat) for lat, lng in h3.cell_to_boundary(cell)]
    return transform(TO_BNG, Polygon(ring))


def areas(*rows):
    import geopandas as gpd

    return gpd.GeoDataFrame(
        {"OA21CD": [r[0] for r in rows]},
        geometry=[r[1] for r in rows],
        crs="EPSG:27700",
    )


class TestResidentsByCell:
    def test_an_area_that_is_one_cell_gives_the_cell_all_its_residents(self):
        result = crime.residents_by_cell(
            areas(("oa1", polygon(A))), pd.Series({"oa1": 1000}), [A, B]
        )
        assert result[A] == pytest.approx(1000, rel=1e-3)
        assert result.get(B, 0) == pytest.approx(0, abs=1)

    def test_an_area_over_two_cells_is_shared_by_the_area_of_overlap(self):
        whole = polygon(A).union(polygon(B))
        result = crime.residents_by_cell(areas(("oa1", whole)), pd.Series({"oa1": 600}), [A, B])
        assert result[A] == pytest.approx(300, rel=1e-3)
        assert result[B] == pytest.approx(300, rel=1e-3)

    def test_residents_are_not_lost_when_an_area_runs_beyond_the_cells(self):
        # Only A is in the region: the half of the area over B is dropped, not given to A.
        whole = polygon(A).union(polygon(B))
        result = crime.residents_by_cell(areas(("oa1", whole)), pd.Series({"oa1": 600}), [A])
        assert result[A] == pytest.approx(300, rel=1e-3)

    def test_an_area_without_a_resident_count_adds_nothing(self):
        result = crime.residents_by_cell(areas(("oa1", polygon(A))), pd.Series({"other": 5}), [A])
        assert result.get(A, 0) == 0


class TestCountsByCell:
    def crimes(self):
        lat, lng = h3.cell_to_latlng(A)
        far_lat, far_lng = h3.cell_to_latlng(C)
        return pd.DataFrame(
            {
                "Month": ["2026-07"] * 6,
                "Longitude": [lng, lng, lng, lng, far_lng, None],
                "Latitude": [lat, lat, lat, lat, far_lat, None],
                "Crime type": [
                    "Burglary",
                    "Burglary",
                    "Robbery",
                    "Theft from the person",
                    "Vehicle crime",
                    "Burglary",
                ],
            }
        )

    def test_counts_each_indicators_crime_types_in_the_cell_they_happened_in(self):
        counts = crime.counts_by_cell(self.crimes(), [A, B, C], RESOLUTION)
        assert counts["burglary"][A] == 2
        assert counts["robbery-and-theft-from-the-person"][A] == 2  # robbery + theft
        assert counts["vehicle-crime"][C] == 1
        assert counts["violence-and-sexual-offences"].sum() == 0

    def test_leaves_out_records_with_no_location_and_cells_outside_the_region(self):
        counts = crime.counts_by_cell(self.crimes(), [A, B], RESOLUTION)  # C is not in the region
        assert counts["burglary"].sum() == 2  # the record with no location is not counted
        assert counts["vehicle-crime"].sum() == 0


class TestRates:
    def test_a_rate_is_per_1000_residents_pooled_over_the_cell_and_its_neighbours(self):
        cells = [A, B, C]
        counts = pd.Series({A: 6, B: 0, C: 100})
        residents = pd.Series({A: 1000, B: 2000, C: 5000})
        # A pools A and B (C is three steps away): 6 crimes among 3,000 residents.
        rates = crime.rates(counts, residents, cells, steps=2, floor=0)
        assert rates[A] == pytest.approx(2.0)
        assert rates[B] == pytest.approx(2.0)
        assert rates[C] == pytest.approx(20.0)

    def test_a_floor_adds_residents_at_the_overall_rate_so_thin_places_move_to_the_average(self):
        cells = [A, C]
        counts = pd.Series({A: 5, C: 0})
        residents = pd.Series({A: 100, C: 900})
        overall = 5 / 1000  # per resident
        floor = 1000
        rates = crime.rates(counts, residents, cells, steps=2, floor=floor)
        expected_a = 1000 * (5 + floor * overall) / (100 + floor)
        assert rates[A] == pytest.approx(expected_a)
        assert rates[C] == pytest.approx(1000 * (0 + floor * overall) / (900 + floor))
        # With the floor, the thin cell's rate lies between its own raw rate and the average.
        assert 5.0 < rates[A] < 50.0

    def test_a_place_with_no_residents_and_no_floor_has_no_rate(self):
        rates = crime.rates(pd.Series({A: 3}), pd.Series({A: 0}), [A], steps=2, floor=0)
        assert rates.isna().all()

    def test_the_default_pool_is_two_steps_and_the_floor_is_3000_residents(self):
        assert crime.STEPS == 2
        assert crime.FLOOR == 3000


def test_the_five_indicators_are_those_of_the_catalogue():
    assert list(crime.CATEGORIES) == [
        "burglary",
        "violence-and-sexual-offences",
        "robbery-and-theft-from-the-person",
        "vehicle-crime",
        "anti-social-behaviour",
    ]


class TestWorkers:
    def test_the_jobs_of_an_area_are_shared_by_the_area_of_overlap_like_residents(self):
        import geopandas as gpd

        whole = polygon(A).union(polygon(B))
        lsoa = gpd.GeoDataFrame({"LSOA11CD": ["l1"]}, geometry=[whole], crs="EPSG:27700")
        result = crime.workers_by_cell(lsoa, pd.Series({"l1": 800.0}), [A, B])
        assert result[A] == pytest.approx(400, rel=1e-3)
        assert result[B] == pytest.approx(400, rel=1e-3)

    def test_people_present_are_residents_and_workers_together(self):
        residents = pd.Series({A: 100.0, B: 50.0})
        workers = pd.Series({A: 900.0, C: 30.0})
        people = crime.people_present(residents, workers)
        assert people[A] == 1000 and people[B] == 50 and people[C] == 30

    def test_a_cell_with_workers_and_no_residents_is_not_left_out(self):
        assert crime.people_present(pd.Series(dtype=float), pd.Series({A: 5.0}))[A] == 5.0


def test_a_crime_is_counted_per_residents_or_per_people_present_by_what_it_follows():
    # A home is burgled and a car stolen where residents live; a person is robbed, assaulted or
    # annoyed where people are, and in the City that is mostly workers and visitors.
    assert crime.DENOMINATOR == {
        "burglary": "residents",
        "vehicle-crime": "residents",
        "violence-and-sexual-offences": "people",
        "robbery-and-theft-from-the-person": "people",
        "anti-social-behaviour": "people",
    }
    assert set(crime.DENOMINATOR) == set(crime.CATEGORIES)

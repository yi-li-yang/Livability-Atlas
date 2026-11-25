import geopandas as gpd
import h3
import numpy as np
import pytest
from shapely.geometry import box

from atlas.datasets.cities.london import gla_elections
from atlas.indicators import turnout
from atlas.spatial.grid import cell_centres_bng

PAGE_ONE = """
   LONDON BOROUGH ELECTIONS MAY 2022   197

Barking and Dagenham

   Ballot papers
Ward   Seats   Electorate   Number   % poll   Polling   Postal
   Voting   Stations
Abbey   2   2,802   746   26.6%   536   210
Alibon   2   6,524   1,483   22.7%   865   618
"""

PAGE_TWO = """
Kensington & Chelsea
Ward   Seats   Electorate   Number   % poll   Polling   Postal
Brompton & Hans Town   3   7,000   2,100   30.0%   1,500   600
St. Helen's   2   5,000   2,000   40.0%   1,400   600
Ham, Petersham & Richmond   3   7,443   3,311   44.5%   2,000   1,311
Riverside
Hounslow
Hanworth Village   3   10,907   2,975   27.3%   1,959   1,016
Heston Central   3   9,500   2,975   31.3%   1,959   1,016
Bedfont   3   9,000   2,700   30.0%   2,000   700
"""

BOROUGHS = ["Barking and Dagenham", "Kensington and Chelsea", "Hounslow"]


class TestParseTables:
    def test_it_reads_each_ward_under_its_borough(self):
        rows = gla_elections.parse_tables([PAGE_ONE, PAGE_TWO], BOROUGHS)
        abbey = rows[(rows["borough"] == "Barking and Dagenham") & (rows["ward"] == "Abbey")]
        assert abbey[["electorate", "ballots"]].values.tolist() == [[2802, 746]]
        assert set(rows["borough"]) == set(BOROUGHS)

    def test_a_heading_with_an_ampersand_names_its_borough(self):
        rows = gla_elections.parse_tables([PAGE_ONE, PAGE_TWO], BOROUGHS)
        assert (
            "Brompton & Hans Town"
            in rows[rows["borough"] == "Kensington and Chelsea"]["ward"].tolist()
        )

    def test_a_long_name_that_wraps_onto_the_next_line_is_whole(self):
        rows = gla_elections.parse_tables([PAGE_ONE, PAGE_TWO], BOROUGHS)
        assert "Ham, Petersham & Richmond Riverside" in rows["ward"].tolist()

    def test_two_wards_of_a_borough_with_the_same_ballot_counts_are_left_out(self):
        # The GLA's report gives Hounslow's Hanworth Village and Heston Central the same ballots,
        # postal votes and all: one is a copy of the other, and which is unknown.
        rows = gla_elections.parse_tables([PAGE_ONE, PAGE_TWO], BOROUGHS)
        hounslow = rows[rows["borough"] == "Hounslow"]["ward"].tolist()
        assert hounslow == ["Bedfont"]

    def test_a_row_before_any_borough_is_refused(self):
        with pytest.raises(ValueError, match="borough"):
            gla_elections.parse_tables([PAGE_ONE.replace("Barking and Dagenham", "")], BOROUGHS)


def wards() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "WD22CD": ["E05000001", "E05000002", "E05000003", "E05000004"],
            "WD22NM": ["Abbey", "Brompton and Hans Town", "St Helen's", "Aldgate"],
            "LAD22NM": [
                "Barking and Dagenham",
                "Kensington and Chelsea",
                "Kensington and Chelsea",
                "City of London",
            ],
        },
        geometry=[
            box(0, 0, 1000, 1000),
            box(1000, 0, 2000, 1000),
            box(2000, 0, 3000, 1000),
            box(3000, 0, 4000, 1000),
        ],
        crs="EPSG:27700",
    )


class TestByWard:
    def test_it_joins_the_results_to_the_wards_by_borough_and_name(self):
        rows = gla_elections.parse_tables([PAGE_ONE, PAGE_TWO], BOROUGHS)
        found = turnout.by_ward(rows, wards())
        assert found.loc["E05000001"] == pytest.approx(746 / 2802 * 100)
        # "&" against "and", and "St." against "St": the same ward.
        assert found.loc["E05000002"] == pytest.approx(30.0)
        assert found.loc["E05000003"] == pytest.approx(40.0)
        assert np.isnan(found.loc["E05000004"])  # the City of London votes apart


class TestByCell:
    def test_a_cell_takes_the_turnout_of_the_ward_its_centre_lies_in(self):
        cells = [h3.latlng_to_cell(51.5, -0.1, 9), h3.latlng_to_cell(51.6, -0.2, 9)]
        x, y = cell_centres_bng(cells)[0]
        area = gpd.GeoDataFrame(
            {"WD22CD": ["E05000001"]},
            geometry=[box(x - 10, y - 10, x + 10, y + 10)],
            crs="EPSG:27700",
        )
        values = turnout.by_cell(area, {"E05000001": 33.0}, cells)
        assert values[0] == pytest.approx(33.0)
        assert np.isnan(values[1])

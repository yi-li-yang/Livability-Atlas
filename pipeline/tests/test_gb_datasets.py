import json
import zipfile
from pathlib import Path

import h3
import pytest

from atlas.datasets.countries.gb import census_residents, output_areas, police_uk
from atlas.spatial.grid import bounds_bng


class TestPoliceUk:
    def test_months_up_to_counts_back_from_the_latest_across_a_new_year(self):
        months = police_uk.months_up_to("2026-02", 4)
        assert months == ["2025-11", "2025-12", "2026-01", "2026-02"]

    def test_a_year_is_twelve_months(self):
        months = police_uk.months_up_to("2026-08")
        assert len(months) == 12
        assert months[0] == "2025-09"
        assert months[-1] == "2026-08"

    def archive(self, tmp_path: Path) -> Path:
        header = (
            "Crime ID,Month,Reported by,Falls within,Longitude,Latitude,Location,"
            "LSOA code,LSOA name,Crime type,Last outcome category,Context\n"
        )
        row = ",{m},x,x,-0.13,51.51,On or near X,E01,Westminster,{kind},,\n"
        path = tmp_path / "2026-08.zip"
        with zipfile.ZipFile(path, "w") as zipped:
            zipped.writestr(
                "2026-07/2026-07-metropolitan-street.csv",
                header + row.format(m="2026-07", kind="Burglary"),
            )
            zipped.writestr(
                "2026-07/2026-07-city-of-london-street.csv",
                header + row.format(m="2026-07", kind="Robbery"),
            )
            zipped.writestr(
                "2026-07/2026-07-kent-street.csv", header + row.format(m="2026-07", kind="Arson")
            )
            zipped.writestr(
                "2026-06/2026-06-metropolitan-street.csv",
                header + row.format(m="2026-06", kind="Vehicle crime"),
            )
        return path

    def test_reads_the_two_londons_forces_for_the_months_asked(self, tmp_path):
        crimes = police_uk.read_crimes(self.archive(tmp_path), ["2026-07"])
        assert sorted(crimes["Crime type"]) == ["Burglary", "Robbery"]
        assert list(crimes.columns) == police_uk.COLUMNS

    def test_skips_a_month_the_archive_lacks_and_other_forces(self, tmp_path):
        crimes = police_uk.read_crimes(self.archive(tmp_path), ["2026-05", "2026-06", "2026-07"])
        assert sorted(crimes["Crime type"]) == ["Burglary", "Robbery", "Vehicle crime"]

    def test_says_so_when_the_archive_has_none_of_the_months(self, tmp_path):
        with pytest.raises(ValueError, match="holds no crimes"):
            police_uk.read_crimes(self.archive(tmp_path), ["2020-01"])


def test_census_residents_are_indexed_by_output_area_code(tmp_path):
    path = tmp_path / "ts001.csv"
    path.write_text(
        '"date","geography","geography code","Residence type: Total; measures: Value",'
        '"Residence type: Lives in a household; measures: Value",'
        '"Residence type: Lives in a communal establishment; measures: Value"\n'
        '"2021","E00060274","E00060274",273,273,0\n'
        '"2021","E00060275","E00060275",416,400,16\n',
        encoding="utf-8",
    )
    residents = census_residents.read_residents(path)
    assert residents.to_dict() == {"E00060274": 273, "E00060275": 416}
    assert residents.index.name == "OA21CD"


def test_output_areas_are_read_in_british_national_grid(tmp_path):
    path = tmp_path / "oa.geojson"
    square = [
        [[530000, 180000], [530100, 180000], [530100, 180100], [530000, 180100], [530000, 180000]]
    ]
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"OA21CD": "E00000001", "other": 1},
                        "geometry": {"type": "Polygon", "coordinates": square},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    areas = output_areas.read_boundaries(path)
    assert list(areas.columns) == ["OA21CD", "geometry"]
    assert areas.crs is not None and areas.crs.to_epsg() == 27700
    assert areas.geometry.iloc[0].area == pytest.approx(10_000)


def test_bounds_bng_box_the_cells_and_widen_by_the_margin():
    soho = h3.latlng_to_cell(51.5136, -0.1337, 9)
    cells = sorted(h3.grid_disk(soho, 3))
    x0, y0, x1, y1 = bounds_bng(cells)
    wide = bounds_bng(cells, margin=500)
    assert (wide[0], wide[1], wide[2], wide[3]) == pytest.approx(
        (x0 - 500, y0 - 500, x1 + 500, y1 + 500)
    )
    # Soho is near easting 529,500 and northing 181,000 in British National Grid.
    assert 528_000 < x0 < x1 < 531_500
    assert 179_500 < y0 < y1 < 182_500

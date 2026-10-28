import h3
import pandas as pd
import pytest
from openpyxl import Workbook
from pyproj import Transformer

from atlas.datasets.cities.london.ptal import BANDS, bands_by_cell, read_grid

TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
RESOLUTION = 9
SOHO = h3.latlng_to_cell(51.5136, -0.1337, RESOLUTION)


def points_in(cell: str, bands: list[object]) -> pd.DataFrame:
    """One 100 m grid point at the centre of `cell` for each band, nudged by metres."""
    lat, lng = h3.cell_to_latlng(cell)
    x, y = TO_BNG.transform(lng, lat)
    return pd.DataFrame(
        {"x": [x + 10 * i for i in range(len(bands))], "y": [y] * len(bands), "band": bands}
    )


def test_a_cell_takes_the_band_that_covers_most_of_it():
    grid = points_in(SOHO, ["2", "2", "3"])
    assert bands_by_cell(grid, RESOLUTION).loc[SOHO] == "2"


def test_a_tie_goes_to_the_lower_band():
    grid = points_in(SOHO, ["3", "2", "3", "2"])
    assert bands_by_cell(grid, RESOLUTION).loc[SOHO] == "2"


def test_a_tie_between_the_top_bands_is_still_the_lower():
    grid = points_in(SOHO, ["6b", "6a"])
    assert bands_by_cell(grid, RESOLUTION).loc[SOHO] == "6a"


def test_the_lowest_band_is_a_band_and_not_a_missing_value():
    grid = points_in(SOHO, ["0", "0"])
    assert bands_by_cell(grid, RESOLUTION).loc[SOHO] == "0"


def test_each_cell_has_its_own_band():
    other = h3.latlng_to_cell(51.4613, -0.1156, RESOLUTION)
    grid = pd.concat([points_in(SOHO, ["6b"]), points_in(other, ["1a"])], ignore_index=True)
    bands = bands_by_cell(grid, RESOLUTION)
    assert bands.loc[SOHO] == "6b" and bands.loc[other] == "1a"


def test_the_result_is_sorted_by_cell():
    other = h3.latlng_to_cell(51.4613, -0.1156, RESOLUTION)
    grid = pd.concat([points_in(SOHO, ["6b"]), points_in(other, ["1a"])], ignore_index=True)
    assert list(bands_by_cell(grid, RESOLUTION).index) == sorted([SOHO, other])


def test_the_bands_run_from_worst_to_best():
    assert BANDS == ["0", "1a", "1b", "2", "3", "4", "5", "6a", "6b"]


def test_a_band_that_does_not_exist_is_an_error():
    with pytest.raises(ValueError):
        bands_by_cell(points_in(SOHO, ["7"]), RESOLUTION)


def test_the_grid_is_read_from_tfls_spreadsheet(tmp_path):
    workbook = Workbook()
    sheet = workbook.create_sheet("Query1")
    sheet.append(["ID", "X", "Y", "AI2015", "PTAL2015"])
    sheet.append([1, 530870, 155930, 0, 0])  # TfL writes the lowest band as a number
    sheet.append([2, 530945, 155898, 3.2, "1a"])
    sheet.append([3, 531045, 155898, 12, 3])
    path = tmp_path / "2015  PTALs Grid Values 280515.xlsx"
    workbook.save(path)
    grid = read_grid(path)
    assert list(grid.columns) == ["x", "y", "band"]
    assert list(grid["band"]) == ["0", "1a", "3"]
    assert list(grid["x"]) == [530870, 530945, 531045]

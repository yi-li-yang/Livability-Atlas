import zipfile
from pathlib import Path

import h3
import numpy as np
import pytest
from pyproj import Transformer

from atlas.datasets.cities.london import laei
from atlas.indicators import air_quality

TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
SOHO = h3.latlng_to_cell(51.5136, -0.1337, 9)


def concentrations_zip(tmp_path: Path, rows_by_pollutant: dict[str, list[tuple]]) -> Path:
    """A file in the layout of the LAEI's CSV download: a table of x, y and conc for each
    pollutant."""
    path = tmp_path / "LAEI2022-Concentrations-Data-CSV.zip"
    with zipfile.ZipFile(path, "w") as archive:
        for pollutant, rows in rows_by_pollutant.items():
            lines = ["x,y,conc"] + [f"{x},{y},{value}" for x, y, value in rows]
            archive.writestr(f"CSV/LAEI2022_V1_{pollutant}.csv", "\n".join(lines) + "\n")
    return path


def grid_over(cell: str, value) -> list[tuple]:
    """Points every 20 m over the cell's surroundings, valued by `value(x, y)`."""
    x, y = TO_BNG.transform(h3.cell_to_latlng(cell)[1], h3.cell_to_latlng(cell)[0])
    x0, y0 = round(x / 20) * 20, round(y / 20) * 20
    return [
        (px, py, value(px, py))
        for px in range(x0 - 400, x0 + 401, 20)
        for py in range(y0 - 400, y0 + 401, 20)
    ]


class TestReadConcentrations:
    def test_reads_a_pollutants_table_out_of_the_zip(self, tmp_path):
        path = concentrations_zip(
            tmp_path,
            {"NO2": [(100, 200, 31.5), (120, 200, 33.0)], "PM25": [(100, 200, 9.5)]},
        )
        grid = laei.read_concentrations(path, "NO2")
        assert grid.at(np.array([100.0, 120.0]), np.array([200.0, 200.0])).tolist() == [31.5, 33.0]

    def test_a_place_with_no_point_has_no_value(self, tmp_path):
        path = concentrations_zip(tmp_path, {"NO2": [(100, 200, 31.5), (120, 200, 33.0)]})
        grid = laei.read_concentrations(path, "NO2")
        far = grid.at(np.array([5000.0, 101.0]), np.array([9000.0, 5000.0]))
        assert np.isnan(far).all()

    def test_a_place_takes_the_value_of_the_nearest_point(self, tmp_path):
        path = concentrations_zip(tmp_path, {"NO2": [(100, 200, 31.5), (120, 200, 33.0)]})
        grid = laei.read_concentrations(path, "NO2")
        assert grid.at(np.array([107.0, 113.0]), np.array([203.0, 197.0])).tolist() == [31.5, 33.0]

    def test_downloads_the_file_once(self, tmp_path, monkeypatch):
        asked = []
        monkeypatch.setattr(laei, "download", lambda url, target: asked.append((url, target.name)))
        assert laei.fetch(tmp_path).name == "LAEI2022-Concentrations-Data-CSV.zip"
        assert asked[0][0].startswith("https://data.london.gov.uk/download/")


class TestMeanConcentration:
    def test_a_cell_of_one_value_has_that_value(self, tmp_path):
        path = concentrations_zip(tmp_path, {"NO2": grid_over(SOHO, lambda x, y: 27.25)})
        mean = air_quality.mean_concentration(laei.read_concentrations(path, "NO2"), [SOHO], 9)
        assert mean[SOHO] == pytest.approx(27.25)

    def test_a_cell_half_at_10_and_half_at_30_has_the_mean_of_the_two(self, tmp_path):
        centre_x = TO_BNG.transform(h3.cell_to_latlng(SOHO)[1], h3.cell_to_latlng(SOHO)[0])[0]
        path = concentrations_zip(
            tmp_path, {"NO2": grid_over(SOHO, lambda x, y: 10.0 if x < centre_x else 30.0)}
        )
        mean = air_quality.mean_concentration(laei.read_concentrations(path, "NO2"), [SOHO], 9)
        assert mean[SOHO] == pytest.approx(20.0, abs=1.5)

    def test_a_cell_outside_the_grid_has_no_value(self, tmp_path):
        path = concentrations_zip(tmp_path, {"NO2": grid_over(SOHO, lambda x, y: 27.25)})
        far = h3.latlng_to_cell(51.40, -0.40, 9)
        mean = air_quality.mean_concentration(laei.read_concentrations(path, "NO2"), [far], 9)
        assert np.isnan(mean[far])

import h3
import pandas as pd
import pytest

from atlas.datasets.countries.gb import dft_stats19
from atlas.families import collisions, discover

A = h3.latlng_to_cell(51.5136, -0.1337, 9)
B = next(iter(h3.grid_ring(A, 1)))


def test_the_collisions_of_the_years_are_averaged_per_year_in_each_cell():
    lat, lng = h3.cell_to_latlng(A)
    table = pd.DataFrame({"Latitude": [lat] * 6, "Longitude": [lng] * 6})
    counts = collisions.collisions_per_year(table, [A, B], 9)
    assert counts[A] == pytest.approx(6 / 3) and counts[B] == 0


def test_a_collision_outside_the_cells_is_left_out():
    far_lat, far_lng = h3.cell_to_latlng(h3.latlng_to_cell(51.0, 0.5, 9))
    table = pd.DataFrame({"Latitude": [far_lat], "Longitude": [far_lng]})
    assert collisions.collisions_per_year(table, [A], 9)[A] == 0


def test_only_fatal_and_serious_collisions_with_a_place_are_read(tmp_path):
    path = tmp_path / "collisions-2024.csv"
    path.write_text(
        "collision_index,longitude,latitude,collision_severity\n"
        "a,-0.1,51.5,1\nb,-0.1,51.5,2\nc,-0.1,51.5,3\nd,,,2\n",
        encoding="utf-8",
    )
    found = dft_stats19.read_collisions([path])
    assert len(found) == 2 and list(found.columns) == ["Longitude", "Latitude"]


def test_each_of_the_latest_three_years_is_fetched(tmp_path, monkeypatch):
    asked = []
    monkeypatch.setattr(dft_stats19, "download", lambda url, target: asked.append(target.name))
    dft_stats19.fetch(tmp_path)
    assert asked == ["collisions-2022.csv", "collisions-2023.csv", "collisions-2024.csv"]


def test_the_family_is_found():
    assert "collisions" in {f.name for f in discover()}


def test_the_family_rates_the_collisions_against_the_people_present(monkeypatch, tmp_path):
    from atlas.families import Context

    lat, lng = h3.cell_to_latlng(A)
    monkeypatch.setattr(dft_stats19, "fetch", lambda data_dir: [])
    monkeypatch.setattr(
        dft_stats19,
        "read_collisions",
        lambda paths: pd.DataFrame({"Latitude": [lat] * 30, "Longitude": [lng] * 30}),
    )
    ctx = Context("london", None, [A, B], tmp_path, pd.DataFrame(), None)  # type: ignore[arg-type]
    ctx.__dict__["people"] = pd.Series({A: 1000.0, B: 1000.0})  # stands in for the cached property
    ctx.__dict__["region"] = type("R", (), {"grid": type("G", (), {"resolution": 9})})()
    out = collisions.columns(ctx)["road-collisions"]
    assert out[0] is not None and out[0] > 0 and out[1] > 0  # B pools A as its neighbour

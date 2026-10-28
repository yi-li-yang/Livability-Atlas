import zipfile
from pathlib import Path

import h3
import numpy as np
import pandas as pd
import pytest

from atlas.datasets.countries.gb import code_point, nhs_ods
from atlas.indicators import health
from atlas.spatial.grid import cell_centres_bng
from atlas.spatial.walking import SPEED, Network


def practice(code: str, postcode: str, status: str = "ACTIVE", role: str = "RO76") -> str:
    """A row of NHS England's file of practices, which has 27 columns and no header."""
    row = [""] * 27
    row[0], row[1], row[9], row[12], row[25] = code, f"PRACTICE {code}", postcode, status, role
    return ",".join(f'"{value}"' for value in row)


def branch(code: str, parent: str, postcode: str, closed: str = "", name: str = "BRANCH") -> str:
    """A row of NHS England's file of branch surgeries, in the same layout."""
    row = [""] * 27
    row[0], row[1], row[9], row[11], row[14] = code, name, postcode, closed, parent
    return ",".join(f'"{value}"' for value in row)


def files(tmp_path: Path, practices: list[str], branches: list[str]) -> tuple[Path, Path]:
    one, two = tmp_path / "epraccur.csv", tmp_path / "ebranchs.csv"
    one.write_text("\n".join(practices) + "\n", encoding="utf-8")
    two.write_text("\n".join(branches) + "\n", encoding="utf-8")
    return one, two


class TestReadGpSites:
    def test_keeps_active_gp_practices_and_the_open_branches_of_them(self, tmp_path):
        practices, branches = files(
            tmp_path,
            [practice("A1", "W1F 9AA"), practice("A2", "N1 1AA")],
            [branch("A1B", "A1", "W1F 9AB")],
        )
        sites = nhs_ods.read_gp_sites(practices, branches)
        assert sites["Postcode"].tolist() == ["W1F 9AA", "N1 1AA", "W1F 9AB"]

    @pytest.mark.parametrize(
        "row",
        [
            practice("B1", "N1 1AA", status="INACTIVE"),
            practice("B2", "N1 1AA", status="DORMANT"),
            practice("B3", "N1 1AA", role="RO72"),  # a service that is not a GP practice
            practice("B4", ""),  # no postcode
        ],
    )
    def test_leaves_out_what_is_not_an_open_gp_practice(self, tmp_path, row):
        practices, branches = files(tmp_path, [row], [branch("Z", "NONE", "N1 1AA")])
        assert nhs_ods.read_gp_sites(practices, branches).empty

    @pytest.mark.parametrize(
        "row",
        [
            branch("C1", "A1", "N1 1AA", closed="20230630"),
            branch("C2", "GONE", "N1 1AA"),  # its practice is not an active GP practice
            branch("C3", "A1", "N1 1AA", name="PRACTICE - COVID LOCAL VACCINATION SERVICE"),
        ],
    )
    def test_leaves_out_branches_that_are_closed_orphaned_or_vaccination_sites(self, tmp_path, row):
        practices, branches = files(tmp_path, [practice("A1", "W1F 9AA")], [row])
        assert nhs_ods.read_gp_sites(practices, branches)["Postcode"].tolist() == ["W1F 9AA"]


class TestFetch:
    def test_downloads_the_two_files_once(self, tmp_path, monkeypatch):
        asked = []

        def fake_download(url, target):
            asked.append(target.name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("x", encoding="utf-8")
            return "digest"

        monkeypatch.setattr(nhs_ods, "download", fake_download)
        practices, branches = nhs_ods.fetch(tmp_path)
        assert (practices.name, branches.name) == ("epraccur.csv", "ebranchs.csv")
        assert asked == ["epraccur.csv", "ebranchs.csv"]


def codepoint_zip(tmp_path: Path, *rows: str) -> Path:
    path = tmp_path / "codepo_gb.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("Data/CSV/w.csv", "\n".join(rows[:2]) + "\n")
        archive.writestr("Data/CSV/n.csv", "\n".join(rows[2:]) + "\n")
        archive.writestr("Doc/licence.txt", "not a table")
    return path


class TestCodePoint:
    def test_places_every_postcode_by_its_spaceless_capitalised_form(self, tmp_path):
        path = codepoint_zip(
            tmp_path,
            '"W1F 9AA",10,529000,181000,"E92000001"',
            '"W1F 9AB",10,529100,181100,"E92000001"',
            '"N1 1AA",10,531000,184000,"E92000001"',
        )
        postcodes = code_point.read_postcodes(path)
        assert postcodes.loc["W1F9AA", ["Easting", "Northing"]].tolist() == [529000, 181000]
        assert postcodes.loc["N11AA", "Easting"] == 531000
        assert len(postcodes) == 3

    def test_leaves_out_a_postcode_without_a_place(self, tmp_path):
        path = codepoint_zip(
            tmp_path,
            '"W1F 9AA",90,0,0,"E92000001"',
            '"W1F 9AB",10,529100,181100,"E92000001"',
            '"N1 1AA",10,531000,184000,"E92000001"',
        )
        assert "W1F9AA" not in code_point.read_postcodes(path).index

    def test_downloads_the_great_britain_file_once(self, tmp_path, monkeypatch):
        asked = []

        def fake_download(url, target):
            asked.append((url, target.name))
            return "digest"

        monkeypatch.setattr(code_point, "download", fake_download)
        assert code_point.fetch(tmp_path).name == "codepo_gb.zip"
        assert "CodePointOpen" in asked[0][0] and "redirect" in asked[0][0]


class TestGpMinutes:
    def test_places_are_the_sites_found_in_code_point(self):
        sites = pd.DataFrame({"Postcode": ["W1F 9AA", "w1f9ab", "ZZ9 9ZZ"]})
        postcodes = pd.DataFrame(
            {"Easting": [529000, 529100], "Northing": [181000, 181100]},
            index=["W1F9AA", "W1F9AB"],
        )
        places = health.gp_places(sites, postcodes)
        assert places.tolist() == [[529000, 181000], [529100, 181100]]  # the unknown one is out

    def test_the_minutes_to_the_nearest_practice_follow_the_street(self):
        soho = h3.latlng_to_cell(51.5136, -0.1337, 9)
        x, y = cell_centres_bng([soho])[0]
        street = [(i, x - 400 + 80.0 * i, y) for i in range(11)]  # 80 m a node
        places = np.array([[x + 240, y], [x + 640, y]])
        minutes = health.gp_minutes(Network.from_ways([street]), places, [soho])
        assert minutes[soho] == pytest.approx(240 / SPEED, abs=0.2)

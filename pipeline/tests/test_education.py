from datetime import date
from pathlib import Path

import h3
import numpy as np
import pandas as pd
import pytest
import requests

from atlas.datasets.countries.gb import gias
from atlas.indicators import education
from atlas.spatial.grid import cell_centres_bng
from atlas.spatial.walking import SPEED, Network

HEADER = (
    "URN,EstablishmentStatus (name),EstablishmentTypeGroup (name),TypeOfEstablishment (name),"
    "PhaseOfEducation (name),Easting,Northing\n"
)


def register(tmp_path: Path, *rows: str) -> Path:
    path = tmp_path / "edubasealldata20261028.csv"
    path.write_text(HEADER + "\n".join(rows) + "\n", encoding="cp1252")
    return path


class TestReadSchools:
    def test_keeps_open_state_funded_mainstream_schools_of_each_phase(self, tmp_path):
        path = register(
            tmp_path,
            "1,Open,Local authority maintained schools,Community school,Primary,530000,180000",
            "2,Open,Academies,Academy converter,Secondary,531000,181000",
            "3,Open,Free Schools,Free schools,All-through,532000,182000",
            "4,Open,Academies,Academy sponsor led,Middle-deemed primary,533000,183000",
        )
        schools = gias.read_schools(path)
        assert schools[["Easting", "primary", "secondary"]].values.tolist() == [
            [530000.0, True, False],
            [531000.0, False, True],
            [532000.0, True, True],  # an all-through school is both
            [533000.0, True, False],
        ]

    @pytest.mark.parametrize(
        "row",
        [
            "1,Closed,Local authority maintained schools,Community school,Primary,530000,180000",
            "2,Open,Independent schools,Other independent school,Secondary,530000,180000",
            "3,Open,Special schools,Community special school,Primary,530000,180000",
            "4,Open,Academies,Academy special converter,Secondary,530000,180000",
            "5,Open,Local authority maintained schools,Pupil referral unit,Secondary,530000,180000",
            "6,Open,Free Schools,Free schools alternative provision,Secondary,530000,180000",
            "7,Open,Free Schools,Free schools 16 to 19,16 plus,530000,180000",
            "8,Open,Local authority maintained schools,Local authority nursery school,Nursery,1,1",
            "9,Open,Universities,Higher education institutions,Not applicable,530000,180000",
            "10,Open,Academies,Academy converter,Primary,,",
        ],
    )
    def test_leaves_out_what_a_child_would_not_walk_to_as_a_school(self, tmp_path, row):
        assert gias.read_schools(register(tmp_path, row)).empty

    def test_an_open_school_proposed_to_close_still_counts(self, tmp_path):
        row = '1,"Open, but proposed to close",Academies,Academy converter,Primary,530000,180000'
        assert len(gias.read_schools(register(tmp_path, row))) == 1


class TestFetch:
    def test_uses_the_register_already_kept(self, tmp_path):
        folder = tmp_path / "raw" / "gias"
        folder.mkdir(parents=True)
        (folder / "edubasealldata20260101.csv").write_text("x", encoding="utf-8")
        (folder / "edubasealldata20260301.csv").write_text("x", encoding="utf-8")
        assert gias.fetch(tmp_path).name == "edubasealldata20260301.csv"

    def test_goes_back_a_day_when_todays_file_is_not_made_yet(self, tmp_path, monkeypatch):
        asked = []

        def fake_download(url, target):
            asked.append(target.name)
            if "20261028" in url:
                raise requests.HTTPError("404")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("x", encoding="utf-8")
            return "digest"

        monkeypatch.setattr(gias, "download", fake_download)
        path = gias.fetch(tmp_path, today=date(2026, 10, 28))
        assert path.name == "edubasealldata20261027.csv"
        assert asked == ["edubasealldata20261028.csv", "edubasealldata20261027.csv"]


class TestSchoolMinutes:
    def test_the_minutes_to_the_nearest_school_of_each_phase_follow_the_street(self):
        soho = h3.latlng_to_cell(51.5136, -0.1337, 9)
        x, y = cell_centres_bng([soho])[0]
        street = [(i, x - 400 + 80.0 * i, y) for i in range(11)]  # 80 m a node, so a minute a step
        schools = pd.DataFrame(
            {
                "Easting": [x + 160, x + 400],  # 2 minutes east, 5 minutes east
                "Northing": [y, y],
                "primary": [True, False],
                "secondary": [False, True],
            }
        )
        result = education.school_minutes(Network.from_ways([street]), schools, [soho])
        assert result["primary-schools"][soho] == pytest.approx(160 / SPEED, abs=0.2)
        assert result["secondary-schools"][soho] == pytest.approx(400 / SPEED, abs=0.2)
        assert np.isfinite(result["primary-schools"][soho])

import zipfile
from pathlib import Path

import h3
import numpy as np
import pandas as pd
import pytest

from atlas.datasets.countries.gb import nhs_gp
from atlas.indicators import health
from atlas.spatial.grid import cell_centres_bng
from atlas.spatial.walking import Network

PATIENTS_HEADER = (
    "PUBLICATION,EXTRACT_DATE,TYPE,SUB_ICB_LOCATION_CODE,ONS_SUB_ICB_LOCATION_CODE,CODE,POSTCODE,"
    "SEX,AGE,NUMBER_OF_PATIENTS"
)
WORKFORCE_HEADER = "﻿PRAC_CODE,PRAC_NAME,STAFF_GROUP,DETAILED_STAFF_ROLE,MEASURE,VALUE"


def patients_zip(tmp_path: Path, rows: list[str]) -> Path:
    path = tmp_path / "patients.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("gp-reg-pat-prac-all.csv", "\n".join([PATIENTS_HEADER, *rows]) + "\n")
    return path


def patient_row(code: str, postcode: str, number: int, kind: str = "GP", sex: str = "ALL") -> str:
    return f"GP_PRAC_PAT_LIST,2026-09-01,{kind},16C,E38000247,{code},{postcode},{sex},ALL,{number}"


def workforce_zip(tmp_path: Path, rows: list[str]) -> Path:
    path = tmp_path / "workforce.zip"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "3 General Practice – September 2026 Practice Level - High level.csv",
            "\n".join([WORKFORCE_HEADER, *rows]) + "\n",
        )
        archive.writestr("1 General Practice – Practice Level - Detailed.csv", "not the table\n")
    return path


def gp_row(code: str, role: str, fte: float, group: str = "GP", measure: str = "FTE") -> str:
    return f"{code},PRACTICE {code},{group},{role},{measure},{fte}"


class TestReadPractices:
    def test_a_practice_has_its_postcode_patients_and_qualified_gps(self, tmp_path):
        patients = patients_zip(tmp_path, [patient_row("A1", "W1F 9AA", 9000)])
        workforce = workforce_zip(
            tmp_path,
            [
                gp_row("A1", "Partner/Provider", 2.0),
                gp_row("A1", "Salaried By Practice", 1.5),
                gp_row("A1", "Locum - other", 0.5),
                gp_row("A1", "Retainer", 0.25),
                gp_row("A1", "GP in Training Grade ST3", 1.0),
                gp_row("A1", "Total", 5.25),
            ],
        )
        practices = nhs_gp.read_practices(patients, workforce)
        assert practices.loc["A1", "Postcode"] == "W1F 9AA"
        assert practices.loc["A1", "patients"] == 9000
        assert practices.loc["A1", "gps"] == pytest.approx(4.25)  # trainees and the total are out

    def test_only_the_whole_practice_counts_not_a_sex_or_a_nurse_or_headcount(self, tmp_path):
        patients = patients_zip(
            tmp_path,
            [patient_row("A1", "W1F 9AA", 9000), patient_row("A1", "W1F 9AA", 4000, sex="MALE")],
        )
        workforce = workforce_zip(
            tmp_path,
            [
                gp_row("A1", "Partner/Provider", 2.0),
                gp_row("A1", "Partner/Provider", 3, measure="Headcount"),
                gp_row("A1", "Salaried By Practice", 7.0, group="Nurses"),
            ],
        )
        practices = nhs_gp.read_practices(patients, workforce)
        assert practices.loc["A1", "patients"] == 9000
        assert practices.loc["A1", "gps"] == pytest.approx(2.0)

    def test_a_practice_without_gps_on_record_has_none(self, tmp_path):
        patients = patients_zip(tmp_path, [patient_row("A1", "W1F 9AA", 900)])
        workforce = workforce_zip(tmp_path, [gp_row("B2", "Partner/Provider", 1.0)])
        assert nhs_gp.read_practices(patients, workforce).loc["A1", "gps"] == 0.0

    def test_a_row_that_is_not_a_practice_is_left_out(self, tmp_path):
        patients = patients_zip(
            tmp_path,
            [patient_row("A1", "W1F 9AA", 900), patient_row("16C", "", 90000, kind="CCG")],
        )
        workforce = workforce_zip(tmp_path, [gp_row("A1", "Partner/Provider", 1.0)])
        assert nhs_gp.read_practices(patients, workforce).index.tolist() == ["A1"]

    def test_the_files_are_fetched_once(self, tmp_path, monkeypatch):
        asked = []
        monkeypatch.setattr(nhs_gp, "download", lambda url, target: asked.append(target.name))
        assert [p.name for p in nhs_gp.fetch(tmp_path)] == ["patients.zip", "workforce.zip"]
        assert asked == ["patients.zip", "workforce.zip"]


class TestLocatedPractices:
    def test_a_practice_is_placed_by_its_postcode_and_one_without_a_place_is_left_out(self):
        practices = pd.DataFrame(
            {"Postcode": ["W1F 9AA", "ZZ9 9ZZ"], "patients": [9000, 500], "gps": [3.0, 1.0]},
            index=pd.Index(["A1", "A2"], name="code"),
        )
        postcodes = pd.DataFrame({"Easting": [529000], "Northing": [181000]}, index=["W1F9AA"])
        located = health.located_practices(practices, postcodes)
        assert located.index.tolist() == ["A1"]
        assert located.loc["A1", ["Easting", "Northing", "patients", "gps"]].tolist() == [
            529000,
            181000,
            9000,
            3.0,
        ]


def street_from(cell: str) -> tuple[Network, float, float]:
    x, y = cell_centres_bng([cell])[0]
    nodes = [(i, x - 400 + 80.0 * i, y) for i in range(31)]  # 2.4 km of street, 80 m a node
    return Network.from_ways([nodes]), x, y


class TestPatientsPerGp:
    cell = h3.latlng_to_cell(51.5136, -0.1337, 9)

    def test_it_is_the_patients_of_the_practices_in_reach_over_their_gps(self):
        network, x, y = street_from(self.cell)
        places = np.array([[x + 240, y], [x + 480, y]])  # both within a 15-minute walk (1,200 m)
        ratio = health.patients_per_gp(
            network, places, np.array([6000.0, 3000.0]), np.array([2.0, 1.0]), [self.cell]
        )
        assert ratio[self.cell] == pytest.approx(3000.0)  # 9,000 patients over 3 GPs, not a mean

    def test_a_practice_beyond_the_walk_does_not_count(self):
        network, x, y = street_from(self.cell)
        places = np.array([[x + 240, y], [x + 1800, y]])  # the second is 1,800 m away
        ratio = health.patients_per_gp(
            network, places, np.array([6000.0, 3000.0]), np.array([2.0, 1.0]), [self.cell]
        )
        assert ratio[self.cell] == pytest.approx(3000.0)  # 6,000 patients over 2 GPs

    def test_a_cell_with_no_practice_in_reach_has_no_value(self):
        network, x, y = street_from(self.cell)
        places = np.array([[x + 1800, y]])
        ratio = health.patients_per_gp(
            network, places, np.array([6000.0]), np.array([2.0]), [self.cell]
        )
        assert np.isnan(ratio[self.cell])

    def test_practices_without_a_gp_make_no_ratio(self):
        network, x, y = street_from(self.cell)
        places = np.array([[x + 240, y]])
        ratio = health.patients_per_gp(
            network, places, np.array([6000.0]), np.array([0.0]), [self.cell]
        )
        assert np.isnan(ratio[self.cell])

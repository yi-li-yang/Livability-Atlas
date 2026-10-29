from pathlib import Path

import h3
import numpy as np
import pandas as pd
import pytest

from atlas.datasets.countries.gb import gias, ofsted
from atlas.indicators import education
from atlas.spatial.grid import cell_centres_bng
from atlas.spatial.walking import Network

AREAS = [
    "Inclusion",
    "Curriculum and teaching",
    "Achievement",
    "Attendance and behaviour",
    "Personal development and wellbeing",
    "Leadership and governance",
    "Early years (where applicable)",
    "Post-16 provision (where applicable)",
]
OLD = [
    "Latest OEIF overall effectiveness",
    "Ungraded inspection overall outcome",
]
HEADER = ",".join(["URN", "Ofsted phase", "Safeguarding standards", *AREAS, *OLD])


def row(
    urn: int,
    safeguarding: str = "",
    area: str = "",
    overall: str = "",
    ungraded: str = "",
    phase: str = "Primary",
) -> str:
    values = [str(urn), phase, safeguarding, *[area] * len(AREAS), overall, ungraded]
    return ",".join(values)


def inspections(tmp_path: Path, *rows: str) -> Path:
    path = tmp_path / "latest.csv"
    path.write_text("\n".join([HEADER, *rows]) + "\n", encoding="latin-1")
    return path


class TestReadJudgements:
    def test_it_reads_the_urn_and_the_judgements_of_primary_and_secondary_schools(self, tmp_path):
        path = inspections(
            tmp_path,
            row(1, "Met", "Expected standard"),
            row(2, overall="2", phase="Secondary"),
            row(3, phase="Special"),
            row(4, phase="Nursery"),
        )
        found = ofsted.read_judgements(path)
        assert found["URN"].tolist() == [1, 2]
        assert "Safeguarding standards" in found.columns

    def test_the_file_is_fetched_once(self, tmp_path, monkeypatch):
        asked = []
        monkeypatch.setattr(ofsted, "download", lambda url, target: asked.append(target.name))
        assert ofsted.fetch(tmp_path).name == "latest-inspections.csv"
        assert asked == ["latest-inspections.csv"]


def frame(**columns) -> pd.DataFrame:
    blank = {
        "Safeguarding standards": [""],
        **{a: [""] for a in AREAS},
        "Latest OEIF overall effectiveness": [""],
        "Ungraded inspection overall outcome": [""],
    }
    blank.update({k.replace("_", " "): [v] for k, v in columns.items()})
    return pd.DataFrame(blank).replace("", np.nan)


class TestMeetsTheStandard:
    def meets(self, **columns):
        return education.meets_standard(frame(**columns)).iloc[0]

    def test_a_report_card_with_safeguarding_met_and_no_area_below_expected_meets_it(self):
        assert self.meets(Safeguarding_standards="Met", Inclusion="Strong standard") == 1

    def test_one_area_that_needs_attention_or_urgent_improvement_does_not(self):
        assert self.meets(Safeguarding_standards="Met", Achievement="Needs attention") == 0
        assert self.meets(Safeguarding_standards="Met", Achievement="Urgent improvement") == 0

    def test_safeguarding_not_met_does_not(self):
        assert self.meets(Safeguarding_standards="Not met", Inclusion="Exceptional") == 0

    def test_an_area_not_applicable_does_not_count_against_a_school(self):
        card = {"Safeguarding_standards": "Met", "Early_years": "Not applicable"}
        assert self.meets(**card) == 1

    def test_the_report_card_wins_over_an_older_grade(self):
        card = {
            "Safeguarding_standards": "Met",
            "Achievement": "Needs attention",
            "Latest_OEIF_overall_effectiveness": "1",
        }
        assert self.meets(**card) == 0

    def test_without_a_report_card_good_and_outstanding_meet_it(self):
        assert self.meets(Latest_OEIF_overall_effectiveness="1") == 1
        assert self.meets(Latest_OEIF_overall_effectiveness="2") == 1

    def test_without_a_report_card_requires_improvement_and_inadequate_do_not(self):
        assert self.meets(Latest_OEIF_overall_effectiveness="3") == 0
        assert self.meets(Latest_OEIF_overall_effectiveness="4") == 0

    @pytest.mark.parametrize(
        "outcome",
        [
            "School remains Good",
            "School remains Outstanding",
            "Standards maintained",
            "School remains Good (Concerns) - S5 Next",
            "School remains Outstanding (Concerns) - S5 Next",
        ],
    )
    def test_a_school_with_no_grade_but_a_later_inspection_that_kept_it_good_meets_it(
        self, outcome
    ):
        assert self.meets(Ungraded_inspection_overall_outcome=outcome) == 1
        graded_not_judged = {
            "Latest_OEIF_overall_effectiveness": "Not judged",
            "Ungraded_inspection_overall_outcome": outcome,
        }
        assert self.meets(**graded_not_judged) == 1

    def test_a_grade_is_not_overturned_by_an_ungraded_visit(self):
        both = {
            "Latest_OEIF_overall_effectiveness": "3",
            "Ungraded_inspection_overall_outcome": "School remains Good",
        }
        assert self.meets(**both) == 0

    @pytest.mark.parametrize("outcome", ["Improved significantly", "Some aspects not as strong"])
    def test_an_outcome_that_does_not_say_good_leaves_the_school_unjudged(self, outcome):
        assert np.isnan(self.meets(Ungraded_inspection_overall_outcome=outcome))

    def test_a_school_never_inspected_is_unjudged(self):
        assert np.isnan(self.meets())


class TestInspectionShare:
    cell = h3.latlng_to_cell(51.5136, -0.1337, 9)

    def setup(self, offsets, meets):
        x, y = cell_centres_bng([self.cell])[0]
        street = [(i, x - 400 + 80.0 * i, y) for i in range(61)]  # 4.8 km of street
        schools = pd.DataFrame(
            {"Easting": [x + o for o in offsets], "Northing": [y] * len(offsets), "meets": meets}
        )
        return Network.from_ways([street]), schools

    def test_it_is_the_percentage_of_judged_schools_within_the_walk_that_meet_the_standard(self):
        network, schools = self.setup([400, 800, 1200, 1600], [1.0, 1.0, 0.0, 1.0])
        share = education.inspection_share(network, schools, [self.cell], minutes=25, minimum=3)
        assert share[self.cell] == pytest.approx(75.0)

    def test_a_school_beyond_the_walk_is_not_counted(self):
        network, schools = self.setup([400, 800, 1200, 2600], [1.0, 1.0, 0.0, 0.0])
        share = education.inspection_share(network, schools, [self.cell], minutes=25, minimum=3)
        assert share[self.cell] == pytest.approx(200 / 3)

    def test_a_school_without_a_judgement_is_not_counted(self):
        network, schools = self.setup([400, 800, 1200, 1600], [1.0, np.nan, 0.0, 1.0])
        share = education.inspection_share(network, schools, [self.cell], minutes=25, minimum=3)
        assert share[self.cell] == pytest.approx(200 / 3)

    def test_with_fewer_judged_schools_than_the_minimum_there_is_no_value(self):
        network, schools = self.setup([400, 800], [1.0, 1.0])
        share = education.inspection_share(network, schools, [self.cell], minutes=25, minimum=3)
        assert np.isnan(share[self.cell])


class TestGiasKeepsTheUrn:
    def test_the_schools_have_their_urn(self, tmp_path):
        header = (
            "URN,EstablishmentStatus (name),EstablishmentTypeGroup (name),"
            "TypeOfEstablishment (name),PhaseOfEducation (name),Easting,Northing\n"
        )
        path = tmp_path / "edubasealldata20261028.csv"
        path.write_text(
            header + "100001,Open,Academies,Academy converter,Primary,530000,180000\n",
            encoding="cp1252",
        )
        assert gias.read_schools(path)["URN"].tolist() == [100001]

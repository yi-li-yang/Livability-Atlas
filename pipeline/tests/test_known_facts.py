"""Facts about London that the built data must agree with.

The facts are in `datasets/cities/london/facts.py`, and the QA report runs them on every build.
These tests run each of them on the real bundle that `just data london` builds, so that one that
fails shows by name. They are skipped where there is no bundle, as in CI.
"""

import json

import pytest

from atlas.paths import data_dir
from atlas.qa.cells import Cells, read_cells
from atlas.qa.facts import fact_checks
from atlas.qa.regional import regional
from atlas.qa.relations import relation_checks

LONDON = data_dir() / "published" / "london"
pytestmark = pytest.mark.skipif(
    not (LONDON / "latest.json").exists(), reason="no built London bundle: run `just data london`"
)

FACTS = regional("london").facts
RELATIONS = regional("london").relations


@pytest.fixture(scope="module")
def cells() -> Cells:
    version = json.loads((LONDON / "latest.json").read_text(encoding="utf-8"))["version"]
    return read_cells(LONDON / version, regional("london").places)


@pytest.mark.parametrize("fact", FACTS, ids=lambda fact: fact.id)
def test_london_fact(cells, fact):
    [result] = fact_checks(cells, [fact])
    assert result.status == "pass", f"{result.name}: {result.detail}"


@pytest.mark.parametrize("relation", RELATIONS, ids=lambda r: f"{r.a}-{r.b}")
def test_london_relation(cells, relation):
    [result] = relation_checks(cells, [relation])
    assert result.status == "pass", f"{result.name}: {result.detail}"

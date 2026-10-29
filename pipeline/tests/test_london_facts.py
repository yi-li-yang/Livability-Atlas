"""London's facts and relations, checked without any data: that they name columns that exist."""

import ast
import inspect
import textwrap

import pytest

from atlas.catalogue.load import load_catalogue
from atlas.catalogue.models import Factor
from atlas.paths import CATALOGUE_DIR
from atlas.qa.regional import regional

LONDON = regional("london")


def built(nodes: list[Factor]) -> dict[str, Factor]:
    found: dict[str, Factor] = {}
    for node in nodes:
        if node.children is None:
            if node.status == "built":
                found[node.id] = node
        else:
            found |= built(node.children)
    return found


class Columns:
    """The columns a bundle can have: those of the indicators, the prefixes of the options of the
    choice indicators, and the neighbourhood."""

    def __init__(self) -> None:
        indicators = built(load_catalogue(CATALOGUE_DIR).factors.factors)
        choices = {i for i, n in indicators.items() if n.preference_type == "user-choice"}
        self.plain = {i.replace("-", "_") for i in indicators if i not in choices}
        self.plain.add("neighbourhood")
        self.prefixes = {i.replace("-", "_") for i in choices}

    def has(self, column: str) -> bool:
        prefix, separator, option = column.partition("__")
        return column in self.plain or (bool(separator and option) and prefix in self.prefixes)


@pytest.fixture(scope="module")
def columns() -> Columns:
    return Columns()


def test_london_has_facts_and_relations():
    assert len(LONDON.facts) >= 25 and len(LONDON.relations) >= 10


def test_every_fact_needs_columns_that_a_bundle_can_have(columns):
    for fact in LONDON.facts:
        for column in fact.needs:
            assert columns.has(column), f"{fact.id} needs {column}"


def test_every_relation_names_columns_that_a_bundle_can_have(columns):
    for relation in LONDON.relations:
        for column in (relation.a, relation.b):
            assert columns.has(column), f"{relation.a} and {relation.b}: {column}"


def test_a_fact_needs_every_column_it_names_in_its_code(columns):
    """A fact that reads a column it does not list in `needs` would fail, not be skipped, in a
    bundle that lacks the column."""
    for fact in LONDON.facts:
        tree = ast.parse(textwrap.dedent(inspect.getsource(fact.run)))
        [function] = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
        named = {
            node.value
            for statement in function.body
            for node in ast.walk(statement)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
            if columns.has(node.value)
        }
        missing = named - set(fact.needs)
        assert not missing, f"{fact.id} reads {sorted(missing)} but does not list them in needs"


def test_the_places_are_in_greater_london():
    for name, (lat, lng) in LONDON.places.items():
        assert 51.28 < lat < 51.70 and -0.52 < lng < 0.34, name


def test_no_two_facts_say_the_same_thing():
    statements = [fact.statement for fact in LONDON.facts]
    assert len(statements) == len(set(statements))
    assert all(s[0].isupper() and not s.endswith(".") for s in statements)

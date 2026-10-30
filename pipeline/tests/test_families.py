import sys
import textwrap
from pathlib import Path

import pandas as pd

from atlas import families
from atlas.families import Context, Family, built_from, discover, run
from atlas.publish.bundle import Choice


def context(tmp_path: Path) -> Context:
    return Context(
        region_id="london",
        region=None,  # type: ignore[arg-type]  # a family under test names what it reads
        cells=["a", "b"],
        data_dir=tmp_path,
        postcodes=pd.DataFrame(),
        network=None,  # type: ignore[arg-type]
    )


def test_a_module_of_the_package_that_names_a_family_is_found_in_name_order(tmp_path, monkeypatch):
    package = tmp_path / "fake_families"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    for name, indicator in (("b_second", "two"), ("a_first", "one")):
        (package / f"{name}.py").write_text(
            textwrap.dedent(
                f"""
                from atlas.families import Family
                FAMILY = Family("{name}", lambda ctx: {{"{indicator}": [1, 2]}})
                """
            ),
            encoding="utf-8",
        )
    (package / "helper.py").write_text("X = 1\n", encoding="utf-8")  # no FAMILY: not a family
    monkeypatch.syspath_prepend(str(tmp_path))
    try:
        found = discover("fake_families")
    finally:
        for name in [m for m in sys.modules if m.startswith("fake_families")]:
            del sys.modules[name]
    assert [f.name for f in found] == ["a_first", "b_second"]


def test_the_real_package_is_found_and_every_family_is_well_formed():
    for family in discover():
        assert family.name and callable(family.columns)


def test_running_families_gathers_their_columns_and_choices(tmp_path):
    first = Family("first", lambda ctx: {"one": [1, 2]})
    second = Family(
        "second",
        lambda ctx: {"two": [3.0, None]},
        choices=lambda ctx: {"pick": [Choice(id="x", name="X", group=None, values=[1, 2])]},
    )
    columns, choices = run([first, second], context(tmp_path))
    assert list(columns) == ["one", "two"]
    assert [c.id for c in choices["pick"]] == ["x"]


def test_two_families_cannot_build_the_same_indicator(tmp_path):
    clash = [Family("a", lambda ctx: {"one": [1, 2]}), Family("b", lambda ctx: {"one": [3, 4]})]
    try:
        run(clash, context(tmp_path))
    except ValueError as error:
        assert "one" in str(error) and "a" in str(error) and "b" in str(error)
    else:
        raise AssertionError("a clash must be an error")


def test_a_family_that_returns_a_column_of_the_wrong_length_is_an_error(tmp_path):
    short = Family("short", lambda ctx: {"one": [1]})
    try:
        run([short], context(tmp_path))
    except ValueError as error:
        assert "one" in str(error) and "2" in str(error)
    else:
        raise AssertionError("a short column must be an error")


def test_the_datasets_an_indicator_is_built_from_are_gathered(tmp_path):
    first = Family("first", lambda ctx: {}, built_from={"one": ("ds-a",)})
    second = Family("second", lambda ctx: {}, built_from={"two": ("ds-b", "ds-c")})
    assert built_from([first, second]) == {"one": ("ds-a",), "two": ("ds-b", "ds-c")}


def test_the_package_has_a_docstring_that_says_how_to_add_a_family():
    assert families.__doc__ and "FAMILY" in families.__doc__

import json

import pytest

from atlas.catalogue.load import load_catalogue
from atlas.paths import CATALOGUE_DIR
from atlas.qa.regional import Regional
from atlas.qa.release import check, release
from tests.qa_sample import spoil, write_sample

NOTHING_REGIONAL = Regional(places={}, facts=[], relations=[])


@pytest.fixture(scope="module")
def catalogue():
    return load_catalogue(CATALOGUE_DIR)


def latest(tmp_path) -> dict:
    return json.loads((tmp_path / "london" / "latest.json").read_text(encoding="utf-8"))


def test_a_bundle_that_passes_gets_its_report_and_is_published(tmp_path, catalogue):
    folder = write_sample(tmp_path, publish=False)
    report = release(folder, catalogue, regional=NOTHING_REGIONAL)
    assert not report.failed
    assert (folder / "qa.md").read_text(encoding="utf-8") == report.markdown()
    assert latest(tmp_path) == {"version": folder.name}


def test_a_bundle_with_a_failed_check_gets_its_report_and_is_not_published(tmp_path, catalogue):
    old = write_sample(tmp_path)
    new = spoil(
        write_sample(tmp_path, columns={"station-proximity": [1, 2, 3, 4, 5, 6, 7]}, publish=False),
        manifest=lambda m: m.update(cell_count=8),
    )
    report = release(new, catalogue, regional=NOTHING_REGIONAL)
    assert report.failed
    assert "Failed, so it is not published" in (new / "qa.md").read_text(encoding="utf-8")
    assert latest(tmp_path) == {"version": old.name}


def test_a_failed_check_of_the_published_version_does_not_claim_it_is_unpublished(
    tmp_path, catalogue
):
    folder = spoil(write_sample(tmp_path), manifest=lambda m: m.update(cell_count=8))
    report = check(folder, catalogue, regional=NOTHING_REGIONAL)
    assert report.failed and report.published
    text = report.markdown()
    assert "**Failed.** This version is already published" in text
    assert "not published" not in text
    assert latest(tmp_path) == {"version": folder.name}  # checking never moves the pointer


def test_a_version_that_is_not_published_says_so_when_it_fails(tmp_path, catalogue):
    write_sample(tmp_path)
    folder = spoil(
        write_sample(tmp_path, columns={"diversity": [0.1] * 6 + [0.9]}, publish=False),
        manifest=lambda m: m.update(cell_count=8),
    )
    report = check(folder, catalogue, regional=NOTHING_REGIONAL)
    assert report.failed and not report.published
    assert "**Failed, so it is not published.**" in report.markdown()


def test_a_bundle_is_compared_with_the_one_it_replaces(tmp_path, catalogue):
    old = write_sample(tmp_path)
    new = write_sample(
        tmp_path, columns={"station-proximity": [12, 13, 14, 15, 16, 17, 18]}, publish=False
    )
    report = release(new, catalogue, regional=NOTHING_REGIONAL)
    assert report.previous == old.name
    assert report.changes and "Walk to the nearest station: the median moved" in report.changes[0]
    assert latest(tmp_path) == {"version": new.name, "previous": old.name}


def test_the_bundle_that_is_already_latest_is_compared_with_the_one_it_replaced(
    tmp_path, catalogue
):
    old = write_sample(tmp_path)
    new = write_sample(tmp_path, columns={"station-proximity": [12, 13, 14, 15, 16, 17, 18]})
    again = release(new, catalogue, regional=NOTHING_REGIONAL)
    assert again.previous == old.name and again.changes
    assert latest(tmp_path) == {"version": new.name, "previous": old.name}


def test_the_first_bundle_has_nothing_to_compare_with(tmp_path, catalogue):
    folder = write_sample(tmp_path, publish=False)
    assert release(folder, catalogue, regional=NOTHING_REGIONAL).changes is None

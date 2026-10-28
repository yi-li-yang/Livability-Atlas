import json

import pyarrow.parquet as pq
import pytest

from atlas.catalogue.load import load_catalogue
from atlas.paths import CATALOGUE_DIR
from atlas.publish.bundle import write_bundle
from atlas.publish.manifest import Manifest

CELLS = ["891fa5a0003ffff", "891fa5a0007ffff", "891fa5a000bffff"]


@pytest.fixture(scope="module")
def catalogue():
    return load_catalogue(CATALOGUE_DIR)


def build(catalogue, tmp_path, bands=("6b", "2", None)):
    return write_bundle(
        catalogue,
        region_id="london",
        cells=CELLS,
        columns={"service-level": list(bands)},
        out_dir=tmp_path,
    )


def test_a_bundle_holds_a_manifest_and_a_table_of_cells(catalogue, tmp_path):
    bundle = build(catalogue, tmp_path)
    assert sorted(p.name for p in bundle.iterdir()) == ["cells.parquet", "manifest.json"]
    table = pq.read_table(bundle / "cells.parquet")
    assert table.column_names == ["cell", "service_level"]
    assert table["cell"].to_pylist() == CELLS
    assert table["service_level"].to_pylist() == ["6b", "2", None]


def test_the_manifest_describes_the_region_the_grid_and_the_indicators(catalogue, tmp_path):
    bundle = build(catalogue, tmp_path)
    manifest = Manifest.model_validate_json((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert manifest.region.id == "london"
    assert manifest.grid.resolution == 9
    assert manifest.cell_count == 3
    [indicator] = manifest.indicators
    assert indicator.id == "service-level"
    assert indicator.column == "service_level"
    assert indicator.curve is not None and indicator.curve.shape == "lookup"
    assert indicator.datasets == ["tfl-ptal"]
    assert indicator.evidence_type == "direct"


def test_the_manifest_carries_the_datasets_licences_and_attribution(catalogue, tmp_path):
    bundle = build(catalogue, tmp_path)
    manifest = Manifest.model_validate_json((bundle / "manifest.json").read_text(encoding="utf-8"))
    ids = {d.id for d in manifest.datasets}
    assert {"tfl-ptal", "ons-region-boundaries"} <= ids
    ptal = next(d for d in manifest.datasets if d.id == "tfl-ptal")
    assert ptal.licence == "OGL-UK-2.0" and "Transport for London" in ptal.attribution


def test_the_factor_tree_in_the_manifest_leads_to_each_indicator(catalogue, tmp_path):
    bundle = build(catalogue, tmp_path)
    manifest = Manifest.model_validate_json((bundle / "manifest.json").read_text(encoding="utf-8"))
    [top] = manifest.factors
    assert top.id == "transport" and top.default_weight == 3
    path = [top.id]
    node = top
    while node.children:
        [node] = node.children
        path.append(node.id)
    assert path[-1] == "service-level" and node.indicator == "service-level"


def test_the_same_input_gives_the_same_bytes(catalogue, tmp_path):
    first = build(catalogue, tmp_path / "a")
    second = build(catalogue, tmp_path / "b")
    assert first.name == second.name
    for name in ("manifest.json", "cells.parquet"):
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_a_change_to_the_data_changes_the_version(catalogue, tmp_path):
    one = build(catalogue, tmp_path)
    other = build(catalogue, tmp_path, bands=("6b", "3", None))
    assert one.name != other.name
    assert len(one.name) == 12 and int(one.name, 16) >= 0


def test_a_bundle_says_when_it_was_not_built_it_does_not_say_when(catalogue, tmp_path):
    text = (build(catalogue, tmp_path) / "manifest.json").read_text(encoding="utf-8")
    assert "built_at" not in text and "2026" not in json.loads(text).get("version", "")


def test_the_latest_version_is_recorded(catalogue, tmp_path):
    bundle = build(catalogue, tmp_path)
    latest = json.loads((tmp_path / "london" / "latest.json").read_text(encoding="utf-8"))
    assert latest == {"version": bundle.name}


def test_cells_must_be_sorted_and_unique(catalogue, tmp_path):
    with pytest.raises(ValueError, match="sorted"):
        write_bundle(
            catalogue,
            region_id="london",
            cells=["b", "a"],
            columns={"service-level": ["1a", "1b"]},
            out_dir=tmp_path,
        )


def test_a_column_needs_a_value_for_every_cell(catalogue, tmp_path):
    with pytest.raises(ValueError, match="3 cells"):
        write_bundle(
            catalogue,
            region_id="london",
            cells=CELLS,
            columns={"service-level": ["1a"]},
            out_dir=tmp_path,
        )


def test_an_indicator_the_catalogue_does_not_have_is_an_error(catalogue, tmp_path):
    with pytest.raises(KeyError):
        write_bundle(
            catalogue,
            region_id="london",
            cells=CELLS,
            columns={"nope": [1, 2, 3]},
            out_dir=tmp_path,
        )

import json

import pyarrow.parquet as pq
import pytest

from atlas.catalogue.load import load_catalogue
from atlas.paths import CATALOGUE_DIR
from atlas.publish.bundle import (
    Choice,
    Homes,
    Neighbourhoods,
    previous_version,
    publish_latest,
    published_version,
    write_bundle,
)
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


def test_a_bundle_can_be_written_without_being_published(catalogue, tmp_path):
    bundle = write_bundle(
        catalogue,
        region_id="london",
        cells=CELLS,
        columns={"service-level": ["6b", "2", None]},
        out_dir=tmp_path,
        publish=False,
    )
    assert (bundle / "cells.parquet").exists()
    assert not (tmp_path / "london" / "latest.json").exists()


def test_publishing_records_the_version_it_replaced(catalogue, tmp_path):
    one = build(catalogue, tmp_path)
    other = build(catalogue, tmp_path, bands=("6b", "3", None))
    latest = json.loads((tmp_path / "london" / "latest.json").read_text(encoding="utf-8"))
    assert latest == {"version": other.name, "previous": one.name}


def test_publishing_the_same_version_again_keeps_what_it_replaced(catalogue, tmp_path):
    one = build(catalogue, tmp_path)
    other = build(catalogue, tmp_path, bands=("6b", "3", None))
    again = build(catalogue, tmp_path, bands=("6b", "3", None))
    assert again.name == other.name
    latest = json.loads((tmp_path / "london" / "latest.json").read_text(encoding="utf-8"))
    assert latest == {"version": other.name, "previous": one.name}


def test_a_written_bundle_is_published_later_by_its_version(catalogue, tmp_path):
    one = build(catalogue, tmp_path)
    other = write_bundle(
        catalogue,
        region_id="london",
        cells=CELLS,
        columns={"service-level": ["6b", "3", None]},
        out_dir=tmp_path,
        publish=False,
    )
    publish_latest(tmp_path / "london", other.name)
    latest = json.loads((tmp_path / "london" / "latest.json").read_text(encoding="utf-8"))
    assert latest == {"version": other.name, "previous": one.name}


def test_nothing_is_replaced_before_anything_is_published(catalogue, tmp_path):
    bundle = write_bundle(
        catalogue,
        region_id="london",
        cells=CELLS,
        columns={"service-level": ["6b", "2", None]},
        out_dir=tmp_path,
        publish=False,
    )
    assert previous_version(tmp_path / "london", bundle.name) is None
    assert previous_version(tmp_path / "nowhere", bundle.name) is None


def test_publishing_a_new_version_replaces_the_latest_one(catalogue, tmp_path):
    one = build(catalogue, tmp_path)
    assert previous_version(tmp_path / "london", "0123456789ab") == one.name


def test_the_latest_version_replaced_the_one_before_it(catalogue, tmp_path):
    one = build(catalogue, tmp_path)
    other = build(catalogue, tmp_path, bands=("6b", "3", None))
    assert previous_version(tmp_path / "london", other.name) == one.name
    assert previous_version(tmp_path / "london", one.name) == other.name


def test_the_published_version_is_the_one_latest_names(catalogue, tmp_path):
    region = tmp_path / "london"
    assert published_version(region) is None
    one = build(catalogue, tmp_path)
    assert published_version(region) == one.name


@pytest.mark.parametrize("text", ["", "{", "[]", '{"previous": "x"}', '{"version": 3}', "null"])
def test_a_pointer_that_cannot_be_read_names_nothing(catalogue, tmp_path, text):
    one = build(catalogue, tmp_path)
    (tmp_path / "london" / "latest.json").write_text(text, encoding="utf-8")
    assert published_version(tmp_path / "london") is None
    assert previous_version(tmp_path / "london", one.name) is None
    publish_latest(tmp_path / "london", one.name)  # and publishing replaces it
    assert published_version(tmp_path / "london") == one.name


def test_the_first_version_published_replaced_nothing(catalogue, tmp_path):
    one = build(catalogue, tmp_path)
    assert previous_version(tmp_path / "london", one.name) is None


def test_only_a_written_version_can_be_published(catalogue, tmp_path):
    build(catalogue, tmp_path)
    with pytest.raises(ValueError, match="no bundle"):
        publish_latest(tmp_path / "london", "0123456789ab")


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


def choices():
    return {
        "faith": [
            Choice("hindu", "Hindu", "Religion", [4.0, None, 12.0]),
            Choice("sikh", "Sikh", "Religion", [9.0, 9.0, None]),
        ]
    }


def build_with_choices(catalogue, tmp_path):
    return write_bundle(
        catalogue,
        region_id="london",
        cells=CELLS,
        columns={"service-level": ["6b", "2", None]},
        choices=choices(),
        out_dir=tmp_path,
    )


def test_each_option_of_a_choice_has_a_column_named_by_the_indicator_and_the_option(
    catalogue, tmp_path
):
    bundle = build_with_choices(catalogue, tmp_path)
    table = pq.read_table(bundle / "cells.parquet")
    assert table.column_names == ["cell", "service_level", "faith__hindu", "faith__sikh"]
    assert table["faith__hindu"].to_pylist() == [4.0, None, 12.0]


def test_the_manifest_lists_the_options_of_a_choice_indicator(catalogue, tmp_path):
    bundle = build_with_choices(catalogue, tmp_path)
    manifest = Manifest.model_validate_json((bundle / "manifest.json").read_text(encoding="utf-8"))
    faith = next(i for i in manifest.indicators if i.id == "faith")
    assert faith.preference_type == "user-choice"
    assert faith.column == "faith"
    assert faith.options is not None
    assert [(o.id, o.name, o.group, o.column) for o in faith.options] == [
        ("hindu", "Hindu", "Religion", "faith__hindu"),
        ("sikh", "Sikh", "Religion", "faith__sikh"),
    ]
    plain = next(i for i in manifest.indicators if i.id == "service-level")
    assert plain.options is None


def test_a_choice_enters_the_factor_tree_like_any_other_indicator(catalogue, tmp_path):
    bundle = build_with_choices(catalogue, tmp_path)
    manifest = Manifest.model_validate_json((bundle / "manifest.json").read_text(encoding="utf-8"))
    ids: list[str] = []

    def walk(nodes):
        for node in nodes:
            ids.append(node.id)
            walk(node.children or [])

    walk(manifest.factors)
    assert "faith" in ids and "community-and-people" in ids


def test_an_indicator_cannot_be_both_plain_and_a_choice(catalogue, tmp_path):
    with pytest.raises(ValueError, match="faith"):
        write_bundle(
            catalogue,
            region_id="london",
            cells=CELLS,
            columns={"faith": [1.0, 2.0, 3.0]},
            choices=choices(),
            out_dir=tmp_path,
        )


def test_an_option_needs_a_value_for_every_cell(catalogue, tmp_path):
    with pytest.raises(ValueError, match="hindu"):
        write_bundle(
            catalogue,
            region_id="london",
            cells=CELLS,
            columns={},
            choices={"faith": [Choice("hindu", "Hindu", "Religion", [1.0])]},
            out_dir=tmp_path,
        )


def neighbourhoods():
    return Neighbourhoods(
        listing=[("Soho", "Westminster"), ("Fitzrovia", "Camden")],
        of_cell=[0, None, 1],
        datasets=["hoc-msoa-names", "ons-msoa-boundaries"],
    )


def test_the_neighbourhood_of_each_cell_is_a_column_that_points_into_the_manifests_list(
    catalogue, tmp_path
):
    bundle = write_bundle(
        catalogue,
        region_id="london",
        cells=CELLS,
        columns={"service-level": ["6b", "2", None]},
        neighbourhoods=neighbourhoods(),
        out_dir=tmp_path,
    )
    table = pq.read_table(bundle / "cells.parquet")
    assert table.column_names == ["cell", "neighbourhood", "service_level"]
    assert table["neighbourhood"].to_pylist() == [0, None, 1]
    manifest = Manifest.model_validate_json((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert manifest.neighbourhoods is not None
    assert [(n.name, n.area) for n in manifest.neighbourhoods] == [
        ("Soho", "Westminster"),
        ("Fitzrovia", "Camden"),
    ]


def test_the_datasets_of_the_names_are_credited(catalogue, tmp_path):
    bundle = write_bundle(
        catalogue,
        region_id="london",
        cells=CELLS,
        columns={"service-level": ["6b", "2", None]},
        neighbourhoods=neighbourhoods(),
        out_dir=tmp_path,
    )
    manifest = Manifest.model_validate_json((bundle / "manifest.json").read_text(encoding="utf-8"))
    credited = {d.id for d in manifest.datasets}
    assert {"hoc-msoa-names", "ons-msoa-boundaries", "tfl-ptal"} <= credited


def test_a_bundle_without_neighbourhoods_has_no_such_column_or_list(catalogue, tmp_path):
    bundle = build(catalogue, tmp_path)
    assert "neighbourhood" not in pq.read_table(bundle / "cells.parquet").column_names
    assert "neighbourhoods" not in json.loads(
        (bundle / "manifest.json").read_text(encoding="utf-8")
    )


def test_every_cell_needs_a_neighbourhood_entry(catalogue, tmp_path):
    with pytest.raises(ValueError, match="neighbourhood"):
        write_bundle(
            catalogue,
            region_id="london",
            cells=CELLS,
            columns={"service-level": ["6b", "2", None]},
            neighbourhoods=Neighbourhoods(
                listing=[("Soho", "Westminster")], of_cell=[0], datasets=[]
            ),
            out_dir=tmp_path,
        )


def homes():
    return Homes(of_cell=[250, 0, 3], minimum=10, datasets=["epc-domestic"])


def test_the_homes_of_each_cell_are_a_column_and_the_manifest_gives_the_minimum(
    catalogue, tmp_path
):
    bundle = write_bundle(
        catalogue,
        region_id="london",
        cells=CELLS,
        columns={"service-level": ["6b", "2", None]},
        homes=homes(),
        out_dir=tmp_path,
    )
    table = pq.read_table(bundle / "cells.parquet")
    assert table.column_names == ["cell", "homes", "service_level"]
    assert table["homes"].to_pylist() == [250, 0, 3]
    manifest = Manifest.model_validate_json((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert manifest.homes is not None
    assert (manifest.homes.column, manifest.homes.minimum) == ("homes", 10)
    assert "epc-domestic" in {d.id for d in manifest.datasets}


def test_a_bundle_without_homes_has_no_such_column_or_entry(catalogue, tmp_path):
    bundle = build(catalogue, tmp_path)
    assert "homes" not in pq.read_table(bundle / "cells.parquet").column_names
    assert "homes" not in json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))


def test_every_cell_needs_a_count_of_homes(catalogue, tmp_path):
    with pytest.raises(ValueError, match="homes"):
        write_bundle(
            catalogue,
            region_id="london",
            cells=CELLS,
            columns={"service-level": ["6b", "2", None]},
            homes=Homes(of_cell=[1, 2], minimum=10, datasets=[]),
            out_dir=tmp_path,
        )


def _ids(factors):
    for f in factors:
        yield f["id"]
        yield from _ids(f.get("children") or [])


def test_the_manifest_carries_the_presets_cut_to_its_factor_tree(catalogue, tmp_path):
    bundle = build(catalogue, tmp_path)
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    presets = {p["id"]: p for p in manifest["presets"]}
    assert sorted(presets) == sorted(catalogue.presets)
    tree = set(_ids(manifest["factors"]))
    indicators = {i["id"] for i in manifest["indicators"]}
    for preset in presets.values():
        assert preset["name"] and preset["description"]
        assert set(preset.get("weights", {})) <= tree
        assert set(preset.get("flipped", [])) <= indicators
    # the retiree's weight on Transport is kept; its nightlife, not in this bundle, is not
    assert presets["retiree"]["weights"]["transport"] == 4
    assert "flipped" not in presets["retiree"]


def test_a_manifest_limit_needs_exactly_one_bound():
    from pydantic import ValidationError

    from atlas.publish.manifest import ManifestLimit

    with pytest.raises(ValidationError):
        ManifestLimit.model_validate({"indicator": "x"})
    with pytest.raises(ValidationError):
        ManifestLimit.model_validate({"indicator": "x", "max": 1, "min": 0})
    assert ManifestLimit.model_validate({"indicator": "x", "in": ["a"]}).in_ == ["a"]


def test_a_presets_limit_is_written_as_the_web_app_reads_it():
    from atlas.catalogue.models import Limit, Preset
    from atlas.publish.bundle import manifest_presets

    preset = Preset(
        id="p",
        name="P",
        description="A preset.",
        weights={"transport": 5, "gone": 2},
        flipped=["density"],
        limits=[
            Limit.model_validate({"indicator": "service-level", "in": ["6a", "6b"]}),
            Limit(indicator="council-tax", max=2000),
            Limit(indicator="density", min=10),
        ],
    )
    [out] = manifest_presets(
        {"p": preset}, tree={"transport", "service-level"}, indicators={"service-level"}
    )
    dumped = out.model_dump(mode="json", exclude_none=True, by_alias=True)
    assert dumped == {
        "id": "p",
        "name": "P",
        "description": "A preset.",
        "weights": {"transport": 5},
        "limits": [{"indicator": "service-level", "in": ["6a", "6b"]}],
    }


def _travel(minute=7):
    import numpy as np

    from atlas.publish.bundle import Travel

    return Travel(
        stations=[("940GZZLUBXN", 51.4627, -0.1145), ("940GZZLUSKW", 51.4721, -0.1230)],
        cell_stations=[(0, 0, 3.25), (0, 1, 12.0), (2, 1, 5.5)],
        matrix=np.array([[0, minute], [minute + 1, 0]], dtype=np.uint16),
        postcodes=[("SW98HE", 51.4627, -0.1145), ("SW21AA", 51.4612, -0.1156)],
    )


def build_with_travel(catalogue, tmp_path, travel):
    return write_bundle(
        catalogue,
        region_id="london",
        cells=CELLS,
        columns={"service-level": ["6b", "2", None]},
        travel=travel,
        out_dir=tmp_path,
    )


def test_a_bundle_can_carry_the_travel_files_that_the_manifest_names(catalogue, tmp_path):
    bundle = build_with_travel(catalogue, tmp_path, _travel())
    assert sorted(p.name for p in bundle.iterdir()) == [
        "cell-stations.parquet",
        "cells.parquet",
        "manifest.json",
        "postcodes.parquet",
        "station-matrix.parquet",
        "stations.parquet",
    ]
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    travel = manifest["travel"]
    assert travel["indicator"] == "travel-time-to-places"
    assert travel["stations"] == "stations.parquet"
    assert travel["cell_stations"] == "cell-stations.parquet"
    assert travel["matrix"] == "station-matrix.parquet"
    assert travel["station_count"] == 2
    assert travel["unreachable"] == 65535
    stations = pq.read_table(bundle / "stations.parquet").to_pydict()
    assert stations["stop"] == ["940GZZLUBXN", "940GZZLUSKW"]
    links = pq.read_table(bundle / "cell-stations.parquet").to_pydict()
    assert links == {"cell": [0, 0, 2], "station": [0, 1, 1], "minutes": [3.25, 12.0, 5.5]}
    matrix = pq.read_table(bundle / "station-matrix.parquet").to_pydict()
    assert matrix["minutes"] == [0, 7, 8, 0]  # row by row: from each station to each
    assert travel["postcodes"] == "postcodes.parquet"
    postcodes = pq.read_table(bundle / "postcodes.parquet").to_pydict()
    assert postcodes["postcode"] == ["SW21AA", "SW98HE"]  # sorted, for the lookup
    assert postcodes["lat"] == pytest.approx([51.4612, 51.4627], abs=1e-5)


def test_the_travel_files_are_part_of_the_version(catalogue, tmp_path):
    a = build_with_travel(catalogue, tmp_path / "a", _travel(7))
    b = build_with_travel(catalogue, tmp_path / "b", _travel(7))
    c = build_with_travel(catalogue, tmp_path / "c", _travel(9))
    assert a.name == b.name
    assert a.name != c.name


def test_the_travel_files_must_fit_the_cells_and_stations(catalogue, tmp_path):
    import numpy as np

    from atlas.publish.bundle import Travel

    stations = [("a", 51.0, 0.0)]
    with pytest.raises(ValueError, match="square"):
        build_with_travel(
            catalogue,
            tmp_path,
            Travel(stations, [], np.zeros((2, 2), dtype=np.uint16)),
        )
    with pytest.raises(ValueError, match="cell"):
        build_with_travel(
            catalogue,
            tmp_path,
            Travel(stations, [(9, 0, 1.0)], np.zeros((1, 1), dtype=np.uint16)),
        )
    with pytest.raises(ValueError, match="station"):
        build_with_travel(
            catalogue,
            tmp_path,
            Travel(stations, [(0, 3, 1.0)], np.zeros((1, 1), dtype=np.uint16)),
        )
    with pytest.raises(ValueError, match="order of the cells"):
        build_with_travel(
            catalogue,
            tmp_path,
            Travel(stations, [(2, 0, 1.0), (0, 0, 1.0)], np.zeros((1, 1), dtype=np.uint16)),
        )

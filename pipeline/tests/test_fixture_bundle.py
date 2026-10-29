"""The data bundle that the web app's tests load is kept in the repository, so it can go stale.

This checks it against the current manifest model. If it fails, the manifest changed: regenerate
the fixture with `uv run --project pipeline python web/e2e/fixtures/make_fixture.py`.
"""

import json

import pyarrow.parquet as pq

from atlas.paths import REPO_ROOT
from atlas.publish.manifest import Manifest

BUNDLES = REPO_ROOT / "web" / "e2e" / "fixtures" / "bundles" / "london"


def test_the_fixture_bundle_is_valid_under_the_current_manifest_model():
    version = json.loads((BUNDLES / "latest.json").read_text(encoding="utf-8"))["version"]
    manifest = Manifest.model_validate_json(
        (BUNDLES / version / "manifest.json").read_text(encoding="utf-8")
    )
    table = pq.read_table(BUNDLES / version / "cells.parquet")
    assert manifest.version == version
    assert manifest.cell_count == table.num_rows
    expected = [
        column
        for i in manifest.indicators
        for column in ([o.column for o in i.options] if i.options else [i.column])
    ]
    named = ["neighbourhood"] if manifest.neighbourhoods else []
    assert table.column_names == ["cell", *named, *expected]

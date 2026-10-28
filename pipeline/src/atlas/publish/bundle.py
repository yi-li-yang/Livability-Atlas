"""Writes a region's data bundle: `manifest.json` and `cells.parquet`.

The bundle lives in `<out_dir>/<region>/<version>/`, and `<out_dir>/<region>/latest.json` names the
newest version. The version is a hash of the content, so the same data always gives the same
bundle, byte for byte.
"""

import hashlib
import io
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from atlas.catalogue.load import Catalogue
from atlas.catalogue.models import Factor
from atlas.publish.manifest import (
    Manifest,
    ManifestDataset,
    ManifestFactor,
    ManifestIndicator,
    ManifestRegion,
)


def _column(indicator_id: str) -> str:
    return indicator_id.replace("-", "_")


def _find(nodes: Sequence[Factor], indicator_id: str) -> Factor | None:
    for node in nodes:
        if node.children is None:
            if node.id == indicator_id:
                return node
        elif (found := _find(node.children, indicator_id)) is not None:
            return found
    return None


def _prune(node: Factor, wanted: set[str]) -> ManifestFactor | None:
    """The part of the factor tree that leads to the indicators in `wanted`."""
    if node.children is None:
        if node.id not in wanted:
            return None
        return ManifestFactor(
            id=node.id, name=node.name, default_weight=node.default_weight, indicator=node.id
        )
    kept = [child for c in node.children if (child := _prune(c, wanted)) is not None]
    if not kept:
        return None
    return ManifestFactor(
        id=node.id, name=node.name, default_weight=node.default_weight, children=kept
    )


def _manifest(
    catalogue: Catalogue, region_id: str, cell_count: int, indicator_ids: list[str]
) -> Manifest:
    region = catalogue.regions[region_id]
    leaves = {}
    for indicator_id in indicator_ids:
        leaf = _find(catalogue.factors.factors, indicator_id)
        if leaf is None:
            raise KeyError(f"the catalogue has no measured indicator {indicator_id}")
        leaves[indicator_id] = leaf
    indicators = [
        ManifestIndicator(
            id=i,
            name=leaf.name,
            column=_column(i),
            unit=leaf.unit or "",
            evidence_type=leaf.evidence_type,
            preference_type=leaf.preference_type,  # type: ignore[arg-type]
            curve=leaf.curve,
            datasets=list(leaf.datasets or []),
        )
        for i, leaf in leaves.items()
    ]
    used = {d for leaf in leaves.values() for d in leaf.datasets or []} | {region.boundary.dataset}
    datasets = [
        ManifestDataset(
            id=d.id,
            name=d.name,
            publisher=d.publisher,
            url=d.url,
            licence=d.licence,
            attribution=d.attribution or "",
            date=str(d.date),
        )
        for d in sorted(catalogue.datasets.datasets, key=lambda d: d.id)
        if d.id in used
    ]
    wanted = set(indicator_ids)
    factors = [top for f in catalogue.factors.factors if (top := _prune(f, wanted)) is not None]
    return Manifest(
        version="",
        region=ManifestRegion(id=region.id, name=region.name),
        grid=region.grid,
        cell_count=cell_count,
        factors=factors,
        indicators=indicators,
        datasets=datasets,
    )


def _json(manifest: Manifest) -> str:
    return (
        json.dumps(
            manifest.model_dump(mode="json", exclude_none=True), indent=2, ensure_ascii=False
        )
        + "\n"
    )


def write_bundle(
    catalogue: Catalogue,
    *,
    region_id: str,
    cells: Sequence[str],
    columns: dict[str, Sequence[Any]],
    out_dir: Path,
) -> Path:
    """Writes the bundle and returns its folder. `columns` maps indicator ids to raw values."""
    if list(cells) != sorted(set(cells)):
        raise ValueError("cells must be sorted and unique")
    for indicator_id, values in columns.items():
        if len(values) != len(cells):
            raise ValueError(f"{indicator_id} has {len(values)} values for {len(cells)} cells")
    manifest = _manifest(catalogue, region_id, len(cells), list(columns))

    table = pa.table(
        {
            "cell": pa.array(list(cells), pa.string()),
            **{_column(i): pa.array(list(v)) for i, v in columns.items()},
        }
    )
    buffer = io.BytesIO()
    pq.write_table(table, buffer, compression="zstd")
    parquet = buffer.getvalue()

    digest = hashlib.sha256(parquet + _json(manifest).encode("utf-8")).hexdigest()[:12]
    manifest = manifest.model_copy(update={"version": digest})
    bundle = out_dir / region_id / digest
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "cells.parquet").write_bytes(parquet)
    (bundle / "manifest.json").write_text(_json(manifest), encoding="utf-8", newline="\n")
    (out_dir / region_id / "latest.json").write_text(
        json.dumps({"version": digest}) + "\n", encoding="utf-8", newline="\n"
    )
    return bundle

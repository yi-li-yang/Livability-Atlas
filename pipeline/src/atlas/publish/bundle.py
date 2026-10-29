"""Writes a region's data bundle: `manifest.json` and `cells.parquet`.

The bundle lives in `<out_dir>/<region>/<version>/`, and `<out_dir>/<region>/latest.json` names the
newest version. The version is a hash of the content, so the same data always gives the same
bundle, byte for byte.
"""

import hashlib
import io
import json
from collections.abc import Sequence
from dataclasses import dataclass
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
    ManifestNeighbourhood,
    ManifestOption,
    ManifestRegion,
)


@dataclass(frozen=True)
class Choice:
    """One option of a choice indicator and its raw value in each cell, such as the walking
    minutes to the nearest place of worship of one faith."""

    id: str
    name: str
    group: str | None
    values: Sequence[Any]


@dataclass(frozen=True)
class Neighbourhoods:
    """The named areas that cells belong to: the list, for each cell the position of its area in the
    list (None where it has none), and the datasets to credit for the names and the boundaries."""

    listing: Sequence[tuple[str, str]]  # (name, local authority)
    of_cell: Sequence[int | None]
    datasets: Sequence[str]


def _column(indicator_id: str) -> str:
    return indicator_id.replace("-", "_")


def _option_column(indicator_id: str, option_id: str) -> str:
    return f"{_column(indicator_id)}__{_column(option_id)}"


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
    catalogue: Catalogue,
    region_id: str,
    cell_count: int,
    indicator_ids: list[str],
    choices: dict[str, list[Choice]],
    neighbourhoods: Neighbourhoods | None = None,
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
            options=[
                ManifestOption(id=o.id, name=o.name, group=o.group, column=_option_column(i, o.id))
                for o in choices[i]
            ]
            if i in choices
            else None,
        )
        for i, leaf in leaves.items()
    ]
    used = {d for leaf in leaves.values() for d in leaf.datasets or []} | {region.boundary.dataset}
    if neighbourhoods is not None:
        used |= set(neighbourhoods.datasets)
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
        neighbourhoods=[ManifestNeighbourhood(name=n, area=a) for n, a in neighbourhoods.listing]
        if neighbourhoods is not None
        else None,
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
    choices: dict[str, list[Choice]] | None = None,
    neighbourhoods: Neighbourhoods | None = None,
    out_dir: Path,
) -> Path:
    """Writes the bundle and returns its folder. `columns` maps indicator ids to raw values, and
    `choices` maps the ids of choice indicators to their options, each with raw values."""
    choices = choices or {}
    if neighbourhoods is not None:
        if len(neighbourhoods.of_cell) != len(cells):
            raise ValueError(
                f"neighbourhoods has {len(neighbourhoods.of_cell)} entries for {len(cells)} cells"
            )
        if any(
            i is not None and not 0 <= i < len(neighbourhoods.listing)
            for i in neighbourhoods.of_cell
        ):
            raise ValueError("a cell's neighbourhood is not in the neighbourhood list")
    for indicator_id, options in choices.items():
        if indicator_id in columns:
            raise ValueError(f"{indicator_id} is a choice, so it cannot also have a plain column")
        for option in options:
            if len(option.values) != len(cells):
                raise ValueError(
                    f"{indicator_id} option {option.id} has {len(option.values)} values "
                    f"for {len(cells)} cells"
                )
    if list(cells) != sorted(set(cells)):
        raise ValueError("cells must be sorted and unique")
    for indicator_id, values in columns.items():
        if len(values) != len(cells):
            raise ValueError(f"{indicator_id} has {len(values)} values for {len(cells)} cells")
    manifest = _manifest(
        catalogue, region_id, len(cells), [*columns, *choices], choices, neighbourhoods
    )

    table = pa.table(
        {
            "cell": pa.array(list(cells), pa.string()),
            **(
                {"neighbourhood": pa.array(list(neighbourhoods.of_cell), pa.int32())}
                if neighbourhoods is not None
                else {}
            ),
            **{_column(i): pa.array(list(v)) for i, v in columns.items()},
            **{
                _option_column(i, o.id): pa.array(list(o.values), pa.float64())
                for i, options in choices.items()
                for o in options
            },
        }
    )
    buffer = io.BytesIO()
    pq.write_table(table, buffer, compression="snappy")
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

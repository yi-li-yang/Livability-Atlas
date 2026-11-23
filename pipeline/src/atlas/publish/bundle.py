"""Writes a region's data bundle: `manifest.json` and `cells.parquet`.

The bundle lives in `<out_dir>/<region>/<version>/`, and `<out_dir>/<region>/latest.json` names the
newest published version. The version is a hash of the content, so the same data always gives the
same bundle, byte for byte. The QA report (`qa.md`) is written beside them afterwards and is not
part of the hash.
"""

import hashlib
import io
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from atlas.catalogue.load import Catalogue
from atlas.catalogue.models import Factor, Preset
from atlas.indicators.station_matrix import STREET_FACTOR, UNREACHABLE, WALK_METRES_A_MINUTE
from atlas.publish.manifest import (
    Manifest,
    ManifestDataset,
    ManifestFactor,
    ManifestHomes,
    ManifestIndicator,
    ManifestLimit,
    ManifestNeighbourhood,
    ManifestOption,
    ManifestPreset,
    ManifestRegion,
    ManifestTravel,
)


@dataclass(frozen=True)
class Travel:
    """What the travel estimate to a user's places needs: the stations (stop id, latitude,
    longitude), each cell's stations within a walk (cell position, station position, minutes) and
    the minutes from each station to each (a square array of unsigned 16-bit whole minutes)."""

    stations: Sequence[tuple[str, float, float]]
    cell_stations: Sequence[tuple[int, int, float]]
    matrix: np.ndarray
    indicator: str = "travel-time-to-places"
    reach_minutes: float = 40.0
    postcodes: Sequence[tuple[str, float, float]] = ()


TRAVEL_FILES = ("stations.parquet", "cell-stations.parquet", "station-matrix.parquet")
POSTCODES_FILE = "postcodes.parquet"


def _parquet(table: pa.Table) -> bytes:
    buffer = io.BytesIO()
    pq.write_table(table, buffer, compression="snappy")
    return buffer.getvalue()


def _travel_files(travel: Travel, cell_count: int) -> dict[str, bytes]:
    """The three files of the travel estimate, by name, after checking that they fit together."""
    n = len(travel.stations)
    if travel.matrix.shape != (n, n):
        raise ValueError(f"the matrix must be square, {n} by {n}, for {n} stations")
    previous = -1
    for cell, station, _ in travel.cell_stations:
        # The web app reads each cell's stations as one run, in the order of the cells.
        if cell < previous:
            raise ValueError(
                f"the links must be in the order of the cells, and cell {cell} is after {previous}"
            )
        previous = cell
        if not 0 <= cell < cell_count:
            raise ValueError(f"cell {cell} is not one of the {cell_count} cells")
        if not 0 <= station < n:
            raise ValueError(f"station {station} is not one of the {n} stations")
    stations = pa.table(
        {
            "stop": pa.array([s for s, _, _ in travel.stations], pa.string()),
            "lat": pa.array([lat for _, lat, _ in travel.stations], pa.float64()),
            "lng": pa.array([lng for _, _, lng in travel.stations], pa.float64()),
        }
    )
    links = pa.table(
        {
            "cell": pa.array([c for c, _, _ in travel.cell_stations], pa.int32()),
            "station": pa.array([s for _, s, _ in travel.cell_stations], pa.int32()),
            "minutes": pa.array([m for _, _, m in travel.cell_stations], pa.float64()),
        }
    )
    matrix = pa.table(
        {"minutes": pa.array(travel.matrix.astype(np.uint16).ravel(order="C"), pa.uint16())}
    )
    files: dict[str, bytes] = dict(
        zip(TRAVEL_FILES, (_parquet(stations), _parquet(links), _parquet(matrix)), strict=True)
    )
    if travel.postcodes:
        ordered = sorted(travel.postcodes)
        files[POSTCODES_FILE] = _parquet(
            pa.table(
                {
                    "postcode": pa.array([p for p, _, _ in ordered], pa.string()),
                    # A float32 holds a London latitude to about half a metre.
                    "lat": pa.array([lat for _, lat, _ in ordered], pa.float32()),
                    "lng": pa.array([lng for _, _, lng in ordered], pa.float32()),
                }
            )
        )
    return files


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


@dataclass(frozen=True)
class Homes:
    """The number of homes in each cell, the fewest that make a cell a place where people live
    (D22), and the datasets to credit for the count."""

    of_cell: Sequence[int]
    minimum: int
    datasets: Sequence[str]


HOMES_COLUMN = "homes"


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


def manifest_presets(
    presets: dict[str, Preset], *, tree: set[str], indicators: set[str]
) -> list[ManifestPreset]:
    """The presets, by id, cut to a bundle: a weight on a factor that the bundle's tree lacks, and a
    direction or a limit on an indicator that it lacks, are left out, so the app reads only what
    it can show. An empty part is left out too."""
    out = []
    for preset_id in sorted(presets):
        preset = presets[preset_id]
        weights = {k: v for k, v in preset.weights.items() if k in tree}
        flipped = [i for i in preset.flipped if i in indicators]
        limits = [
            ManifestLimit.model_validate(
                {"indicator": limit.indicator, "max": limit.max, "min": limit.min, "in": limit.in_}
            )
            for limit in preset.limits
            if limit.indicator in indicators
        ]
        out.append(
            ManifestPreset(
                id=preset.id,
                name=preset.name,
                description=preset.description,
                weights=weights or None,
                flipped=flipped or None,
                limits=limits or None,
            )
        )
    return out


def _tree_ids(factors: Sequence[ManifestFactor]) -> set[str]:
    return {i for f in factors for i in (f.id, *_tree_ids(f.children or []))}


def _manifest(
    catalogue: Catalogue,
    region_id: str,
    cell_count: int,
    indicator_ids: list[str],
    choices: dict[str, list[Choice]],
    neighbourhoods: Neighbourhoods | None = None,
    homes: Homes | None = None,
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
    if homes is not None:
        used |= set(homes.datasets)
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
        homes=ManifestHomes(column=HOMES_COLUMN, minimum=homes.minimum)
        if homes is not None
        else None,
        presets=manifest_presets(
            catalogue.presets, tree=_tree_ids(factors), indicators=set(indicator_ids)
        )
        or None,
    )


def _json(manifest: Manifest) -> str:
    return (
        json.dumps(
            manifest.model_dump(mode="json", exclude_none=True, by_alias=True),
            indent=2,
            ensure_ascii=False,
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
    homes: Homes | None = None,
    travel: Travel | None = None,
    out_dir: Path,
    publish: bool = True,
) -> Path:
    """Writes the bundle and returns its folder. `columns` maps indicator ids to raw values, and
    `choices` maps the ids of choice indicators to their options, each with raw values. With
    `publish` false the bundle is written but `latest.json` is left alone, for the QA report to
    check it first (`publish_latest` moves the pointer afterwards)."""
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
    if homes is not None and len(homes.of_cell) != len(cells):
        raise ValueError(f"homes has {len(homes.of_cell)} counts for {len(cells)} cells")
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
        catalogue, region_id, len(cells), [*columns, *choices], choices, neighbourhoods, homes
    )

    table = pa.table(
        {
            "cell": pa.array(list(cells), pa.string()),
            **(
                {"neighbourhood": pa.array(list(neighbourhoods.of_cell), pa.int32())}
                if neighbourhoods is not None
                else {}
            ),
            **(
                {HOMES_COLUMN: pa.array(list(homes.of_cell), pa.int32())}
                if homes is not None
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
    parquet = _parquet(table)
    extra = _travel_files(travel, len(cells)) if travel is not None else {}
    if travel is not None:
        manifest = manifest.model_copy(
            update={
                "travel": ManifestTravel(
                    indicator=travel.indicator,
                    stations=TRAVEL_FILES[0],
                    cell_stations=TRAVEL_FILES[1],
                    matrix=TRAVEL_FILES[2],
                    station_count=len(travel.stations),
                    unreachable=UNREACHABLE,
                    reach_minutes=travel.reach_minutes,
                    walk_metres_a_minute=WALK_METRES_A_MINUTE,
                    street_factor=STREET_FACTOR,
                    postcodes=POSTCODES_FILE if travel.postcodes else None,
                )
            }
        )

    # The version covers every file, in a fixed order, so a rebuild gives the same bytes.
    content = parquet + b"".join(extra[name] for name in sorted(extra))
    digest = hashlib.sha256(content + _json(manifest).encode("utf-8")).hexdigest()[:12]
    manifest = manifest.model_copy(update={"version": digest})
    bundle = out_dir / region_id / digest
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "cells.parquet").write_bytes(parquet)
    for name, data in extra.items():
        (bundle / name).write_bytes(data)
    (bundle / "manifest.json").write_text(_json(manifest), encoding="utf-8", newline="\n")
    if publish:
        publish_latest(out_dir / region_id, digest)
    return bundle


def publish_latest(region_dir: Path, version: str) -> None:
    """Points `latest.json`, which the web app follows, at a written version. It also records the
    version it replaced as `previous`, which the QA report compares against; publishing the
    version that is already the latest keeps the `previous` it had."""
    if not (region_dir / version / "manifest.json").exists():
        raise ValueError(f"there is no bundle {version} in {region_dir}")
    record = {"version": version}
    replaced = previous_version(region_dir, version)
    if replaced is not None:
        record["previous"] = replaced
    (region_dir / "latest.json").write_text(
        json.dumps(record) + "\n", encoding="utf-8", newline="\n"
    )


def _pointer(region_dir: Path) -> dict[str, Any] | None:
    """What `latest.json` holds, or None where it is missing or cannot be read."""
    try:
        record = json.loads((region_dir / "latest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(record, dict) or not isinstance(record.get("version"), str):
        return None
    return record


def published_version(region_dir: Path) -> str | None:
    """The version that `latest.json` names, or None where there is none."""
    record = _pointer(region_dir)
    return record["version"] if record is not None else None


def previous_version(region_dir: Path, version: str) -> str | None:
    """The version that publishing `version` replaces: the latest one now, or if `version` is the
    latest already, the one it replaced. None where there is none."""
    record = _pointer(region_dir)
    if record is None:
        return None
    replaced = record.get("previous") if record["version"] == version else record["version"]
    return replaced if isinstance(replaced, str) else None

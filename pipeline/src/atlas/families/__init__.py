"""Indicator families: the way a measured indicator joins a region's bundle.

A family is one module of this package that builds the columns of one dataset or one indicator
family (`crime`, `energy`, `collisions`). It names a `FAMILY` at the top level of the module:

    FAMILY = Family("energy", columns, built_from={"energy-efficiency": ("epc-domestic",)})

`columns(ctx)` returns the raw value of each indicator it builds for every cell of the region, in
the order of `ctx.cells`, keyed by the indicator's id in `catalogue/factors.yaml`. A family that
builds a user-choice indicator also gives `choices(ctx)`. `built_from` names, for an indicator
whose dataset has no licence for commercial use (D07), the datasets it is built from, so that a
commercial build leaves it out. `atlas build` runs every family it finds, after the indicators
that `build.py` still builds itself, and it needs no change to `build.py` or any other family.

A family reads from `ctx` what it needs (the postcodes, the street network, the output areas) and
fetches its own datasets, each cached in `data/raw/`. Its own tests call it with a small
synthetic context, and the full synthetic build in `test_build.py` runs no families.
"""

import importlib
import pkgutil
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd

from atlas.catalogue.models import Region
from atlas.datasets.countries.gb import bres, census_residents, ons_lsoa, output_areas
from atlas.datasets.world import overture
from atlas.indicators import crime
from atlas.indicators import places as place_pool
from atlas.publish.bundle import Choice
from atlas.spatial import walking
from atlas.spatial.grid import bounds_bng, cell_centres_bng, lonlat_box


@dataclass
class Context:
    """What a family may read: the region, its cells (in the order of the columns it returns), the
    data folder, the postcodes of Code-Point Open and the walking network."""

    region_id: str
    region: Region
    cells: list[str]
    data_dir: Path
    postcodes: pd.DataFrame
    network: walking.Network

    @property
    def resolution(self) -> int:
        return self.region.grid.resolution

    def postcodes_inside(self, margin: float = 2000) -> pd.DataFrame:
        """The postcodes (`Easting` and `Northing`, indexed by the normalised postcode) within
        `margin` metres of the cells' bounding box."""
        x0, y0, x1, y1 = bounds_bng(self.cells, margin=margin)
        east, north = self.postcodes["Easting"], self.postcodes["Northing"]
        return self.postcodes.loc[(east >= x0) & (east <= x1) & (north >= y0) & (north <= y1)]

    @cached_property
    def residents(self) -> pd.Series:
        """Each cell's usual residents (Census 2021), shared from the output areas by area."""
        counts = census_residents.read_residents(census_residents.fetch(self.data_dir))
        return crime.residents_by_cell(self.areas, counts, self.cells)

    @cached_property
    def workers(self) -> pd.Series:
        """Each cell's jobs (the Business Register and Employment Survey), shared from the 2011
        LSOAs by area."""
        lsoas = ons_lsoa.read_boundaries(
            ons_lsoa.fetch(self.data_dir, bounds_bng(self.cells, margin=2000))
        )
        return crime.workers_by_cell(lsoas, bres.read_jobs(bres.fetch(self.data_dir)), self.cells)

    @cached_property
    def people(self) -> pd.Series:
        """Residents and workers together: the people a rate of a harm to people is counted
        against."""
        return crime.people_present(self.residents, self.workers)

    @cached_property
    def overture(self) -> pd.DataFrame:
        """Every place Overture lists in the region (`lng`, `lat`, `name`, `category`)."""
        box = lonlat_box(self.cells, margin=0.05)
        return overture.read_places(overture.fetch(self.data_dir, self.region_id, box))

    def places_of(
        self, categories: Iterable[str] = (), suffixes: Iterable[str] = ()
    ) -> pd.DataFrame:
        """The places of Overture's categories (or categories that end as `suffixes` do), as a
        table with `Easting`, `Northing` and `name`."""
        return place_pool.located(self.overture, categories, suffixes)

    def walk_to_nearest(self, places: pd.DataFrame) -> list[float | None]:
        """The minutes on foot from each cell's centre to the nearest of `places`, along streets
        and paths. No value where there is no place, or no way to one."""
        if places.empty:
            return [None] * len(self.cells)
        found = np.column_stack([places["Easting"].to_numpy(), places["Northing"].to_numpy()])
        origins = cell_centres_bng(self.cells)
        minutes = self.network.minutes_to_nearest(places=found, origins=origins)
        return [None if np.isnan(m) else float(m) for m in minutes]

    def count_within(self, places: pd.DataFrame, minutes: float) -> list[int]:
        """The number of `places` within a walk of `minutes` of each cell's centre."""
        if places.empty:
            return [0] * len(self.cells)
        found = np.column_stack([places["Easting"].to_numpy(), places["Northing"].to_numpy()])
        reach = self.network.groups_within([found], cell_centres_bng(self.cells), minutes)[0]
        return [len(r) for r in reach]

    @cached_property
    def areas(self) -> gpd.GeoDataFrame:
        """The census output areas that cover the cells, with a 2 km margin."""
        path = output_areas.fetch(self.data_dir, bounds_bng(self.cells, margin=2000))
        return output_areas.read_boundaries(path)


@dataclass(frozen=True)
class Family:
    name: str
    columns: Callable[[Context], Mapping[str, Sequence[Any]]]
    choices: Callable[[Context], Mapping[str, list[Choice]]] | None = None
    built_from: Mapping[str, tuple[str, ...]] = field(default_factory=dict)


def discover(package: str = "atlas.families") -> list[Family]:
    """The `FAMILY` of every module of `package`, in the order of the modules' names."""
    root = importlib.import_module(package)
    found = []
    for module in sorted(pkgutil.iter_modules(root.__path__), key=lambda m: m.name):
        family = getattr(importlib.import_module(f"{package}.{module.name}"), "FAMILY", None)
        if isinstance(family, Family):
            found.append(family)
    return found


def run(
    found: Sequence[Family], ctx: Context
) -> tuple[dict[str, Sequence[Any]], dict[str, list[Choice]]]:
    """Builds every family's columns and choices. An indicator built by two families, or a column
    that is not one value for each cell, is an error."""
    columns: dict[str, Sequence[Any]] = {}
    choices: dict[str, list[Choice]] = {}
    made_by: dict[str, str] = {}
    for family in found:
        for indicator, values in family.columns(ctx).items():
            if indicator in made_by:
                raise ValueError(
                    f"{indicator} is built by both {made_by[indicator]} and {family.name}"
                )
            if len(values) != len(ctx.cells):
                raise ValueError(
                    f"{family.name} gave {len(values)} values for {indicator}, "
                    f"and the region has {len(ctx.cells)} cells"
                )
            made_by[indicator] = family.name
            columns[indicator] = values
        if family.choices is not None:
            for indicator, options in family.choices(ctx).items():
                if indicator in made_by:
                    raise ValueError(
                        f"{indicator} is built by both {made_by[indicator]} and {family.name}"
                    )
                made_by[indicator] = family.name
                choices[indicator] = options
    return columns, choices


def built_from(found: Sequence[Family]) -> dict[str, tuple[str, ...]]:
    """The datasets each indicator is built from, for the families that name them."""
    merged: dict[str, tuple[str, ...]] = {}
    for family in found:
        merged.update(family.built_from)
    return merged

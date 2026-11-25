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
import h3
import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray

from atlas.catalogue.models import Region
from atlas.datasets.countries.gb import (
    bres,
    census_residents,
    epc,
    ons_lsoa,
    ons_msoa,
    output_areas,
)
from atlas.datasets.world import overture
from atlas.indicators import crime, reach
from atlas.indicators import places as place_pool
from atlas.indicators.station_matrix import STREET_FACTOR, WALK_METRES_A_MINUTE
from atlas.publish.bundle import Choice, Travel
from atlas.spatial import walking
from atlas.spatial.grid import bounds_bng, cell_centres_bng, cells_at_bng, lonlat_box


@dataclass
class Context:
    """What a family may read: the region, its cells (in the order of the columns it returns), the
    data folder, the postcodes of Code-Point Open, the walking network, and the travel estimate's
    stations, cell-station links and station matrix (None for a region with no default places)."""

    region_id: str
    region: Region
    cells: list[str]
    data_dir: Path
    postcodes: pd.DataFrame
    network: walking.Network
    travel: Travel | None = None

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
    def homes(self) -> pd.DataFrame:
        """The region's homes with an energy certificate, one row each (see `epc.read_stock`), with
        the `cell` that holds their postcode's centre."""
        inside = self.postcodes_inside()
        homes = epc.stock(self.data_dir, self.region_id, set(inside.index))
        where = inside.reindex(pd.Index(homes["postcode"]))
        known = where["Easting"].notna().to_numpy()
        homes = homes.loc[known].reset_index(drop=True)
        homes["cell"] = cells_at_bng(
            where["Easting"].to_numpy(dtype=float)[known],
            where["Northing"].to_numpy(dtype=float)[known],
            self.resolution,
        )
        return homes

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

    def count_in_cells(self, places: pd.DataFrame) -> NDArray[np.float64]:
        """The number of `places` (with `Easting` and `Northing`) whose point lies in each cell, in
        the order of the cells; places outside the cells are not counted."""
        if places.empty:
            return np.zeros(len(self.cells))
        resolution = h3.get_resolution(self.cells[0])
        found = cells_at_bng(
            places["Easting"].to_numpy(), places["Northing"].to_numpy(), resolution
        )
        counts = pd.Series(found).value_counts()
        return counts.reindex(self.cells, fill_value=0).to_numpy(dtype=np.float64)

    def reached_by_transport(self, values: ArrayLike, minutes: float) -> list[float | None]:
        """For each cell, the sum of `values` (one for each cell) over the cells it reaches by
        public transport within `minutes`, itself included, by the travel estimate's stations, links
        and station matrix (`reach.within_minutes`). None for every cell where the region has no
        travel estimate."""
        if self.travel is None:
            return [None] * len(self.cells)
        links = np.asarray(self.travel.cell_stations, dtype=np.float64).reshape(-1, 3)
        centres = cell_centres_bng(self.cells)
        sums = reach.within_minutes(
            np.asarray(values, dtype=np.float64),
            centres[:, 0],
            centres[:, 1],
            links,
            self.travel.matrix,
            minutes=minutes,
            reach_minutes=self.travel.reach_minutes,
            walk_metres_a_minute=WALK_METRES_A_MINUTE,
            street_factor=STREET_FACTOR,
        )
        return [float(v) for v in sums]

    @cached_property
    def msoas(self) -> gpd.GeoDataFrame:
        """The neighbourhoods (2021 MSOAs) that cover the cells, with a 2 km margin."""
        path = ons_msoa.fetch(self.data_dir, bounds_bng(self.cells, margin=2000))
        return ons_msoa.read_boundaries(path)

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
    regions: tuple[str, ...] | None = None  # the regions it is for; None means every region


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
        if family.regions is not None and ctx.region_id not in family.regions:
            continue
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

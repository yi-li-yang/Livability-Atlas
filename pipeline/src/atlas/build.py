"""Builds a region's data bundle from raw downloads.

London so far has the service level (PTAL) and the five crime rates of Safety. Each indicator
that arrives later adds its columns here, through the factor recipe.
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.catalogue.load import load_catalogue
from atlas.datasets.cities.london import ptal
from atlas.datasets.countries.gb import (
    census_residents,
    ea_flood_risk,
    naptan,
    ons_regions,
    output_areas,
    police_uk,
)
from atlas.datasets.world import openstreetmap
from atlas.indicators import crime, flood, transport
from atlas.paths import CATALOGUE_DIR
from atlas.paths import data_dir as default_data_dir
from atlas.publish.bundle import write_bundle
from atlas.spatial import walking
from atlas.spatial.grid import boundary_from_geojson, bounds_bng, region_cells


def build_region(
    region_id: str, *, catalogue_dir: Path = CATALOGUE_DIR, data_dir: Path | None = None
) -> Path:
    """Fetches what the region needs (each download is cached), and builds its bundle.

    `data_dir` defaults to `ATLAS_DATA_DIR`, or `data/` in the repository.
    """
    data_dir = data_dir or default_data_dir()
    catalogue = load_catalogue(catalogue_dir)
    if region_id not in catalogue.regions:
        raise KeyError(f"the catalogue has no region {region_id}")
    region = catalogue.regions[region_id]

    boundary_path = ons_regions.fetch(region.boundary.name, data_dir)
    boundary = boundary_from_geojson(boundary_path, ons_regions.NAME_FIELD, region.boundary.name)
    cells = region_cells(boundary, region.grid.resolution)

    # A cell with no PTAL grid point has no value: outside TfL's grid, that is not band 0.
    bands = ptal.bands_by_cell(
        ptal.read_grid(ptal.fetch(data_dir)), region.grid.resolution
    ).reindex(cells)
    service_level = [None if pd.isna(band) else str(band) for band in bands]

    columns: dict[str, Sequence[Any]] = {"service-level": service_level}
    columns.update(_crime_columns(cells, region.grid.resolution, data_dir))
    columns.update(_flood_columns(cells, region.grid.resolution, data_dir))
    columns.update(_walking_columns(region_id, cells, data_dir))

    return write_bundle(
        catalogue,
        region_id=region_id,
        cells=cells,
        columns=columns,
        out_dir=data_dir / "published",
    )


def _crime_columns(cells: list[str], resolution: int, data_dir: Path) -> dict[str, list]:
    """Crimes per 1,000 residents for each of Safety's five crime indicators (spike S2)."""
    areas = output_areas.read_boundaries(
        output_areas.fetch(data_dir, bounds_bng(cells, margin=2000))
    )
    residents = crime.residents_by_cell(
        areas, census_residents.read_residents(census_residents.fetch(data_dir)), cells
    )
    archive, months = police_uk.fetch(data_dir)
    counts = crime.counts_by_cell(police_uk.read_crimes(archive, months), cells, resolution)
    return {
        indicator: [
            None if pd.isna(rate) else float(rate) for rate in crime.rates(n, residents, cells)
        ]
        for indicator, n in counts.items()
    }


# The catalogue's indicator for each flood risk service of the Environment Agency.
FLOOD_INDICATORS = {
    "rivers-and-sea": "river-and-sea-flooding",
    "surface-water": "surface-water-flooding",
}


def _flood_columns(cells: list[str], resolution: int, data_dir: Path) -> dict[str, Sequence[Any]]:
    """The share of each cell with a 1 in 100 chance of flooding in a year, from each service."""
    bounds = bounds_bng(cells, margin=500)
    columns: dict[str, Sequence[Any]] = {}
    for service, indicator in FLOOD_INDICATORS.items():
        mosaic = ea_flood_risk.fetch(data_dir, service, bounds)
        share = flood.share_at_risk(mosaic, cells, resolution)
        columns[indicator] = [None if pd.isna(v) else float(v) for v in share]
    return columns


def _walking_columns(region_id: str, cells: list[str], data_dir: Path) -> dict[str, Sequence[Any]]:
    """The indicators that are walks along streets (spike S6): minutes to the nearest station."""
    ways = walking.read_ways(openstreetmap.fetch(data_dir, region_id))
    network = walking.Network.from_ways(ways)
    stations = naptan.read_stations(naptan.fetch(data_dir))
    minutes = transport.station_minutes(network, stations, cells)
    return {"station-proximity": [None if pd.isna(m) else float(m) for m in minutes]}

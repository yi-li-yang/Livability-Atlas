"""Builds a region's data bundle from raw downloads.

Walking skeleton: one measured indicator, the service level (PTAL), for London. Each indicator
that arrives later adds its columns here, through the factor recipe.
"""

from pathlib import Path

import pandas as pd

from atlas.catalogue.load import load_catalogue
from atlas.datasets.cities.london import ptal
from atlas.datasets.countries.gb import ons_regions
from atlas.paths import CATALOGUE_DIR
from atlas.paths import data_dir as default_data_dir
from atlas.publish.bundle import write_bundle
from atlas.spatial.grid import boundary_from_geojson, region_cells


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

    return write_bundle(
        catalogue,
        region_id=region_id,
        cells=cells,
        columns={"service-level": service_level},
        out_dir=data_dir / "published",
    )

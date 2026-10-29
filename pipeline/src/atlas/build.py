"""Builds a region's data bundle from raw downloads.

London so far has the service level (PTAL), the crime rates of Safety, the flood shares of
Natural hazards, the walks to a station, a school, a GP practice and a park, the air quality, the
noise, the rent and council tax of the borough, the broadband and 5G, and the amenities: the walks
to a grocery, a pharmacy, a gym and a library, and the cafés, restaurants, cuisines and food
hygiene near each cell. Each indicator that arrives later adds its columns here, through the
factor recipe.
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.catalogue.load import Catalogue, load_catalogue
from atlas.datasets.cities.london import laei, ptal, tfl_lines
from atlas.datasets.countries.gb import (
    census_ethnic_group,
    census_religion,
    census_residents,
    code_point,
    defra_noise,
    ea_flood_risk,
    fsa,
    gias,
    mhclg_council_tax,
    naptan,
    nhs_gp,
    nhs_ods,
    ofcom,
    ons_local_authorities,
    ons_regions,
    ons_rents,
    os_open_greenspace,
    output_areas,
    police_uk,
)
from atlas.datasets.world import openstreetmap, overture
from atlas.indicators import (
    air_quality,
    amenities,
    community,
    connectivity,
    crime,
    education,
    environment,
    faith,
    flood,
    health,
    housing,
    noise,
    transport,
)
from atlas.indicators import places as place_pool
from atlas.paths import CATALOGUE_DIR
from atlas.paths import data_dir as default_data_dir
from atlas.publish.bundle import Choice, write_bundle
from atlas.spatial import walking
from atlas.spatial.grid import boundary_from_geojson, bounds_bng, lonlat_box, region_cells

# The measured indicators that are built from a dataset without a licence for commercial use (D07),
# with that dataset. The build is non-commercial and uses them; a commercial build leaves them out.
BUILT_FROM = {"no2": "laei", "pm25": "laei"}


def needs_commercial_licence(catalogue: Catalogue, indicators: Sequence[str]) -> list[str]:
    """The indicators among `indicators` that are built from a dataset without a licence for
    commercial use."""
    allowed = {d.id for d in catalogue.datasets.datasets if d.commercial_use}
    return [i for i in indicators if i in BUILT_FROM and BUILT_FROM[i] not in allowed]


def build_region(
    region_id: str,
    *,
    catalogue_dir: Path = CATALOGUE_DIR,
    data_dir: Path | None = None,
    commercial: bool = False,
) -> Path:
    """Fetches what the region needs (each download is cached), and builds its bundle.

    `data_dir` defaults to `ATLAS_DATA_DIR`, or `data/` in the repository. The build is
    non-commercial, and uses every dataset. A `commercial` build leaves out the indicators from
    datasets without a licence for commercial use (D07).
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
    postcodes = code_point.read_postcodes(code_point.fetch(data_dir))
    network = walking.Network.from_ways(walking.read_ways(openstreetmap.fetch(data_dir, region_id)))
    columns.update(_walking_columns(network, cells, data_dir, postcodes))
    columns.update(_amenity_columns(region_id, network, cells, data_dir))
    columns.update(_noise_columns(cells, region.grid.resolution, data_dir, postcodes))
    columns.update(_housing_columns(region_id, cells, data_dir))
    columns.update(_connectivity_columns(region_id, cells, data_dir))
    columns.update(_community_columns(cells, data_dir))
    columns.update(_air_columns(cells, region.grid.resolution, data_dir))
    if commercial:
        for indicator in needs_commercial_licence(catalogue, list(columns)):
            del columns[indicator]

    choices = _choices(region_id, network, cells, data_dir)
    return write_bundle(
        catalogue,
        region_id=region_id,
        cells=cells,
        columns=columns,
        choices=choices,
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


def _housing_columns(region_id: str, cells: list[str], data_dir: Path) -> dict[str, Sequence[Any]]:
    """Housing and cost, measured for a whole borough: the ONS's average monthly private rent and
    the council tax of a Band D home (with the Mayor's precept), which every cell takes from the
    borough that holds its centre."""
    boundaries = ons_local_authorities.fetch(data_dir, region_id)
    owner = ons_local_authorities.borough_of(boundaries, cells)
    rents = ons_rents.read_rents(ons_rents.fetch(data_dir))
    tax = mhclg_council_tax.read_band_d(mhclg_council_tax.fetch(data_dir))
    return {
        indicator: [
            None if pd.isna(v) else float(v) for v in housing.by_borough(values, owner, cells)
        ]
        for indicator, values in (("renting-cost", rents), ("council-tax", tax))
    }


def _connectivity_columns(
    region_id: str, cells: list[str], data_dir: Path
) -> dict[str, Sequence[Any]]:
    """Digital connectivity: the share of each cell's homes that can get gigabit-capable
    broadband (Ofcom, by census output area, shared by area), and the share of its borough's
    premises with 5G outdoors from all four networks (Ofcom, by local authority)."""
    fixed, mobile = ofcom.fetch(data_dir)
    areas = output_areas.read_boundaries(
        output_areas.fetch(data_dir, bounds_bng(cells, margin=2000))
    )
    gigabit = connectivity.gigabit_share(areas, ofcom.read_fixed(fixed), cells)
    owner = ons_local_authorities.borough_of(
        ons_local_authorities.fetch(data_dir, region_id), cells
    )
    five_g = housing.by_borough(ofcom.read_five_g(mobile), owner, cells)
    return {
        "gigabit-broadband": [None if pd.isna(v) else float(v) for v in gigabit],
        "5g-coverage": [None if pd.isna(v) else float(v) for v in five_g],
    }


def _choices(
    region_id: str, network: walking.Network, cells: list[str], data_dir: Path
) -> dict[str, list[Choice]]:
    """The user-choice indicators, with a column for each option (specs/2026-10-29-user-choice):
    Your community, the share of residents in each ethnic group and religion (Census 2021), and
    Faith, the minutes on foot to the nearest place of worship of each religion."""
    areas = output_areas.read_boundaries(
        output_areas.fetch(data_dir, bounds_bng(cells, margin=2000))
    )
    ethnic = community.shares(
        areas, census_ethnic_group.read_groups(census_ethnic_group.fetch(data_dir)), cells
    )
    religion = community.shares(
        areas, census_religion.read_groups(census_religion.fetch(data_dir)), cells
    )
    your_community = [
        Choice(id=i, name=n, group=g, values=_floats(v))
        for i, n, g, v in community.community_options(ethnic, religion)
    ]
    worship = faith.places_of_worship(openstreetmap.places(data_dir, region_id))
    minutes = faith.faith_minutes(network, worship, cells)
    return {
        "your-community": your_community,
        "faith": [
            Choice(id=r, name=faith.name_of(r), group="Religion", values=_floats(m))
            for r, m in minutes.items()
        ],
    }


def _floats(values: pd.Series) -> list[float | None]:
    return [None if pd.isna(v) else float(v) for v in values]


def _community_columns(cells: list[str], data_dir: Path) -> dict[str, Sequence[Any]]:
    """Community and people: how mixed each cell's residents are by ethnic group (Census 2021, by
    output area, shared by area)."""
    areas = output_areas.read_boundaries(
        output_areas.fetch(data_dir, bounds_bng(cells, margin=2000))
    )
    groups = census_ethnic_group.read_groups(census_ethnic_group.fetch(data_dir))
    index = community.diversity(areas, groups, cells)
    return {"diversity": [None if pd.isna(v) else float(v) for v in index]}


def _air_columns(cells: list[str], resolution: int, data_dir: Path) -> dict[str, Sequence[Any]]:
    """The mean modelled concentration over each cell of NO₂ and PM2.5, in 2022."""
    path = laei.fetch(data_dir)
    columns: dict[str, Sequence[Any]] = {}
    for indicator, pollutant in (("no2", "NO2"), ("pm25", "PM25")):
        mean = air_quality.mean_concentration(
            laei.read_concentrations(path, pollutant), cells, resolution
        )
        columns[indicator] = [None if pd.isna(v) else float(v) for v in mean]
    return columns


# The catalogue's indicator for each kind of noise of Defra's maps.
NOISE_INDICATORS = {"road": "road-noise", "rail": "rail-noise", "aircraft": "aircraft-noise"}


def _noise_columns(
    cells: list[str], resolution: int, data_dir: Path, postcodes: pd.DataFrame
) -> dict[str, Sequence[Any]]:
    """The mean daytime noise level in each cell from roads, railways and aircraft, taken at the
    cell's addresses (spike S5), which stand in as the postcodes of Code-Point Open."""
    west, south, east, north = bounds_bng(cells, margin=500)
    inside = postcodes["Easting"].between(west, east) & postcodes["Northing"].between(south, north)
    addresses = postcodes.loc[inside, ["Easting", "Northing"]].to_numpy(dtype=float)
    columns: dict[str, Sequence[Any]] = {}
    for kind, indicator in NOISE_INDICATORS.items():
        tiles = defra_noise.fetch(data_dir, kind, bounds_bng(cells))
        mean = noise.mean_level(defra_noise.read_levels(tiles), addresses, cells, resolution)
        columns[indicator] = [None if pd.isna(v) else float(v) for v in mean]
    return columns


def _amenity_columns(
    region_id: str, network: walking.Network, cells: list[str], data_dir: Path
) -> dict[str, Sequence[Any]]:
    """Daily amenities (spikes S6 and S8): the minutes on foot to the nearest grocery, pharmacy, gym
    and library, the cafés and restaurants and cuisines within a 10-minute walk, from Overture's
    places and OpenStreetMap's pooled, and the share of nearby food businesses rated good."""
    found = place_pool.pool(
        overture.read_places(overture.fetch(data_dir, region_id, lonlat_box(cells, margin=0.05))),
        openstreetmap.places(data_dir, region_id),
    )
    columns: dict[str, Sequence[Any]] = {
        indicator: [None if pd.isna(m) else float(m) for m in walk]
        for indicator, walk in amenities.nearest_minutes(network, found, cells).items()
    }
    ratings = fsa.read_ratings(fsa.fetch(data_dir, region_id))
    empty = pd.DataFrame(columns=["Easting", "Northing"])
    reach = amenities.reach_of(
        network,
        {
            "cafe": found.get("cafe", empty),
            "restaurant": found.get("restaurant", empty),
            "ratings": ratings,
        },
        cells,
    )
    for indicator, count in amenities.counts_within_a_walk(network, found, cells, reach).items():
        columns[indicator] = [int(n) for n in count]
    variety = amenities.cuisine_variety(network, found, cells, reach)
    columns["cuisine-variety"] = [int(n) for n in variety]
    share = amenities.good_hygiene_share(network, ratings, cells, reach)
    columns["food-hygiene"] = [None if pd.isna(v) else float(v) for v in share]
    return columns


def _walking_columns(
    network: walking.Network, cells: list[str], data_dir: Path, postcodes: pd.DataFrame
) -> dict[str, Sequence[Any]]:
    """The indicators that are walks along streets (spike S6): minutes to the nearest station,
    school, GP practice and way into a park; the patients per GP, the rail lines and the bus routes
    within a walk."""
    stations = naptan.read_stations(naptan.fetch(data_dir))
    minutes = transport.station_minutes(network, stations, cells)
    columns: dict[str, Sequence[Any]] = {
        "station-proximity": [None if pd.isna(m) else float(m) for m in minutes]
    }
    schools = gias.read_schools(gias.fetch(data_dir))
    for indicator, walk in education.school_minutes(network, schools, cells).items():
        columns[indicator] = [None if pd.isna(m) else float(m) for m in walk]
    sites = nhs_ods.read_gp_sites(*nhs_ods.fetch(data_dir))
    places = health.gp_places(sites, postcodes)
    columns["gp-walk"] = [
        None if pd.isna(m) else float(m) for m in health.gp_minutes(network, places, cells)
    ]
    practices = health.located_practices(nhs_gp.read_practices(*nhs_gp.fetch(data_dir)), postcodes)
    ratio = health.patients_per_gp(
        network,
        practices[["Easting", "Northing"]].to_numpy(dtype=float),
        practices["patients"].to_numpy(dtype=float),
        practices["gps"].to_numpy(dtype=float),
        cells,
    )
    columns["gp-list-size"] = [None if pd.isna(v) else float(v) for v in ratio]
    stops = transport.place_stops(tfl_lines.read_stops(tfl_lines.fetch(data_dir)))
    for indicator, kind, minutes in (
        ("rail-lines-nearby", "rail", 12),
        ("bus-routes-nearby", "bus", 8),
    ):
        of_kind = pd.DataFrame(stops[stops["kind"] == kind])
        found = transport.lines_within_a_walk(network, of_kind, cells, minutes)
        columns[indicator] = [int(n) for n in found]
    gates = os_open_greenspace.read_access_points(
        os_open_greenspace.fetch(data_dir), bounds_bng(cells, margin=3000)
    )
    columns["walk-to-green-space"] = [
        None if pd.isna(m) else float(m)
        for m in environment.green_space_minutes(network, gates, cells)
    ]
    return columns

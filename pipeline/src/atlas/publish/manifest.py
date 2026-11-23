"""The manifest of a data bundle: what the web app needs to read and explain `cells.parquet`.

It is the contract between the pipeline and the web app. `atlas schemas` exports it to JSON
Schema, and the web app generates its types from that. It holds no date: a bundle is named by
a hash of its content, so building twice from the same data gives the same bytes.
"""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from atlas.catalogue.models import Curve, EvidenceType, Grid, PreferenceType


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ManifestRegion(_Model):
    id: str
    name: str


class ManifestDataset(_Model):
    id: str
    name: str
    publisher: str
    url: str
    licence: str
    attribution: str
    date: str


class ManifestOption(_Model):
    """One of the options a user can pick on a choice indicator, such as a faith."""

    id: str
    name: str
    group: str | None = None  # the title of the picker's section
    column: str  # the column of cells.parquet that holds this option's raw value


class ManifestNeighbourhood(_Model):
    """A named area that hex cells belong to, such as an MSOA: "Soho", in Westminster."""

    name: str
    area: str  # the local authority it is in


class ManifestIndicator(_Model):
    id: str
    name: str
    # The column of cells.parquet that holds its raw value. A choice indicator has `options`, each
    # with a column of its own, and this is the prefix of their names.
    column: str
    unit: str
    evidence_type: EvidenceType
    preference_type: PreferenceType
    curve: Curve | None = None
    datasets: list[str]
    options: list[ManifestOption] | None = None


class ManifestFactor(_Model):
    """A node of the factor tree, down to the measured indicators that the bundle holds."""

    id: str
    name: str
    default_weight: int = Field(ge=0, le=5)
    children: list["ManifestFactor"] | None = None
    indicator: str | None = None  # the id of the measured indicator, on a leaf


class ManifestLimit(_Model):
    """A hard limit of a preset, as the web app's profile holds one: one of max, min and in."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    indicator: str
    max: float | None = None
    min: float | None = None
    in_: list[str] | None = Field(default=None, alias="in")

    @model_validator(mode="after")
    def one_bound(self) -> Self:
        if sum(b is not None for b in (self.max, self.min, self.in_)) != 1:
            raise ValueError("a limit needs exactly one of max, min and in")
        return self


class ManifestPreset(_Model):
    """A ready-made preference profile, cut to the factors and indicators of this bundle."""

    id: str
    name: str
    description: str
    weights: dict[str, int] | None = None
    flipped: list[str] | None = None
    limits: list[ManifestLimit] | None = None


class ManifestTravel(_Model):
    """The files and constants of the travel estimate to a user's places (D10), which the web app
    reads only when the user adds a place. Each file is beside `cells.parquet`."""

    # The measured indicator whose values the estimate replaces once a user has places of their own
    indicator: str
    stations: str  # each station's `stop` id, `lat` and `lng`, in the matrix's order
    cell_stations: str  # `cell` (position in cells.parquet), `station` and walking `minutes`
    matrix: str  # `minutes` from each station to each, row by row (station_count squared)
    station_count: int
    unreachable: int  # the minutes that stand for "no way there"
    reach_minutes: float  # how far a walk to a station may be
    walk_metres_a_minute: float
    street_factor: float  # a street walk over its straight line, for a walk from a user's place
    # The region's postcodes (`postcode` without a space, `lat`, `lng`), sorted, so that the app
    # finds a user's postcode without sending it anywhere.
    postcodes: str | None = None


class ManifestHomes(_Model):
    """Where people live (D22). A score describes the homes in a cell, so a cell with fewer than
    `minimum` homes, such as a park, an airport or an industrial estate, has no score."""

    column: str  # the column of cells.parquet with the number of homes in each cell
    minimum: int


class Manifest(_Model):
    format_version: Literal[1] = 1
    version: str  # a hash of the bundle's content
    region: ManifestRegion
    grid: Grid
    cell_count: int
    factors: list[ManifestFactor]
    indicators: list[ManifestIndicator]
    datasets: list[ManifestDataset]
    # The neighbourhoods that cells belong to. The `neighbourhood` column of cells.parquet holds,
    # for each cell, the position of its neighbourhood in this list (empty where it has none).
    neighbourhoods: list[ManifestNeighbourhood] | None = None
    # The homes in each cell. Without it, every cell counts as a place where people live.
    homes: ManifestHomes | None = None
    # Ready-made preference profiles to start from (catalogue/presets/), by name.
    presets: list[ManifestPreset] | None = None
    # The station matrix and each cell's stations, for the travel estimate to a user's places.
    travel: ManifestTravel | None = None

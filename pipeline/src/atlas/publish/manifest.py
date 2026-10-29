"""The manifest of a data bundle: what the web app needs to read and explain `cells.parquet`.

It is the contract between the pipeline and the web app. `atlas schemas` exports it to JSON
Schema, and the web app generates its types from that. It holds no date: a bundle is named by
a hash of its content, so building twice from the same data gives the same bytes.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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


class Manifest(_Model):
    format_version: Literal[1] = 1
    version: str  # a hash of the bundle's content
    region: ManifestRegion
    grid: Grid
    cell_count: int
    factors: list[ManifestFactor]
    indicators: list[ManifestIndicator]
    datasets: list[ManifestDataset]

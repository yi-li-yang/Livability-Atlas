"""The factor catalogue's two files, as Pydantic models.

These models are the one definition of `catalogue/factors.yaml` and
`catalogue/datasets.yaml`: `atlas validate` checks the files against them, and
`atlas schemas` exports them to JSON Schema for the web app. The field
reference is in catalogue/README.md. Rules that span several records, such as
unique ids, live in checks.py.
"""

import re
from datetime import date
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    StringConstraints,
    model_validator,
)

Id = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Url = Annotated[str, StringConstraints(pattern=r"^https?://\S+$")]
Weight = Annotated[int, Field(ge=0, le=5, strict=True)]
Score = Annotated[float, Field(ge=0, le=1)]

Scale = Literal["within-city", "across-cities"]
Status = Literal["idea", "researched", "spiked", "built"]
PreferenceType = Literal["fixed", "user-direction", "user-range", "user-choice"]
EvidenceType = Literal["direct", "estimate", "indirect", "perception", "ranking"]
Tier = Literal["city", "country", "global"]
Credibility = Literal["high", "medium", "low"]

SCALES: tuple[str, ...] = ("within-city", "across-cities")

# Licences that allow redistribution and commercial use, by SPDX id (D07).
# Only datasets under one of them may go into public builds. A licence that
# SPDX does not list takes a LicenseRef- id: TfL's open data licence is
# version 2.0 of the Open Government Licence with TfL's amendments.
OPEN_LICENCES: tuple[str, ...] = (
    "OGL-UK-1.0",
    "OGL-UK-2.0",
    "OGL-UK-3.0",
    "CC-BY-3.0",
    "CC-BY-4.0",
    "CC-BY-SA-3.0",
    "CC-BY-SA-4.0",
    "CC0-1.0",
    "ODbL-1.0",
    "CDLA-Permissive-1.0",
    "CDLA-Permissive-2.0",
    "Apache-2.0",
    "LicenseRef-TfL-Open-Data",
)


class _Strict(BaseModel):
    """Rejects unknown fields, so a misspelt field name does not pass unseen."""

    model_config = ConfigDict(extra="forbid")


# --- Scoring curves (docs/methodology/scoring.md, section 3) ---


class Ramp(_Strict):
    shape: Literal["ramp"]
    t0: float
    t1: float

    @model_validator(mode="after")
    def _ends_differ(self) -> Self:
        if self.t0 == self.t1:
            raise ValueError("a ramp needs two different numbers, t0 and t1")
        return self


class IdealRange(_Strict):
    shape: Literal["ideal-range"]
    l0: float
    l1: float
    u1: float
    u0: float

    @model_validator(mode="after")
    def _in_order(self) -> Self:
        if not (self.l0 < self.l1 <= self.u1 < self.u0):
            raise ValueError("an ideal-range curve needs numbers with l0 < l1 ≤ u1 < u0")
        return self


class Lookup(_Strict):
    shape: Literal["lookup"]
    scores: dict[str | int, Score] = Field(min_length=1)


class Percentile(_Strict):
    shape: Literal["percentile"]
    better: Literal["higher", "lower"]


Curve = Annotated[Ramp | IdealRange | Lookup | Percentile, Field(discriminator="shape")]


# --- factors.yaml ---

# The fields research adds to a measured indicator.
INDICATOR_FIELDS = (
    "unit",
    "preference_type",
    "curve",
    "curve_reason",
    "evidence_type",
    "comparable_across_regions",
    "method",
    "datasets",
)
_RESEARCHED = (
    "unit",
    "preference_type",
    "evidence_type",
    "comparable_across_regions",
    "method",
    "datasets",
    "curve_reason",
)
# The fields each research status requires of a measured indicator, beyond a
# name and a default weight.
REQUIRED_BY_STATUS: dict[str, tuple[str, ...]] = {
    "idea": (),
    "researched": _RESEARCHED,
    "spiked": (*_RESEARCHED, "curve"),
    "built": (*_RESEARCHED, "curve"),
}


class Factor(_Strict):
    id: Id
    name: Text
    description: Text | None = None
    default_weight: Weight
    weight_reason: Text | None = None
    scales: list[Scale] | None = Field(default=None, min_length=1)
    status: Status | None = None
    children: list["Factor"] | None = None
    # Measured indicators only.
    unit: Text | None = None
    preference_type: PreferenceType | None = None
    curve: Curve | None = None
    curve_reason: Text | None = None
    evidence_type: EvidenceType | None = None
    comparable_across_regions: StrictBool | None = None
    method: Text | None = None
    datasets: list[Text] | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _fields_fit_the_kind_of_factor(self) -> Self:
        present = [name for name in INDICATOR_FIELDS if getattr(self, name) is not None]
        if self.children is not None:
            if not self.children:
                raise ValueError("children must be a non-empty list")
            if present:
                raise ValueError(
                    "a factor with sub-factors is not a measured indicator, "
                    f"so it cannot have {', '.join(present)}"
                )
            if self.status is not None:
                raise ValueError(
                    "a factor with sub-factors takes its research status from them, "
                    "so it has none of its own"
                )
            return self
        if self.curve is not None:
            if self.curve_reason is None:
                raise ValueError("a curve needs a curve_reason")
            if self.preference_type == "user-range" and self.curve.shape != "ideal-range":
                raise ValueError(
                    "a user-range measured indicator needs an ideal-range curve, "
                    "because its user drags a band"
                )
        status = self.status or "idea"
        missing = [name for name in REQUIRED_BY_STATUS[status] if getattr(self, name) is None]
        if missing:
            raise ValueError(f"at status {status}, it needs {', '.join(missing)}")
        return self


class FactorsFile(_Strict):
    factors: list[Factor] = Field(min_length=1)


# --- datasets.yaml ---


class Dataset(_Strict):
    id: Id
    name: Text
    publisher: Text
    url: Url
    tier: Tier
    area: Text
    resolution: Text
    date: Text | StrictInt
    licence: Text
    licence_checked: date | None = None
    public_build: StrictBool
    licence_note: Text | None = None
    attribution: Text | None = None
    tells: list[Text] = Field(min_length=1)
    credibility: Credibility | None = None
    credibility_reason: Text | None = None

    @model_validator(mode="after")
    def _public_build_follows_d07(self) -> Self:
        if self.public_build:
            # A dataset under several licences at once joins their ids with
            # AND, as SPDX expressions do, and each of them must be open.
            closed = [
                part for part in re.split(r"\s+AND\s+", self.licence) if part not in OPEN_LICENCES
            ]
            if closed:
                raise ValueError(
                    f"public_build is true, but {' and '.join(closed)} "
                    f"{'is' if len(closed) == 1 else 'are'} not on D07's list of open licences: "
                    f"{', '.join(OPEN_LICENCES)}"
                )
            if self.licence_checked is None:
                raise ValueError(
                    "public_build is true, so it needs licence_checked, "
                    "the date its licence was checked at the source"
                )
            if self.attribution is None:
                raise ValueError("public_build is true, so it needs an attribution")
        elif self.licence_note is None:
            raise ValueError("public_build is false, so it needs a licence_note saying why")
        if self.credibility is not None and self.credibility_reason is None:
            raise ValueError("credibility needs a credibility_reason")
        return self


class DatasetsFile(_Strict):
    datasets: list[Dataset]

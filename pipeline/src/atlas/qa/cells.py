"""A built bundle, read for the QA report's checks and facts.

It reads only the bundle's own files, `manifest.json` and `cells.parquet`, so a report can be made
again from any build without the raw downloads.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import h3
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from numpy.typing import NDArray

from atlas.catalogue.models import Curve
from atlas.publish.manifest import Manifest, ManifestOption

NOT_VALUES = ("cell", "neighbourhood")  # the columns of cells.parquet that are not measured


class OutsideBundle(KeyError):
    """A named place is not in any of the bundle's cells (the bundle covers part of the region)."""


@dataclass(frozen=True)
class Described:
    """A column of values, and what the manifest says about it."""

    column: str
    indicator: str
    name: str
    unit: str
    curve: Curve | None
    datasets: list[str]
    option: ManifestOption | None  # the option of a choice indicator that the column holds

    @property
    def label(self) -> str:
        """ "Faith (Hindu)" for an option of a choice, and the indicator's name for any other."""
        return f"{self.name} ({self.option.name})" if self.option else self.name


class Cells:
    """The cells of one bundle, with named places (Soho, Wimbledon village) to look values up at."""

    def __init__(
        self,
        folder: Path,
        manifest: Manifest,
        table: pa.Table,
        places: Mapping[str, tuple[float, float]],
    ) -> None:
        self.folder = folder
        self.manifest = manifest
        self.table = table
        self.places = dict(places)
        self._row = {cell: i for i, cell in enumerate(table["cell"].to_pylist())}
        self._texts = frozenset(
            name
            for name in self.columns
            if pa.types.is_string(table[name].type) or pa.types.is_large_string(table[name].type)
        )
        self._described = tuple(_describe(manifest))
        self._numbers: dict[str, NDArray[np.float64]] = {}

    @property
    def count(self) -> int:
        return self.table.num_rows

    @property
    def columns(self) -> list[str]:
        return [name for name in self.table.column_names if name not in NOT_VALUES]

    def has(self, *columns: str) -> bool:
        """Whether the table has every one of these columns, `neighbourhood` included."""
        return all(column in self.table.column_names for column in columns)

    def _field(self, column: str) -> pa.ChunkedArray:
        if column not in self.columns:
            raise KeyError(f"the bundle has no column {column}")
        return self.table[column]

    def texts(self) -> frozenset[str]:
        """The value columns that hold text, such as the PTAL band."""
        return self._texts

    def numbers(self, column: str) -> NDArray[np.float64]:
        """The values as floats, with NaN where a cell has none. The array is read once and
        shared, so it cannot be changed."""
        field = self._field(column)
        if column in self._texts:
            raise TypeError(f"{column} holds text, not numbers")
        if column not in self._numbers:
            values = np.asarray(field.to_numpy(zero_copy_only=False), dtype=np.float64)
            values.flags.writeable = False
            self._numbers[column] = values
        return self._numbers[column]

    def text(self, column: str) -> list[str | None]:
        field = self._field(column)
        if column not in self.texts():
            raise TypeError(f"{column} holds numbers, not text")
        return field.to_pylist()

    def valued(self, column: str) -> NDArray[np.bool_]:
        """Whether each cell has a value in a column of numbers or of text."""
        if column in self.texts():
            return np.array([v is not None for v in self.text(column)], dtype=np.bool_)
        return ~np.isnan(self.numbers(column))

    def scored(self, column: str) -> NDArray[np.float64]:
        """Numbers to rank the cells by: the values, or for a text column the scores that its
        lookup curve gives them (the higher PTAL band scores higher), NaN where it has none."""
        if column not in self.texts():
            return self.numbers(column)
        curve = next((d.curve for d in self.described() if d.column == column), None)
        if curve is None or curve.shape != "lookup":
            raise TypeError(f"{column} holds text with no lookup curve to rank it by")
        scores = {str(key): float(score) for key, score in curve.scores.items()}
        return np.array(
            [scores.get(v, np.nan) if v is not None else np.nan for v in self.text(column)]
        )

    def cell_of(self, place: str) -> str:
        """The cell that a named place is in."""
        if place not in self.places:
            raise KeyError(f"no place named {place}")
        lat, lng = self.places[place]
        cell = h3.latlng_to_cell(lat, lng, self.manifest.grid.resolution)
        if cell not in self._row:
            raise OutsideBundle(f"{place} is outside the bundle's cells")
        return cell

    def at(self, place: str, column: str) -> float:
        return float(self.numbers(column)[self._row[self.cell_of(place)]])

    def text_at(self, place: str, column: str) -> str | None:
        return self.text(column)[self._row[self.cell_of(place)]]

    def neighbourhood_at(self, place: str) -> tuple[str, str] | None:
        """The name and the local authority of the neighbourhood that a place is in."""
        listing = self.manifest.neighbourhoods
        if listing is None or "neighbourhood" not in self.table.column_names:
            return None
        index = self.table["neighbourhood"][self._row[self.cell_of(place)]].as_py()
        return None if index is None else (listing[index].name, listing[index].area)

    def described(self) -> list[Described]:
        """Every value column, in the manifest's order, with its indicator, unit and curve."""
        return list(self._described)


def _describe(manifest: Manifest) -> list[Described]:
    out: list[Described] = []
    for indicator in manifest.indicators:
        common = (indicator.id, indicator.name, indicator.unit, indicator.curve)
        if indicator.options is not None:
            out += [Described(o.column, *common, indicator.datasets, o) for o in indicator.options]
        else:
            out.append(Described(indicator.column, *common, indicator.datasets, None))
    return out


def read_cells(folder: Path, places: Mapping[str, tuple[float, float]] | None = None) -> Cells:
    manifest = Manifest.model_validate_json((folder / "manifest.json").read_text(encoding="utf-8"))
    return Cells(folder, manifest, pq.read_table(folder / "cells.parquet"), places or {})

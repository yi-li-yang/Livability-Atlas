"""Reads the catalogue's YAML files and checks them.

`validate_catalogue` is what `atlas validate` runs. It never raises on bad
content: it returns the problems, so that one run lists them all.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError

from atlas.catalogue.checks import check_datasets, check_factors
from atlas.catalogue.models import DatasetsFile, FactorsFile
from atlas.paths import CATALOGUE_DIR


def describe(error: Any, raw: Any, file_name: str) -> str:
    """One Pydantic error as a sentence that names the factor or dataset it concerns."""
    label = file_name
    node = raw
    for part in error["loc"]:
        try:
            node = node[part]
        except (KeyError, IndexError, TypeError):
            break
        if isinstance(node, dict) and isinstance(node.get("id"), str):
            label = node["id"]
    field = next((part for part in reversed(error["loc"]) if isinstance(part, str)), file_name)
    if error["type"] == "extra_forbidden":
        return f"{label}: unknown field {field}."
    message = error["msg"].removeprefix("Value error, ")
    if error["type"] == "value_error":
        return f"{label}: {message}."
    return f"{label}: {field}: {message}."


def _parse[T: BaseModel](model: type[T], path: Path, problems: list[str]) -> T | None:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as error:
        problems.append(f"{path.name}: cannot be read ({error.strerror}).")
        return None
    except yaml.YAMLError as error:
        problems.append(f"{path.name}: is not valid YAML ({error}).")
        return None
    try:
        return model.model_validate(raw)
    except ValidationError as error:
        problems.extend(describe(item, raw, path.name) for item in error.errors())
        return None


def validate_catalogue(directory: Path = CATALOGUE_DIR) -> list[str]:
    """Checks `factors.yaml` and `datasets.yaml` in `directory`. An empty list means they pass."""
    problems: list[str] = []
    datasets = _parse(DatasetsFile, directory / "datasets.yaml", problems)
    factors = _parse(FactorsFile, directory / "factors.yaml", problems)
    if datasets is not None:
        problems.extend(check_datasets(datasets))
    if factors is not None and datasets is not None:
        problems.extend(check_factors(factors, datasets))
    return problems

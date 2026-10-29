"""Overture Maps' places (dataset `overture-places`): shops, cafés, pharmacies and other businesses
from several sources, with a category for each. Licences are by source: CDLA-Permissive-2.0,
Apache-2.0 and CC0-1.0.

A release is a set of Parquet files on Amazon S3, which DuckDB reads in place and filters to the
region's box. The result is kept in `data/raw/overture/`, and the release is pinned, so a build
reads the same places until the release is changed here.
"""

from pathlib import Path

import duckdb
import pandas as pd

RELEASE = "2026-10-21.0"
NOT_OPEN = "permanently_closed"


def source(release: str) -> str:
    return f"s3://overturemaps-us-west-2/release/{release}/theme=places/type=place/*"


def fetch(data_dir: Path, region_id: str, box: tuple[float, float, float, float]) -> Path:
    """The region's places in `box` (west, south, east, north, in degrees), saved once as Parquet
    without those that Overture marks permanently closed."""
    path = data_dir / "raw" / "overture" / f"places-{region_id}-{RELEASE}.parquet"
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    where = source(RELEASE)
    connection = duckdb.connect()
    connection.sql("SET enable_progress_bar=false;")
    if where.startswith("s3://"):
        connection.sql("INSTALL httpfs; LOAD httpfs; SET s3_region='us-west-2';")
    west, south, east, north = box
    partial = path.with_name(path.name + ".part")
    try:
        connection.sql(f"""
            COPY (
              SELECT id, bbox.xmin AS lng, bbox.ymin AS lat, names.primary AS name,
                     taxonomy.primary AS category
              FROM read_parquet('{where}', hive_partitioning=1)
              WHERE bbox.xmin BETWEEN {west} AND {east}
                AND bbox.ymin BETWEEN {south} AND {north}
                AND coalesce(operating_status, 'open') <> '{NOT_OPEN}'
            ) TO '{partial.as_posix()}' (FORMAT parquet)
        """)
        partial.replace(path)
    finally:
        partial.unlink(missing_ok=True)
    return path


def read_places(path: Path) -> pd.DataFrame:
    """The places, with `id`, `lng`, `lat`, `name` (or None) and `category`."""
    return pd.read_parquet(path)

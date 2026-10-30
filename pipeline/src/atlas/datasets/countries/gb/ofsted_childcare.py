"""Ofsted's register of childcare providers in England (dataset `ofsted-childcare`).

The "most recent inspections" management information: one row for each registered provider, with
its type, its postcode and its latest inspection. Open Government Licence v3.0. Ofsted hides the
name and the address of childminders and home childcarers (they work from homes), so only
childcare on non-domestic premises has a postcode. The release is pinned: each release has its
own address.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.csv as pacsv

from atlas.fetch import download

URL = (
    "https://assets.publishing.service.gov.uk/media/6973934c67ae94b3280137b4/"
    "Management_information_-_childcare_providers_and_inspections_-_most_recent_inspections_"
    "data_as_at_31_December_2025.csv"
)
PREMISES = "Childcare on non-domestic premises"
NURSERIES = ["Full day care", "Sessional day care"]  # not out-of-school clubs
COLUMNS = ["Provider Type", "Provider Subtype", "Provider Postcode"]


def fetch(data_dir: Path) -> Path:
    """Downloads the file (about 19 MB) to `data/raw/ofsted-childcare/` once, and returns it."""
    path = data_dir / "raw" / "ofsted-childcare" / "most-recent-inspections.csv"
    download(URL, path)
    return path


def read_nurseries(path: Path) -> pd.DataFrame:
    """The nurseries and pre-schools (full day care and sessional day care on non-domestic
    premises) with their `Postcode`. Two lines of title come before the header, and the file is
    not UTF-8."""
    table = pacsv.read_csv(
        path,
        read_options=pacsv.ReadOptions(skip_rows=2, encoding="latin-1"),
        convert_options=pacsv.ConvertOptions(
            include_columns=COLUMNS, column_types={c: pa.string() for c in COLUMNS}
        ),
    )
    kind = np.array(table["Provider Type"].to_pylist(), dtype=object)
    subtype = np.array(table["Provider Subtype"].to_pylist(), dtype=object)
    postcode = np.array(table["Provider Postcode"].to_pylist(), dtype=object)
    named = np.array([isinstance(p, str) and p.strip() not in ("", "REDACTED") for p in postcode])
    keep = (kind == PREMISES) & np.isin(subtype, NURSERIES) & named
    return pd.DataFrame({"Postcode": postcode[keep]})

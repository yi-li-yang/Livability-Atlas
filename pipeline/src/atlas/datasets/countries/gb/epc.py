"""Domestic energy performance certificates for England and Wales (dataset `epc-domestic`).

The service of the Department for Levelling Up, Housing and Communities (MHCLG) offers the whole
register as one zip of CSV files by year, regenerated on the 1st of each month. Fetching it takes
a bearer token from the owner's account (`EPC_TOKEN` in `.env`, after signing in with GOV.UK One
Login). All fields but the address are under the Open Government Licence v3.0. The address and
postcode come from Ordnance Survey and Royal Mail, who permit them for purposes related to energy
performance, and under the copyright exception for non-commercial research. See the dataset's
`licence_note`: this build uses them only to match a certificate to a sale, and keeps a hash of
each address, not the address. The service says the register holds personal data, so the register
itself stays in `data/raw/`, which git ignores.
"""

import io
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import IO

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.csv as pacsv
import requests

from atlas.datasets.countries.gb.addresses import address_key
from atlas.datasets.countries.gb.code_point import normalise
from atlas.fetch import download
from atlas.secrets import secret

URL = "https://api.get-energy-performance-data.communities.gov.uk/api/files/domestic/csv"


def token() -> str:
    return secret("EPC_TOKEN")


def fetch(data_dir: Path) -> Path:
    """Downloads the full register to `data/raw/epc/` once, and returns the zip. The service
    answers with a redirect to a signed address, which is read without the token and downloaded
    on its own."""
    target = data_dir / "raw" / "epc" / "domestic-csv.zip"
    if target.exists() and target.with_name(target.name + ".sha256").exists():
        return target
    reply = requests.get(
        URL,
        headers={"Authorization": f"Bearer {token()}", "Accept": "application/json"},
        allow_redirects=False,
        timeout=60,
    )
    if reply.status_code != 302 or "location" not in reply.headers:
        raise RuntimeError(
            f"the certificate service answered {reply.status_code}, not a download: "
            "check EPC_TOKEN in .env (the token is on your account page and may have expired)"
        )
    download(reply.headers["location"], target)
    return target


COLUMNS = ["address1", "address2", "address3", "postcode", "total_floor_area"]


BLOCK = 64 * 2**20  # bytes of CSV parsed at a time


def _blocks(file: IO[bytes], size: int = BLOCK) -> Iterator[bytes]:
    """The CSV file in blocks of about `size` bytes that each end at the end of a record and
    start with the header, so that each reads as a table of its own. A quoted field may hold
    a line break, so a record ends at the last line break after an even number of quotes."""
    header = file.readline()
    pending = b""
    while True:
        data = pending + file.read(size)
        if not data:
            return
        more = len(data) - len(pending) == size
        if not more:
            yield header + data
            return
        end = data.rfind(b"\n") + 1
        while end > 0 and data.count(b'"', 0, end) % 2 == 1:
            end = data.rfind(b"\n", 0, end - 1) + 1
        if end == 0:  # one record longer than a block: take more
            pending = data
            continue
        yield header + data[:end]
        pending = data[end:]


def read_certificates(path: Path, postcodes: set[str]) -> pd.DataFrame:
    """The homes with a certificate at the given postcodes, as a table with an address `key`
    (a hash that `addresses.address_key` makes, so that no address is kept) and the `floor_area`
    in square metres, the median of a home's certificates. `postcodes` are written without
    spaces, in capitals. A certificate with no floor area is left out. The recommendations
    files in the zip are not read."""
    frames = []
    with zipfile.ZipFile(path) as archive:
        for name in sorted(n for n in archive.namelist() if n.startswith("certificates-")):
            with archive.open(name) as file:
                for block in _blocks(file):
                    table = pacsv.read_csv(
                        io.BytesIO(block),
                        convert_options=pacsv.ConvertOptions(
                            include_columns=COLUMNS,
                            column_types={c: pa.string() for c in COLUMNS},
                        ),
                    )
                    frame = table.to_pandas()
                    squashed = frame["postcode"].fillna("").map(normalise)
                    frame = frame.loc[squashed.isin(postcodes)]
                    if not frame.empty:
                        frames.append(frame)
    if not frames:
        return pd.DataFrame({"key": [], "floor_area": []})
    every = pd.concat(frames, ignore_index=True)
    area = np.asarray(pd.to_numeric(every["total_floor_area"], errors="coerce"), dtype=float)
    keys = np.array(
        [
            address_key(p, one, two, three)
            for p, one, two, three in zip(
                every["postcode"],
                every["address1"],
                every["address2"],
                every["address3"],
                strict=True,
            )
        ]
    )
    homes = pd.Series(area[area > 0], index=keys[area > 0])
    median = homes.groupby(level=0).median()
    return pd.DataFrame({"key": median.index.to_numpy(), "floor_area": median.to_numpy()})


def certificates(data_dir: Path, region_id: str, postcodes: set[str]) -> pd.DataFrame:
    """The region's certificates, read from the zip once. Reading 27 GB of CSV takes a while, so
    the table is kept beside the zip, named by the first characters of the zip's checksum: a new
    download has new certificates."""
    archive = fetch(data_dir)
    checksum = archive.with_name(archive.name + ".sha256").read_text(encoding="utf-8").strip()
    kept = archive.with_name(f"certificates-{region_id}-{checksum[:12]}.parquet")
    if kept.exists():
        return pd.read_parquet(kept)
    table = read_certificates(archive, postcodes)
    table.to_parquet(kept)
    return table

"""Spike S3: are there enough sales per hex cell, and can rent be modelled from sale prices?

Throwaway code, never imported by `atlas`. It answers the part of S3 that needs no energy
certificates: those need a GOV.UK account to download, and matching them to sales by address
waits on Royal Mail's answer (docs/progress.md). Needs, in `data/raw/`:
- `landregistry/pp-2024.csv`, `pp-2025.csv`, `pp-2026.csv`, the Price Paid Data
- `codepoint/Data/CSV/*.csv`, OS Code-Point Open, for each postcode's coordinates
- `ons-rents/rents.xlsx`, the ONS's private rental market in London by postcode district
- what spike S2 needs, for the residents of each cell
Run from `pipeline/` with `uv run python notebooks/s3_sales_and_rents.py`.
"""

import json

import h3
import numpy as np
import openpyxl
import pandas as pd
from pyproj import Transformer
from s2_crime_rates import london_cells, residents_by_area

from atlas.paths import data_dir

RESOLUTION = 9
RAW = data_dir() / "raw"
LAST_12 = "2025-10-01"
LAST_24 = "2024-10-01"
THRESHOLDS = (5, 10, 20, 40)


def postcodes() -> pd.DataFrame:
    """Every London postcode with its coordinates and the admin district code that holds it."""
    frames = [
        pd.read_csv(
            path, header=None, usecols=[0, 2, 3, 8], names=["postcode", "e", "n", "district"]
        )
        for path in sorted((RAW / "codepoint" / "Data" / "CSV").glob("*.csv"))
    ]
    codes = pd.concat(frames, ignore_index=True)
    codes = codes[codes["district"].astype(str).str.startswith("E09")].copy()
    lng, lat = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True).transform(
        codes["e"].to_numpy(), codes["n"].to_numpy()
    )
    codes["cell"] = [h3.latlng_to_cell(a, o, RESOLUTION) for a, o in zip(lat, lng, strict=True)]
    codes["outward"] = codes["postcode"].str.split(" ").str[0]
    return codes


def sales() -> pd.DataFrame:
    columns = [
        "id",
        "price",
        "date",
        "postcode",
        "type",
        "new",
        "tenure",
        "paon",
        "saon",
        "street",
        "locality",
        "town",
        "district",
        "county",
        "category",
        "status",
    ]
    frame = pd.concat(
        [
            pd.read_csv(
                RAW / "landregistry" / f"pp-{year}.csv",
                header=None,
                names=columns,
                usecols=["price", "date", "postcode", "type", "new", "category"],
            )
            for year in (2024, 2025, 2026)
        ],
        ignore_index=True,
    )
    frame["date"] = frame["date"].str[:10]
    return frame[frame["category"] == "A"]


def cells_with_enough(counts: pd.Series, cells: list[str], k: int, minimum: int) -> float:
    index = set(cells)
    pooled = [sum(counts.get(c, 0) for c in h3.grid_disk(cell, k) if c in index) for cell in cells]
    return float((np.array(pooled) >= minimum).mean())


def rent_by_district() -> pd.DataFrame:
    sheet = openpyxl.load_workbook(RAW / "ons-rents" / "rents.xlsx", read_only=True)["3"]
    rows = list(sheet.iter_rows(min_row=4, values_only=True))
    frame = pd.DataFrame(
        [r[:7] for r in rows],
        columns=["outward", "bedrooms", "count", "mean", "lq", "median", "uq"],
    )
    frame["median"] = pd.to_numeric(frame["median"], errors="coerce")
    frame["count"] = pd.to_numeric(frame["count"], errors="coerce")
    return frame.dropna(subset=["outward", "median"])


def fit(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float, float]:
    """Log rent on log price: slope, intercept, R squared, and the leave-one-out mean % error."""
    slope, intercept = np.polyfit(x, y, 1)
    r2 = 1 - ((y - (slope * x + intercept)) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    errors = []
    for i in range(len(x)):
        keep = np.arange(len(x)) != i
        s, c = np.polyfit(x[keep], y[keep], 1)
        errors.append(abs(np.exp(s * x[i] + c) / np.exp(y[i]) - 1))
    return float(slope), float(intercept), float(r2), float(np.mean(errors))


def main() -> None:
    cells = london_cells()
    residents = residents_by_area(cells)
    homes = [c for c in cells if residents.get(c, 0) >= 50]
    codes = postcodes().drop_duplicates("postcode")
    sold = sales().merge(codes, on="postcode", how="inner")
    result: dict[str, object] = {
        "residential sales in London since Oct 2024": int((sold["date"] >= LAST_24).sum()),
        "cells": len(cells),
        "cells with 50 or more residents": len(homes),
    }
    for label, start in (("12 months", LAST_12), ("24 months", LAST_24)):
        counts = sold[sold["date"] >= start].groupby("cell").size()
        for k in (0, 1, 2):
            for minimum in THRESHOLDS:
                share = cells_with_enough(counts, homes, k, minimum)
                result[f"homes cells with {minimum}+ sales, {label}, pooled over {k} steps"] = (
                    round(share, 3)
                )

    # How many sales a median needs: the spread of log price inside a cell sets the error.
    recent = sold[sold["date"] >= LAST_24].assign(log=lambda d: np.log(d["price"]))
    spread = recent.groupby("cell")["log"].agg(["std", "count"])
    typical_sd = float(spread.loc[spread["count"] >= 10, "std"].median())
    result["typical spread of log price within a cell"] = round(typical_sd, 3)
    for error in (0.10, 0.15, 0.20):
        result[f"sales for a median within {error:.0%}, 95% sure"] = int(
            np.ceil((1.96 * 1.2533 * typical_sd / error) ** 2)
        )

    # Rent from sale prices, by postcode district.
    rents = rent_by_district()
    flats = (
        sold[(sold["type"] == "F") & (sold["date"] >= LAST_12)]
        .groupby("outward")["price"]
        .agg(["median", "count"])
    )
    flats = flats[flats["count"] >= 10]
    district_of = codes.groupby("outward")["district"].agg(lambda s: s.mode().iat[0])
    result["postcode districts with rents"] = int(rents["outward"].nunique())
    model: dict[str, object] = {}
    for bedrooms in ("One Bedroom", "Two Bedrooms"):
        r = rents[(rents["bedrooms"] == bedrooms) & (rents["count"] >= 30)].set_index("outward")[
            "median"
        ]
        both = pd.concat(
            [r.rename("rent"), flats["median"].rename("price")], axis=1, join="inner"
        ).dropna()
        x, y = np.log(both["price"].to_numpy()), np.log(both["rent"].to_numpy())
        slope, _, r2, loo = fit(x, y)
        group = district_of.reindex(both.index)
        baseline = []
        for outward, rent in both["rent"].items():
            others = both["rent"][(group == group[outward]) & (both.index != outward)]
            if len(others):
                baseline.append(abs(others.mean() / rent - 1))
        yield_ = 12 * both["rent"] / both["price"]
        constant_yield = []
        combined = []
        for outward in both.index:
            keep = both.index != outward
            constant_yield.append(
                abs(yield_[keep].median() * both["price"][outward] / 12 / both["rent"][outward] - 1)
            )
            same = keep & (group == group[outward]).to_numpy()
            if same.sum() >= 3:
                mean_log_rent, mean_log_price = (
                    np.log(both["rent"][same]).mean(),
                    np.log(both["price"][same]).mean(),
                )
                slope_within = np.polyfit(
                    np.log(both["price"][same]) - mean_log_price,
                    np.log(both["rent"][same]) - mean_log_rent,
                    1,
                )[0]
                guess = np.exp(
                    mean_log_rent + slope_within * (np.log(both["price"][outward]) - mean_log_price)
                )
                combined.append(abs(guess / both["rent"][outward] - 1))
        model[bedrooms] = {
            "districts used": len(both),
            "slope of log rent on log price": round(slope, 3),
            "R squared": round(r2, 3),
            "leave-one-out error of the price model": round(loo, 3),
            "error of using the mean of the district's borough": round(float(np.mean(baseline)), 3),
            "error of a constant yield": round(float(np.mean(constant_yield)), 3),
            "error of the borough mean plus price differences within the borough": round(
                float(np.mean(combined)), 3
            ),
            "districts the last model could be tried on": len(combined),
            "gross yield implied at the median (annual rent over price)": round(
                float((12 * both["rent"] / both["price"]).median()), 3
            ),
            "spread of yield, 10th to 90th percentile": [
                round(float(q), 3) for q in (12 * both["rent"] / both["price"]).quantile([0.1, 0.9])
            ],
        }
    result["rent from sale prices, by postcode district"] = model
    print(json.dumps(result, indent=2, default=float))


if __name__ == "__main__":
    main()

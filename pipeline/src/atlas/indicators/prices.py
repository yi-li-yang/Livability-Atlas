"""The buying cost indicator: the price per square metre of the homes sold nearby.

A sale's floor area comes from the energy certificate at the same address (an address is matched
by its postcode and the words of its lines, whatever their order: see `addresses`). The price per
square metre of a cell is the median over the sales in the cell and the cells within two steps,
over 24 months (spike S3: that gives 20 or more sales in 99% of London's cells).
"""

import h3
import numpy as np
import pandas as pd

from atlas.datasets.countries.gb.addresses import address_key

MIN_AREA, MAX_AREA = 10.0, 500.0  # m²: a floor area outside these is a typing error
STEPS = 2
MINIMUM_SALES = 20


def floor_areas(sales: pd.DataFrame, certificates: pd.DataFrame) -> pd.Series:
    """The floor area in square metres of each sale's home, or NaN where no certificate is at its
    address. `sales` has `postcode`, `saon`, `paon` and `street`; `certificates` has the address
    `key` (`addresses.address_key`) and the `floor_area` of each home. A home with several
    certificates gets their median area."""
    area = pd.Series(certificates["floor_area"].to_numpy(dtype=float), index=certificates["key"])
    median = area.groupby(level=0).median()
    sale_keys = [
        address_key(p, s, n, t)
        for p, s, n, t in zip(
            sales["postcode"], sales["saon"], sales["paon"], sales["street"], strict=True
        )
    ]
    return pd.Series(median.reindex(sale_keys).to_numpy(dtype=float))


def per_metre(price: pd.Series, area: pd.Series) -> pd.Series:
    """The price over the floor area, where the area is that of a home."""
    values = area.to_numpy(dtype=float)
    plausible = (values >= MIN_AREA) & (values <= MAX_AREA)
    return price.astype(float) / pd.Series(np.where(plausible, values, np.nan), index=area.index)


def pooled_median(
    sold: pd.DataFrame, cells: list[str], steps: int = STEPS, minimum: int = MINIMUM_SALES
) -> pd.Series:
    """The median `per_metre` over the sales in each cell and the cells within `steps` of it.
    `sold` has a `cell` and a `per_metre` for each sale. A cell with fewer than `minimum` sales
    around it has no value."""
    by_cell = {
        str(cell): group.to_numpy(dtype=float) for cell, group in sold.groupby("cell")["per_metre"]
    }
    out = np.full(len(cells), np.nan)
    for position, cell in enumerate(cells):
        around = [by_cell[c] for c in h3.grid_disk(cell, steps) if c in by_cell]
        if around:
            values = np.concatenate(around)
            if len(values) >= minimum:
                out[position] = float(np.median(values))
    return pd.Series(out, index=cells)

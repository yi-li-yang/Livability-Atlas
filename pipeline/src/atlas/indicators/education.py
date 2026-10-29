"""The education indicators that are walks: the minutes on foot to the nearest primary school and
the nearest secondary school, and the share of the schools within a walk whose latest Ofsted
inspection meets the standard."""

import numpy as np
import pandas as pd

from atlas.datasets.countries.gb.ofsted import AREAS
from atlas.spatial.grid import cell_centres_bng
from atlas.spatial.walking import Network


def school_minutes(
    network: Network, schools: pd.DataFrame, cells: list[str]
) -> dict[str, pd.Series]:
    """The walking minutes from each cell's centre to the nearest school of each phase, along
    streets and paths. `schools` has `Easting`, `Northing`, `primary` and `secondary` columns."""
    origins = cell_centres_bng(cells)
    result: dict[str, pd.Series] = {}
    for indicator, phase in (("primary-schools", "primary"), ("secondary-schools", "secondary")):
        chosen = schools.loc[schools[phase]]
        places = np.column_stack([chosen["Easting"].to_numpy(), chosen["Northing"].to_numpy()])
        minutes = network.minutes_to_nearest(places=places, origins=origins)
        result[indicator] = pd.Series(minutes, index=cells)
    return result


# What Ofsted's file says of a school's latest inspections, and what counts as meeting the standard.
BELOW_EXPECTED = ["Needs attention", "Urgent improvement"]
GOOD = ["1", "2"]  # overall effectiveness: outstanding, good
NOT_GOOD = ["3", "4"]  # requires improvement, inadequate
MINIMUM_JUDGED = 3  # schools with a judgement that a share needs in reach
STILL_GOOD = [
    "School remains Good",
    "School remains Outstanding",
    "Standards maintained",
    "School remains Good (Concerns) - S5 Next",
    "School remains Good (Improving) - S5 Next",
    "School remains Outstanding (Concerns) - S5 Next",
]


def meets_standard(judgements: pd.DataFrame) -> pd.Series:
    """Whether each school's latest inspection meets the standard: 1, 0, or NaN where the file
    gives no judgement to go on.

    A school with a report card (since November 2025) meets it if its safeguarding standards are
    met and none of its graded areas needs attention or urgent improvement. Otherwise its latest
    graded overall effectiveness counts: outstanding or good meet it, and requires improvement or
    inadequate do not. A school with no grade, whose later inspection without grades says that it
    remains good or outstanding, meets it. The report card is the later inspection, and a grade is
    not overturned by a visit without grades.
    """
    count = len(judgements)
    safeguarding = judgements["Safeguarding standards"].to_numpy(dtype=object)
    has_card = np.asarray(pd.notna(safeguarding))
    below = np.zeros(count, dtype=bool)
    for area in AREAS:
        below |= np.isin(judgements[area].to_numpy(dtype=object), BELOW_EXPECTED)
    overall = judgements["Latest OEIF overall effectiveness"].to_numpy(dtype=object)
    outcome = judgements["Ungraded inspection overall outcome"].to_numpy(dtype=object)
    result = np.full(count, np.nan)
    result[np.isin(outcome, STILL_GOOD)] = 1.0
    result[np.isin(overall, GOOD)] = 1.0
    result[np.isin(overall, NOT_GOOD)] = 0.0
    card = (safeguarding == "Met") & ~below
    result[has_card] = card[has_card].astype(float)
    return pd.Series(result)


def inspection_share(
    network: Network,
    schools: pd.DataFrame,
    cells: list[str],
    minutes: float = 25.0,
    minimum: int | None = None,
) -> pd.Series:
    """The percentage of the schools within a walk of each cell's centre whose latest inspection
    meets the standard. `schools` has `Easting`, `Northing` and `meets` (1, 0 or NaN where the
    school has no judgement, which leaves it out). A cell with fewer than `minimum` judged schools
    in reach (`MINIMUM_JUDGED` by default) has no value."""
    judged = schools.loc[schools["meets"].notna().to_numpy()]
    places = np.column_stack([judged["Easting"].to_numpy(), judged["Northing"].to_numpy()])
    meets = judged["meets"].to_numpy(dtype=float)
    reach = network.places_within(places, cell_centres_bng(cells), minutes)
    share = np.full(len(cells), np.nan)
    for position, found in enumerate(reach):
        if len(found) >= (minimum or MINIMUM_JUDGED):
            share[position] = 100.0 * meets[found].mean()
    return pd.Series(share, index=cells)

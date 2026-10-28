# S2: crime rates per hex cell

Status: done. A spike of step 0.4 ([roadmap](../roadmap.md#spikes)). Its code is [pipeline/notebooks/s2_crime_rates.py](../../pipeline/notebooks/s2_crime_rates.py), throwaway and never imported by `atlas`.

## Question

What crime rates per hex cell do 12 months of Police.uk data give, with smoothing?

## Answer

Rates per 1,000 residents work, with three choices that the spike made for them:

1. **Share each output area's residents between the cells it overlaps, by area.** Placing them at the output area's centroid left 38% of London's cells with no residents, and no rate.
2. **Pool each cell with its neighbours within two steps** (19 cells, about an 8-minute walk).
3. **Add a floor of 3,000 residents at the London-wide rate,** so that a cell with few residents around it does not top the ranking on a handful of crimes.

One problem remains open: rates per resident put the City of London at the top of every category (see Findings).

## What was done

1. Read 12 months (September 2025 to August 2026) of the Metropolitan Police's and the City of London Police's street-level files, straight from the latest data.police.uk archive (1.6 GB, a rolling 36 months for every force). That is 1,130,241 records, of which 0.06% have no location and 0.4% fall outside Greater London's cells.
2. Counted five groups of crimes, the five that the catalogue's crime indicators use, in H3 resolution 9 cells: burglary, violence and sexual offences, robbery and theft from the person, vehicle crime, and anti-social behaviour.
3. Took residents from Census 2021 (Nomis table TS001) by output area, and compared two ways of putting them on the grid: at each output area's population-weighted centroid, and shared by the area of overlap between the output area's boundary and each cell.
4. For each smoothing choice, split the year into alternate months, computed each half's rates, and measured how well the two halves rank the cells alike (Spearman rank correlation). A rate that is mostly noise ranks cells differently in each half, so higher agreement means more signal.

## Findings

**Residents.** Greater London has 8,800,816 residents in 16,883 cells, a median of 418 a cell. The centroid method gave 37.6% of cells none, because an output area in outer London is larger than a cell, and all of its residents land in one. Sharing by area leaves 0.3% of cells empty, and 19% with under 50 residents (parks, industry, the airport).

**London-wide rates a year per 1,000 residents.**

| Crime | Records in London's cells | Rate |
| --- | --- | --- |
| Burglary | 47,764 | 5.4 |
| Violence and sexual offences | 282,062 | 32.0 |
| Robbery and theft from the person | 104,041 | 11.8 |
| Vehicle crime | 82,622 | 9.4 |
| Anti-social behaviour | 233,718 | 26.6 |

**How much smoothing.** Agreement between the two halves of the year, by how many steps each cell pools (0 is the cell alone):

| Crime | 0 | 1 | 2 | 3 | 2, with a floor of 3,000 |
| --- | --- | --- | --- | --- | --- |
| Burglary | 0.55 | 0.64 | 0.67 | 0.72 | 0.76 |
| Violence and sexual offences | 0.83 | 0.87 | 0.91 | 0.93 | 0.94 |
| Robbery and theft from the person | 0.67 | 0.79 | 0.85 | 0.90 | 0.94 |
| Vehicle crime | 0.64 | 0.69 | 0.75 | 0.80 | 0.80 |
| Anti-social behaviour | 0.83 | 0.87 | 0.89 | 0.91 | 0.94 |

Burglary and vehicle crime are the noisiest, because they are the rarest per cell. Two steps reach cell centres about 600 m away, which is the distance the project already treats as a short walk (CIHT's 800 m acceptable distance for trips other than commuting, in the Daily amenities research). More steps would blur a neighbourhood into its surroundings for a smaller gain.

**Why a floor.** Even with two steps, 21% of cells have under 3,000 residents pooled around them, and among the 5% of cells with the highest rates, half of burglary's and vehicle crime's rest on such a thin denominator. A floor of 3,000 cuts that to 5% for burglary and 22% for vehicle crime, and raises the agreement for every crime. A floor of 10,000 raises it a little more, but is larger than the median pooled population (8,821), so it would flatten real differences.

**Per resident against per area.** The two rank cells differently: the rank correlation between the smoothed rate per resident and the count per cell is 0.45 to 0.67, and between 18% and 46% of the top-decile cells per resident are in the lower half by count. Cells with few residents and few crimes can have high rates, which is the reason for the floor. The rate per resident stays the measure, because it is the one people compare with their own street.

**The City of London.** The cell at the Bank junction has 1,908 residents pooled within two steps, and ranks above 96% to 100% of London's cells on all five crimes, even with the floor. The City has few residents and a very large workforce and many visitors, who are in the crime counts and not in the denominator. Other workplace and nightlife centres, such as the West End, are likely to behave the same way, which the spike did not check.

## Decisions

1. **Share residents by area, not at centroids.**
2. **Pool over two steps and add a floor of 3,000 residents.** The catalogue's crime method now says so, and the five crime measured indicators move to `spiked`.
3. **Keep the rate per 1,000 residents,** and say in the evidence layer that it overstates crime where few people live and many work or visit.
4. **Leave the City problem open.** A denominator of residents plus workers would fix it. The Census 2021 has workplace population tables, whose licence and geography would need checking, and it is a larger piece of work than this spike. It goes to the backlog for Phase 2.

## What it means for other spikes

- **S3 and S5** can reuse `residents_by_area` for any rate per resident, and the overlay pattern for sharing any area's value between hex cells. The whole script, including fetching 30,000 output areas' boundaries once, takes about a minute.
- **Windows.** `requests` and `scipy` join the `spikes` dependency group. The ONS's ArcGIS services page their results, and both the centroids and the boundaries are cached in `data/raw/census/` after the first run.
- **What was not tested.** Smoothing that weights near cells more than far ones, and how the answer changes with a different year. Police.uk's points are moved to anonymous map points, and the spike did not measure how much this moves crimes between cells.

## Reproduce

From `pipeline/`, with the data.police.uk archive in `data/raw/police/`, Census 2021's TS001 in `data/raw/census/`, and S1's contours in `data/raw/ptal/`:

```sh
uv run python notebooks/s2_crime_rates.py
```

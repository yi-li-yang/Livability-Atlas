# Scoring method v0

Status: draft (D06, proposed). Step 0.5 of Phase 0 finalises this method and adds golden test cases in `shared/fixtures/scoring/`. Terms are defined in the [glossary](../glossary.md).

## 1. Spatial framework

- **Hex cells.** The within-city scale scores H3 resolution 9 hex cells. They average 0.105 km², with edges of about 200 m, so each is about 350 m across. About 15,000 cover Greater London.
- **Buffer zone.** Measured indicators are computed over the region plus a 2 km ring around it, so a hex cell at the boundary still counts the parks and shops just outside. Only the region is displayed.
- **Neighbourhoods.** In the UK, neighbourhoods are MSOAs: census areas of about 8,000 residents, about 1,000 of them in London. The House of Commons Library's readable names label them on the map and in the ranked list.
- **Across-cities scale (Phase 3).** The unit becomes a city outline from the GHS Urban Centre Database. The rest of this method is unchanged.

Data reaches hex cells according to its type:

| Data type | Becomes | Example |
| --- | --- | --- |
| Points | A count within a walking distance, or the distance to the nearest | Shops, stations, crimes |
| Polygons | An area-weighted share | Parks, flood zones |
| Rasters | An area-weighted mean, computed with exactextract | Air quality, noise |
| Values for administrative areas | Joined to hex cells by containment | Council tax by borough |

## 2. The factor tree

Factors form a tree. Top-level factors split into sub-factors, which can split again, down to measured indicators: one number per hex cell, computed from a dataset.

```text
Environment                          ← one weight
├── Air quality                      ← own weight, opened in a dropdown
│   ├── NO₂, annual mean             ← measured indicator
│   └── PM2.5, annual mean
├── Noise
│   ├── Road traffic noise
│   ├── Rail noise
│   └── Aircraft noise
├── Green space
│   ├── Park area within a 10-min walk
│   └── Tree canopy cover
├── Water nearby (river, canal, lake)
└── Urban heat
```

## 3. Scoring curves

Each measured indicator has a scoring curve that turns its raw value into a score from 0 (worst) to 1 (best). Every curve has stated thresholds and a written justification in the factor catalogue.

| Shape | Definition | Example |
| --- | --- | --- |
| Rising or falling | Linear between two thresholds, flat outside them | PM2.5: 5 µg/m³ (WHO 2021 guideline) → 1; 25 µg/m³ → 0 |
| Ideal range | 0 at or below a, rising to 1 at b, 1 from b to c, falling to 0 at d | Summer temperature, with a band the user can move |
| Lookup | A score for each category | Flood risk band, with illustrative values: very low 1, low 0.75, medium 0.4, high 0 |
| Percentile (fallback) | Rank within the region | Only where no meaningful threshold exists |

**Why thresholds before percentiles.** With percentiles, every region's best hex cell scores 1, so a score means "good for this region", not "good". Thresholds keep scores comparable across regions, as long as the measured indicator itself is comparable (section 9).

## 4. Preference types

For some measured indicators everyone agrees on the direction. For others, people disagree: some like rain, others want none. Each measured indicator therefore has a preference type (D18).

| Preference type | Meaning | Examples | Default |
| --- | --- | --- | --- |
| Fixed | Everyone agrees which way is better | PM2.5, crime, flood risk, travel time | Thresholds from standards or evidence |
| User direction | People disagree on whether more is better | Rain, snow, wind, nightlife nearby, population density, distance to the centre, tourist crowds, schools nearby | The more common preference in surveys; one switch flips it |
| User range | People have an ideal band | Temperature, humidity, daylight hours, building age | A comfort band from the research literature; the user drags it |
| User choice | People pick what to look for | Industry, cuisines, community group, faith | Weight 0 until the user picks |

A user who cannot stand rain can also set a hard limit, e.g. fewer than 100 rainy days a year.

## 5. Weights and aggregation up the tree

Weights run from 0 (ignore) to 5 (crucial). A node's weight counts only against its siblings.

For one hex cell, a composite factor's score is the weighted mean of the scores of its children that have data and a weight above 0:

```text
S(n) = Σ w(c) · S(c) / Σ w(c)      both sums over c in A(n)
A(n) = the children of n that have data for this hex cell and w(c) > 0
S(i) = curve_i(x_i)                for a measured indicator i with raw value x_i
```

A node whose set A is empty has no score, and its parent leaves it out. The livability score is `100 × S(root)`, where the root's children are the top-level factors.

## 6. Hard limits

- A hard limit is a must-have rule on a raw value or a category, e.g. rent no higher than the user's cap, or flood risk not "high".
- Hard limits apply before scoring. Hex cells that fail one are shown grey and are not ranked.
- A hex cell that lacks the data a hard limit needs is kept, and flagged "could not check" for that limit.

## 7. Missing data and data coverage

Missing parts are skipped, and the remaining weights are renormalised (section 5). Data coverage tells the user how much of their weight a score rests on:

```text
p(i)     = product of w(x) / Σ w(siblings of x) along the path from the root to leaf i,
           counting all siblings with weight > 0, with or without data
coverage = Σ p(i) over the leaves that have data
```

Hex cells below 70% coverage are flagged.

## 8. Explanation: score contributions

```text
W(c) = product of w(x) / Σ w(y), over y in A(parent of x), along the path from the root to c
C(c) = 100 × W(c) × S(c)
```

Contributions add up at every level. The contributions of a node's children sum to the node's own contribution, and the contributions of the top-level factors sum to the livability score. The interface shows top-level contributions first and opens into sub-factors on demand ([interface.md](../interface.md)). Every measured indicator shows its confidence label: direct, estimate, proxy, perception or ranking.

## 9. Comparability across regions

Each measured indicator is marked comparable across regions or not. Satellite-derived PM2.5 means the same thing everywhere. Crime counts follow national definitions, so they do not. Views that compare regions use comparable measured indicators and say which ones are not.

## 10. Counting twice

Some factors overlap:

- PTAL overlaps door-to-door travel time.
- Deprivation indices already contain crime and income.
- Published rankings and resident wellbeing already reflect other factors.
- Brand presence partly mirrors house prices.

Composite indices and supporting factors therefore get low default weights, and the factor tree shows what overlaps.

## 11. Rules for ML

- No model produces the livability score.
- ML may produce measured indicators or estimates, such as rent where data is sparse. Each is labelled "estimate" or "perception".

## 12. Later

These features are in the [backlog](../backlog.md):

- a "no weak spots" mode that uses a weighted geometric mean
- a sensitivity view showing how stable the top 10 stays when weights shift by ±20%
- scoring curves that users can edit

## 13. Golden test cases (step 0.5)

These are fixed inputs with expected scores, which both the TypeScript engine and its Python copy must reproduce. They will cover:

- nested factor trees
- missing data and coverage
- hard limits
- flipped directions and ideal ranges
- lookup curves
- contributions that add up

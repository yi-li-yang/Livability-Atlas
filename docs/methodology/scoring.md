# Scoring method v0

Status: draft (D06, proposed). Step 0.5 of Phase 0 finalises this method and adds golden test cases in `shared/fixtures/scoring/`. Terms are defined in the [glossary](../glossary.md), and the symbols in the formulas under [Notation](#notation).

## Notation

Sections 3 to 8 compute everything for one hex cell under one preference profile, so the symbols leave the hex cell out. The formulas render on GitHub and in VS Code's Markdown preview.

| Symbol | Name | Meaning |
| --- | --- | --- |
| $n$ | node | Any factor in the factor tree: a top-level factor, a sub-factor or a measured indicator |
| $r$ | root | The top of the factor tree. Its children are the top-level factors |
| $c$, $k$ | child | A node one level below $n$. Sums use $k$ to run over the children |
| $i$ | measured indicator | A node at the bottom of the factor tree |
| $A(n)$ | active children | The children of $n$ that have a weight above 0 and a score in this hex cell |
| $w_n$ | weight | From 0 (ignore) to 5 (crucial), set by the user |
| $x_i$ | raw value | The value of measured indicator $i$ in this hex cell, in its unit. It can be missing |
| $f_i$ | scoring curve | The rule that turns $x_i$ into a score (section 3) |
| $t_0$, $t_1$ | thresholds | On a ramp, the raw values that score 0 and 1 |
| $l_0$, $l_1$, $u_1$, $u_0$ | ideal-range thresholds | On an ideal range, the lower ($l$) and upper ($u$) raw values that score 0 and 1. The subscript is the score |
| $s_n$ | score | From 0 (worst) to 1 (best). A node without data has no score |
| $L$ | livability score | From 0 to 100 |
| $P_n$ | share of total weight | How much of the whole factor tree $n$ accounts for, from the weights alone (section 5) |
| $D$ | data coverage | The share of total weight that has data in this hex cell (section 7) |
| $E_n$ | effective share | The share of total weight that $n$ carries in this hex cell, once missing parts are skipped (section 8) |
| $C_n$ | score contribution | The points of $L$ that $n$ adds (section 8) |

Section 8 ends with a [worked example](#worked-example).

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

Each measured indicator $i$ has a scoring curve $f_i$ that turns its raw value $x_i$ into a score from 0 (worst) to 1 (best). Every curve has stated thresholds and a written justification in the factor catalogue.

| Shape | Definition | Example |
| --- | --- | --- |
| Ramp (rising or falling) | 0 at threshold $t_0$ and 1 at threshold $t_1$, linear in between and flat beyond | PM2.5: $t_0 = 25$ µg/m³, $t_1 = 5$ µg/m³ (the WHO 2021 guideline) |
| Ideal range | 0 up to $l_0$, rising to 1 at $l_1$, 1 up to $u_1$, then falling to 0 at $u_0$ | Summer temperature, with a band the user can move |
| Lookup | A score for each category | Flood risk band, with illustrative values: very low 1, low 0.75, medium 0.4, high 0 |
| Percentile (fallback) | The share of the region's hex cells with a worse raw value | Only where no meaningful threshold exists |

A ramp is

```math
f(x) = \min\left(1,\ \max\left(0,\ \frac{x - t_0}{t_1 - t_0}\right)\right)
```

It rises when $t_1 > t_0$ and falls when $t_1 < t_0$. For PM2.5, a raw value of 9 µg/m³ scores $(9 - 25)/(5 - 25) = 0.8$.

An ideal range is the lower of two ramps: one rising from $l_0$ to $l_1$, and one falling from $u_1$ to $u_0$. With illustrative summer temperatures of $l_0 = 14$, $l_1 = 20$, $u_1 = 26$ and $u_0 = 32$ °C, 23 °C scores 1 and 29 °C scores 0.5.

```text
score
  1 |         ____________
    |        /            \
    |       /              \
  0 |______/                \______
           l0 l1         u1 u0   raw value
```

**Why thresholds before percentiles.** With percentiles, every region's best hex cell scores 1, so a score means "good for this region", not "good". Thresholds keep scores comparable across regions, as long as the measured indicator itself is comparable (section 9).

## 4. Preference types

For some measured indicators everyone agrees on the direction. For others, people disagree: some like rain, others want none. Each measured indicator therefore has a preference type (D18).

| Preference type | Meaning | Examples | Default |
| --- | --- | --- | --- |
| Fixed | Everyone agrees which way is better | PM2.5, crime, flood risk, travel time | Thresholds from standards or evidence |
| User direction | People disagree on whether more is better | Rain, snow, wind, nightlife nearby, population density, distance to the centre, tourist crowds, schools nearby | The more common preference in surveys; one switch flips it |
| User range | People have an ideal band | Temperature, humidity, daylight hours, building age | A comfort band from the research literature; the user drags it |
| User choice | People pick what to look for | Industry, cuisines, community group, faith | Weight 0 until the user picks |

Flipping a user direction swaps $t_0$ and $t_1$, so every score $s$ becomes $1 - s$. A user who cannot stand rain can also set a hard limit, e.g. fewer than 100 rainy days a year.

## 5. Weights and aggregation up the tree

Weights run from 0 (ignore) to 5 (crucial). A node's weight counts only against its siblings: children weighted 2 and 2 split their parent the same way as children weighted 5 and 5. A composite factor whose children all have weight 0 counts as weight 0.

**Share of total weight.** The root's share is 1. Each node splits its share among its children in proportion to their weights:

```math
\begin{aligned}
P_r &= 1 \\
P_c &= P_n \cdot \frac{w_c}{\sum_{k \in \mathrm{children}(n)} w_k} \quad \text{for each child } c \text{ of } n
\end{aligned}
```

The shares depend only on the weights, so they are the same in every hex cell. They are the areas the visual factor tree draws ([interface.md](../interface.md#visual-factor-tree)).

**Scores.** A measured indicator's score comes from its scoring curve. A composite factor's score is the weighted mean of its active children's scores. The livability score is the root's score times 100:

```math
\begin{aligned}
s_i &= f_i(x_i) \\
s_n &= \frac{\sum_{c \in A(n)} w_c \, s_c}{\sum_{c \in A(n)} w_c} \\
L &= 100 \, s_r
\end{aligned}
```

- A measured indicator whose raw value is missing has no score.
- A composite factor with no active children has no score, and its parent leaves it out. If the root has no score, the hex cell has no livability score.

## 6. Hard limits

- A hard limit is a must-have rule on a raw value or a category, e.g. rent no higher than the user's cap, or flood risk not "high".
- Hard limits apply before scoring. Hex cells that fail one are shown grey and are not ranked.
- A hex cell that lacks the data a hard limit needs is kept, and flagged "could not check" for that limit.

## 7. Missing data and data coverage

Missing parts are skipped, and the remaining weights are renormalised (section 5). Data coverage tells the user how much of their weight a score rests on. It adds up the shares of total weight of the measured indicators that have data:

```math
D = \sum_{i \text{ with data}} P_i
```

Hex cells with data coverage below 70% ($D < 0.7$) are flagged.

## 8. Explanation: score contributions

A node's effective share is its share of total weight as it works out in this hex cell. It is split the same way as $P$, but only among active children, so a child without a score passes its share to its active siblings. A node's score contribution is its effective share times its score, in points out of 100:

```math
\begin{aligned}
E_r &= 1 \\
E_c &= E_n \cdot \frac{w_c}{\sum_{k \in A(n)} w_k} \quad \text{for each active child } c \text{ of } n \\
C_n &= 100 \, E_n \, s_n
\end{aligned}
```

Nodes that are not active have no effective share and no contribution.

Contributions add up at every level. A node's score is the weighted mean of its active children's scores, so their contributions sum to the node's own contribution. The contributions of the top-level factors therefore sum to the livability score:

```math
\sum_{c \in A(n)} C_c = C_n
\qquad\qquad
\sum_{c \in A(r)} C_c = L
```

The interface shows top-level contributions first and opens into sub-factors on demand ([interface.md](../interface.md)). Every measured indicator shows its evidence type: direct, estimate, indirect, perception or ranking.

### Worked example

One hex cell, with illustrative numbers. Housing and cost and Transport are collapsed: their scores come from their own sub-factors in the same way, and all their data is present. Environment shows the other cases: a nested factor, a factor with no data in this hex cell (Noise) and a factor switched off (Green space). The columns are weight $w$, share of total weight $P$, raw value $x$, score $s$, effective share $E$ and score contribution $C$.

```text
                          w   P      x           s      E        C
Livability score (root)       1.00               0.59   1.00    59
├── Housing and cost      4   0.40               0.40   0.40    16
├── Transport             4   0.40               0.80   0.40    32
└── Environment           2   0.20               0.55   0.20    11
    ├── Air quality       3   0.10               0.55   0.20    11
    │   ├── NO₂           2   0.05   31 µg/m³    0.30   0.10     3
    │   └── PM2.5         2   0.05    9 µg/m³    0.80   0.10     8
    ├── Noise             3   0.10   no data     –      –        –
    └── Green space       0   0.00   not counted
```

1. **Scores of measured indicators** (section 3). NO₂ uses $t_0 = 40$ µg/m³ (the UK annual limit) and $t_1 = 10$ µg/m³ (the WHO 2021 guideline), so 31 µg/m³ scores $(31 - 40)/(10 - 40) = 0.30$. PM2.5 scores 0.80, as in section 3.
2. **Up the tree** (section 5). Air quality scores $(2 \times 0.30 + 2 \times 0.80)/(2 + 2) = 0.55$. Noise has no score and Green space has weight 0, so Air quality is Environment's only active child, and Environment also scores 0.55. The root scores $(4 \times 0.40 + 4 \times 0.80 + 2 \times 0.55)/(4 + 4 + 2) = 0.59$, so $L = 59$.
3. **Data coverage** (section 7). Environment's share of 0.20 splits into 0.10 for Air quality and 0.10 for Noise. The measured indicators with data hold 0.40 and 0.40 in the collapsed factors, and 0.05 each in NO₂ and PM2.5, so $D = 0.90$. That is at least 0.7, so the hex cell is not flagged.
4. **Contributions** (section 8). Noise has no data, so Air quality's effective share is 0.20, twice its share of total weight. The top-level contributions add up to the livability score, $16 + 32 + 11 = 59$, and inside Environment $3 + 8 = 11$.

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
- ML may produce measured indicators or estimates, such as rent where data is sparse. Each carries the evidence type "estimate" or "perception".

## 12. Later

These features are in the [backlog](../backlog.md):

- a "no weak spots" mode that uses a weighted geometric mean
- a sensitivity view showing how stable the top 10 stays when weights shift by ±20%
- scoring curves that users can edit

## 13. Golden test cases (step 0.5)

These are fixed inputs with expected scores, which both the TypeScript engine and its Python copy must reproduce. The worked example in section 8 becomes the first. They will cover:

- nested factor trees
- missing data and coverage
- hard limits
- flipped directions and ideal ranges
- lookup curves
- contributions that add up

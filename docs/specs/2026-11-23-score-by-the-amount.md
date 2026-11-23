# Score by the amount, never by rank

Status: approved by the owner on 2026-11-23, in plan mode. Decision D25. The implementation plan is [docs/plans/2026-11-23-score-by-the-amount.md](../plans/2026-11-23-score-by-the-amount.md).

## The problem

The owner showed the map with only "Renting cost" on: boroughs at £2,834 and £3,739 a month had the same colour.

38 of the 70 built measured indicators used the `percentile` curve. A percentile scores a hex cell by its rank among the region's cells with homes, so it shows the order and hides the amount. On bundle `36eb7eb8e423`:

- **One value per area.** Rent, council tax, life satisfaction and A&E waiting have one value per borough or per trust, so the score follows how many cells each area has. Rent: £905 more cost 5.5 points, and £5 more cost up to 6. Council tax: £7 a year moved a borough 10 points.
- **Long tails.** 26 indicators put 50% or more of their range into 5 points of score. Burglary at 55 a year per 1,000 residents looked the same as at 10.
- **Ties at zero.** "None nearby" scored in the middle: 42 for coworking and LGBTQ+ venues, 25 for water, nature sites and night services.

D06 already chose scoring curves with stated thresholds and rejected "percentile ranks everywhere". The percentile was the fallback where no standard sets thresholds, and it came to cover more than half of the indicators.

## The rule

Every curve scores by the amount, never by rank:

1. **A fixed ramp** where a standard or a natural scale gives the two ends, as for the 29 ramps already built.
2. **A region ramp** where nothing does. Its ends come from the region's own values, and the build writes them into the bundle as numbers, so every curve in a bundle has stated thresholds.

The `percentile` shape is removed: nothing uses it, and keeping it invites the same mistake.

## The region ramp

In the catalogue: `curve: {shape: region-ramp, better: lower|higher}`, with `log: true` for a log scale and, on a log scale, an `offset` (0 when left out). The word `scale` already names a factor's scales (within a city, across cities), so a curve does not use it.

**The ends.** The build takes the values of the hex cells with at least `homes.minimum` homes, the cells the app scores (D22). From each end it leaves out the most extreme cells, up to 1 in 100 of them, but never a value that 0.1% or more of the cells share, which is a whole area such as a borough. So:

- Rent and council tax lose nothing: their ends are the dearest and the cheapest borough.
- A value per cell loses the most extreme 1% at each end, so that one odd cell cannot stretch the scale.
- A count keeps 0 as its low end, and its top end falls at about the 99th percentile: for cafés, 118 against a maximum of 437.

**Straight or log.** A score is clip((f(x) − f(t₀)) / (f(t₁) − f(t₀))), with t₀ the end that scores 0:

- Straight (no `log`): f(x) = x, for shares, indices, times and distances.
- `log: true`: f(x) = ln(x + offset).
  - Offset 0 for money, rates and densities: each step of the same percentage counts the same, in any currency.
  - Offset 1 for counts of places nearby: none and one are a step apart, and the first few count most.
  - A value with x + offset ≤ 0 scores as the low end of the values.

**In the bundle** the build writes a plain ramp: `{shape: ramp, t0, t1, log, offset, from_region: true}`. A fixed ramp can use the same `log` and `offset`. The two scorers and the app then deal only with ramps, ideal ranges and lookups.

**Choice indicators.** "Your community" and "Your industry" score each option against its own ends, written on each option in the manifest.

**Format 2.** The bundle's `format_version` becomes 2, so an app and a bundle on either side of this change refuse each other rather than misread a curve.

**Equal ends.** Where a region has a single value, the indicator cannot tell its cells apart, so it gets no curve, and the QA report says so.

## The curve of each former percentile indicator

| Curve | Measured indicators |
| --- | --- |
| Region ramp, log | buying cost, renting cost, council tax; burglary, violence and sexual offences, robbery and theft from the person, vehicle crime, anti-social behaviour, road collisions; sales volume; job density, density |
| Region ramp, log, offset 1 (counts) | rail lines, bus routes, night services, cafés, restaurants, cuisines, LGBTQ+ friendly venues, cultural venues, listed buildings, nightlife, coworking; your industry (each option) |
| Region ramp, linear | price trend, water nearby, nature sites, distance to A&E, dentists, school league tables, diversity, residents who stay, years of good health; your community (each option) |
| Fixed ramp | A&E waiting: full marks at 95% within four hours (the NHS standard), none at the bottom of England's spread. Life satisfaction: across the range of the UK's local-authority means, so that a difference inside the survey's error looks small. School inspections and conservation areas: 0 to 100%, as food hygiene is. |

## Results on bundle 36eb7eb8e423 (scores out of 100)

| Rent a month | £3,739 | £3,209 | £2,834 | £2,349 | £1,833 | £1,693 | £1,540 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Percentile | 0.5 | 1.8 | 6 | 19 | 50 | 74 | 98 |
| Region ramp, log | 0 | 17 | 31 | 52 | 80 | 89 | 100 |

- Cafés: none scores 0, one 15, five 37, eleven 52, thirty 72 and 76 cafés 91.
- Every region ramp keeps a standard deviation of 16 to 27 points over the cells with homes.
- What looks harsh is the true picture of the amounts:
  - Council tax: 94% of cells score under 40, because Westminster and Wandsworth are about £1,000 a year below the rest.
  - Where most cells have none nearby (LGBTQ+ venues, coworking, water, nature sites), most cells now score 0.
- The livability score barely changes its spread. The rank colouring of the map (D24) still colours by fifths of the order, so it cannot show amounts.

## Curves tested and rejected (on the same bundle)

- **A linear ramp for money:** 60% to 64% of rent and buying cost fell in the top fifth.
- **The ratio to the region's median** (twice the median scores 0, half scores 1): no London rent scored above 63, and no council tax below 38.
- **A median-anchored log:** £247 a month bought 42 points on the cheap side and £1,906 bought 50 on the dear side.
- **Tukey fences, and a 5% trim kept to whole areas:** they cut whole boroughs, so Kensington and Chelsea and Westminster both scored 0.
- **Half percentile, half ramp:** £2,834 and £3,739 were only 18 points apart.
- **Ends at the 1st and 99th percentile of the cells:** they keep Kensington and Chelsea only because it holds 1.01% of the cells; a smaller borough at the end would be cut.
- **Ends at the 1st and 99th percentile of the distinct values:** they keep whole boroughs, but for counts the tail holds the distinct values, so the cafés' top end was 424 and most cells scored red.

## What the user sees

- **The map**, with only rent shown: £3,739 red, £2,834 orange, £2,349 yellow, the cheapest boroughs blue-green.
- **The legend**, when the map shows one measured indicator with a ramp: the ends give the values ("£3,739 a month" and "£1,540 a month") in place of "Worse" and "Better", the right way round when the user has flipped the direction.
- **The quick look and the phone peek:** "On the map: Renting cost, £2,834 a month, 31 out of 100".
- **Details, "How it scores":** "Full marks at £1,540 a month or less, none at 3,739 or more. Both ends come from London's own values." Then, for a log scale, "In between, each step of the same percentage counts the same", or for a count, "In between, the first few count most".

## Checks

- Both scorers reproduce a new golden case of log ramps, worked out by hand.
- The build's tests cover the ends: whole areas kept, 1% cut from cell values, 0 kept for a count, cells with few homes ignored, equal ends, each option of a choice.
- The QA report lists each region ramp's ends, straight or log, and the share of cells beyond each end. A check fails if an end lies outside the values; the bundle's model already refuses a log ramp with t + offset ≤ 0.
- On the rebuilt bundle, rent £3,739 scores 0, £2,834 scores 31 and £1,540 scores 100, in the app and in the reference scorer.

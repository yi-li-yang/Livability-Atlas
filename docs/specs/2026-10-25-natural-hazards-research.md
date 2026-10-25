# Natural hazards research

Status: built. The fifth MVP factor researched in Phase 0, step 0.2 ([roadmap](../roadmap.md)), with the `/research-factor` recipe.

## Scope

- **Researched:** flood risk from rivers and the sea, and from surface water, the Natural hazards row of the MVP candidates in the [research notes](../factors/research-notes.md).
- **Left as an idea:** subsidence, outside the MVP row. Its usual source, the British Geological Survey's GeoSure, is licensed commercially, so it needs its own look. Earthquakes, storms, wildfire and sea-level rise apply across cities, which waits for Phase 3.

## Measured indicators

| Measured indicator | Unit | Scoring curve | Evidence type | Comparable across regions | Dataset |
| --- | --- | --- | --- | --- | --- |
| Rivers and sea | % of the area | Ramp: 1 at 0%, 0 at 100% | estimate | no | Risk of Flooding from Rivers and Sea |
| Surface water | % of the area | Ramp: 1 at 0%, 0 at 100% | estimate | no | Risk of Flooding from Surface Water |

**The measure.** The Environment Agency maps flood risk on a 2 m grid, in four bands of the chance of flooding in any year: high (1 in 30 or more), medium (down to 1 in 100), low (down to 1 in 1,000) and very low. A hex cell holds thousands of these grid squares, often in several bands, so one band per hex cell would hide risk. Each measured indicator is instead the share of the hex cell's area in the medium or high band: a chance of 1 in 100 or more in any year. Its score is the share outside those bands. A YAML anchor shares this reason between the two.

**Evidence type and comparability.** The risk is modelled, so the evidence type is estimate. Countries model flood risk and count flood defences differently, so the share does not compare across regions.

## Datasets

| Dataset | Tier | Licence | Public builds |
| --- | --- | --- | --- |
| Risk of Flooding from Rivers and Sea, from the Environment Agency | country | Open Government Licence | yes |
| Risk of Flooding from Surface Water, from the Environment Agency | country | Open Government Licence | yes |

Both come from the National Flood Risk Assessment (NaFRA2) and cover England. Their product descriptions say they are available under the Open Government Licence, and their records set no access constraints. The rivers and sea product counts flood defences and the chance that they fail. Both also offer flood depths and climate change scenarios, which can follow later.

## Decisions to review

1. **The share of the area at medium or high risk**, rather than one band per hex cell.
2. **The 1 in 100 line**, from the Environment Agency's own bands, so that low and very low risk count as safe.
3. **Area, not homes**, until spike S5 decides whether homes give a better weight.

## Findings for the spikes

- **S5.** Whether to weight the flood shares by homes instead of area, and how to read a 2 m grid into hex cells.

## Testing

- Both catalogue files pass every check, and the explorer's tests pass, with a new case: a unit that starts with "%", such as "% of the area", follows its number without a space.
- The browser check passes.

## Done when

- The checks pass, the Artifact is published again, and the pull request is merged.

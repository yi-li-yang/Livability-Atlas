# Daily amenities research

Status: built. The sixth MVP factor researched in Phase 0, step 0.2 ([roadmap](../roadmap.md)), with the `/research-factor` recipe.

## Scope

- **Researched:** groceries, pharmacies, cafés, gyms and libraries (everyday amenities), and restaurant choice, cuisine variety and food hygiene (food and drink). That is the Daily amenities row of the MVP candidates in the [research notes](../factors/research-notes.md).
- **Left as ideas:** your cuisines, guide recognition, independent restaurants, brand presence and destinations, which the MVP row does not include. Several wait for spike S8, and destinations for Phase 2. The research notes keep their leads. Shopping applies across cities, which waits for Phase 3.

## Measured indicators

Three designs cover the eight measured indicators:

| Design | Measured indicators | Unit | Scoring curve |
| --- | --- | --- | --- |
| The walk to the nearest one | Groceries, pharmacies, gyms, libraries | minutes on foot | Ramp: 1 within 5 minutes, 0 at 15 minutes |
| How many within a 10-minute walk | Cafés, restaurant choice, cuisine variety | places or cuisines | Waits for spike S6 |
| How good the food hygiene is nearby | Food hygiene | % of food businesses | Ramp: the share rated 4 or 5 |

**Where the curves come from.**

- **The walk.** CIHT's guidelines (2000, Table 3.2) give 400 m as the desirable walking distance for trips other than commuting, and 1,200 m as the preferred maximum: about 5 and 15 minutes at the 4.8 km/h used throughout. The green space walk ends at the same 15 minutes.
- **The counts.** The 10-minute walk, 800 m, is CIHT's acceptable distance for the same trips. No standard says how many cafés or restaurants are enough, so their thresholds wait for spike S6's counts.
- **Food hygiene.** The Food Hygiene Rating Scheme rates food businesses from 0 to 5, and calls 4 good and 5 very good. The score is the share of nearby rated businesses at 4 or 5.

YAML anchors share the reasons, the methods and the list of place datasets between the measured indicators that use them.

**Evidence types.** Every measured indicator is direct except cuisine variety, which is indirect: variety is a sign of a lively food scene, not a measure of one. Food hygiene does not compare across regions, because Scotland rates hygiene under a different scheme.

**Cuisine variety** now applies within a city only, because it is measured within a walk. A variety for the whole city can return for the across-cities scale.

## Datasets

| Dataset | Tier | Licence | Public builds |
| --- | --- | --- | --- |
| Overture Maps Places | global | CDLA-Permissive-2.0, Apache-2.0 and CC0-1.0, by source | yes |
| OpenStreetMap, already in the catalogue | global | ODbL 1.0 | yes |
| Food Hygiene Rating Scheme ratings, from the Food Standards Agency | country | Open Government Licence v3.0 | yes |

**Overture's licences.** Overture licenses Places by source: most under CDLA-Permissive-2.0, Foursquare's records under Apache-2.0 with Foursquare's notice, and AllThePlaces under CC0-1.0. The catalogue records this as an SPDX expression, `CDLA-Permissive-2.0 AND Apache-2.0 AND CC0-1.0`, and the checks now accept an expression joined by AND when every licence in it is on D07's list. Overture already carries Foursquare's open places, so they need no entry of their own.

**The FSA's terms.** Users must show current ratings or the date they were updated, and must not suggest that the FSA endorses a business. The project shows shares of ratings, not single ones, and does not use the scheme's images.

## Decisions to review

1. **Walks for essentials, counts for choice.** Groceries, pharmacies, gyms and libraries are measured by the walk to the nearest one; cafés and restaurants by how many there are.
2. **One walking curve for every amenity**, from CIHT's distances for trips other than commuting.
3. **Food hygiene as the share rated good or very good.**

## Findings for the spikes

- **S6.** How complete Overture and OpenStreetMap are for each kind of place, and the counts that will set the thresholds for cafés, restaurants and cuisines.
- **S8.** How complete OpenStreetMap's cuisine tags are for London.

## Testing

- Both catalogue files pass every check, and the explorer's tests pass, with a new test for licences joined by AND.
- The browser check passes.

## Done when

- The checks pass, the Artifact is published again, and the pull request is merged.

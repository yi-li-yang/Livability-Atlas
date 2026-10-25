# Community and people research

Status: built. The ninth and last MVP factor researched in Phase 0, step 0.2 ([roadmap](../roadmap.md)), with the `/research-factor` recipe.

## Scope

- **Researched:** your community, diversity and faith, the Community and people row of the MVP candidates in the [research notes](../factors/research-notes.md): community composition and places of worship by faith.
- **Left as ideas:** the four sub-factors of community life, outside the MVP row, with leads in the research notes. English proficiency, expat communities, religious freedom and gender equality apply across cities, which waits for Phase 3.

## How the design follows D08

D08 includes community composition from Census 2021 (ethnicity, religion, country of birth, main language and life stage) at a default weight of 0, framed as the presence of a group the user chooses and as diversity, never as "fewer of group X". Each choice below follows from it:

- **Community composition keeps weight 0**, so it counts only when a user asks for it.
- **Your community scores presence only.** Its direction is fixed, higher being better, so a group's absence never adds to a score, and no setting turns it round.
- **Diversity also has a fixed direction**, more being better. A "less diverse" switch would let the tool rank places by fewer of some group in another form.
- **Residents who share a faith** count under your community, by religion, so that faith itself measures only the walk to a place of worship.

## Measured indicators

| Measured indicator | Preference type | Unit | Scoring curve | Datasets |
| --- | --- | --- | --- | --- |
| Your community | user choice | % of residents | Percentile, higher is better | Census 2021 topic summaries, output area boundaries |
| Diversity | fixed | diversity index, from 0 to 1 | Percentile, higher is better | Census 2021 topic summaries, output area boundaries |
| Faith | user choice | minutes on foot | Ramp: 1 within 5 minutes, 0 at 15 minutes | OpenStreetMap, Overture Places |

- **Your community.** The user picks a group by ethnic group, religion, country of birth, main language or five-year age band, the census's own categories. The measured indicator is that group's share of residents, from output areas, weighted by residents. No standard sets how present a group should be, so it scores by rank within the region.
- **Diversity.** Simpson's diversity index over the census's 19 ethnic groups: the chance that two residents picked at random belong to different groups. No standard sets a level, so it also scores by rank.
- **Faith.** The walk to the nearest place of worship of the chosen faith, on the same curve as the other everyday walks, from CIHT's distances for trips other than commuting. Spike S6 checks how complete the place data's religion tags are.

Census categories differ between countries, so your community and diversity do not compare across regions.

## Datasets

| Dataset | Tier | Licence | Public builds |
| --- | --- | --- | --- |
| Census 2021 topic summaries by output area, from the ONS through Nomis | country | Open Government Licence | yes |

The topic summaries are TS021 (ethnic group), TS030 (religion), TS004 (country of birth), TS024 (main language) and TS007A (five-year age bands), each published for output areas. The output area boundaries, OpenStreetMap and Overture Places are already in the catalogue.

## Decisions to review

1. **Fixed directions for your community and diversity**, as D08 requires.
2. **Percentile scores for both**, with no standard to draw on.
3. **Faith as the walk only**, with shared faith under your community.

## Testing

- Both catalogue files pass every check, and the explorer's 45 tests pass.
- The browser check passes.

## Done when

- The checks pass, the Artifact is published again, and the pull request is merged.

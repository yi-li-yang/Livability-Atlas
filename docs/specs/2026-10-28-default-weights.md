# Default weights and build order

Status: built. The D14 and build-order item of Phase 0, step 0.2 ([roadmap](../roadmap.md)).

## Scope

- Sets every top-level factor's `default_weight` from evidence, with a `weight_reason` (D14).
- Computes the build order: the sequence for turning the nine researched MVP candidates into working indicators, by weight and by how much of each candidate's research already has an open licence.
- Leaves sub-factor weights at the engineering default of 3, because none of D14's five sources give evidence below the top level. The already-set exceptions are untouched: community composition and the choice factors (`your-community`, `your-cuisines`, `faith`, `destinations`, `your-industry`) stay at 0 (D08, D18), and the two supporting factors (published rankings, resident wellbeing) stay at 1 (D14).

## The five sources

D14 names two kinds of source. Each is counted at the level of its own named categories, not its underlying indicators, because only the EIU's and Mercer's category names are verified; their indicator-level detail is not.

- **OECD Better Life Index** (11 topics): housing, income, jobs, community, education, environment, civic engagement, health, life satisfaction, safety, work-life balance.
- **EIU Global Liveability Index** (5 categories, weighted): stability 25%, healthcare 20%, culture and environment 25%, education 10%, infrastructure 20%.
- **Mercer Quality of Living** (the verified 2018 list of 10 categories, since Mercer's newer material gives examples rather than a complete list): political and social environment, economic environment, socio-cultural environment, medical and health, schools and education, public services and transport, recreation, consumer goods, housing, natural environment.
- **AARP Livability Index** (7 categories, each with named components): housing (costs, options, availability); neighbourhood (walkable, access to jobs, shops, restaurants and gathering places; personal safety); transportation; environment (sustainability, disasters, air and water); health (care access and quality); engagement (internet access, civic life); opportunity (economies, living wage, education).
- **English Housing Survey**, 2021–22 household moves fact sheet: owner-occupiers' reasons for moving home. It speaks only to housing, so it counts only there.

## Mapping sources to factors

Each source's named category counts once per factor it names, even where one category lists more than one component (AARP's and EIU's descriptions above name their components explicitly). `weight = max(1, count)`.

| Top-level factor | Sources that weigh it | Count | Weight |
| --- | --- | --- | --- |
| Housing and cost | OECD (housing), Mercer (housing), AARP (housing), EHS | 4 | 4 |
| Transport | EIU (infrastructure), Mercer (transport), AARP (transportation) | 3 | 3 |
| Daily amenities | Mercer (consumer goods, recreation), AARP (neighbourhood: shops, restaurants, gathering places) | 2 | 2 |
| Environment | OECD (environment), EIU (culture and environment), Mercer (natural environment), AARP (environment: sustainability, air, water) | 4 | 4 |
| Climate | — | 0 | 1 (floor) |
| Natural hazards | AARP (environment: disasters) | 1 | 1 |
| Safety | OECD (safety), EIU (stability), Mercer (safety), AARP (neighbourhood: personal safety) | 4 | 4 |
| Health care | OECD (health), EIU (healthcare), Mercer (medical and health), AARP (health) | 4 | 4 |
| Education | OECD (education), EIU (education), Mercer (schools and education), AARP (opportunity: education) | 4 | 4 |
| Community and people | OECD (community), AARP (engagement: civic life) | 2 | 2 |
| Culture and leisure | EIU (culture and environment), Mercer (recreation, socio-cultural environment) | 2 | 2 |
| Animal friendliness | — | 0 | 1 (floor) |
| Work and economy | OECD (income, jobs, work-life balance), Mercer (economic environment), AARP (neighbourhood: jobs; opportunity: economies, living wage) | 3 | 3 |
| Digital connectivity | AARP (engagement: internet access) | 1 | 1 |
| Urban form and change | — | 0 | 1 (floor) |
| Governance and rights | OECD (civic engagement), Mercer (political and social environment) | 2 | 2 |
| Published rankings | supporting factor (D14) | — | 1 |
| Resident wellbeing | supporting factor (D14); reinforced by OECD (life satisfaction) | — | 1 |

Two factors land on weight 3, the engineering default's own number, by coincidence of the count: Transport and Work and economy. Both still carry a `weight_reason`, so a reader cannot mistake a counted 3 for an unweighed placeholder; the explorer now requires a reason on every top-level factor for this reason (`explorer-core.js`).

## Decisions to review

Matching a source's own category names to our factors took judgement. The choices below are the ones most open to a different reading:

1. **One category can count for two of our factors, but only when its own description names two distinct concerns.** AARP's "neighbourhood" names personal safety alongside its walkable, shops-and-restaurants description, so it counts for both Safety and Daily amenities (and, through "access to jobs", Work and economy). AARP's "environment" names sustainability and disasters separately, so it counts for both Environment and Natural hazards. AARP's "engagement" names internet access and civic life separately, so it counts for both Digital connectivity and Community and people. EIU's "culture and environment" names both in its title, so it counts for both Culture and leisure and Environment. A single OECD topic is never split this way: each of its 11 topics went to exactly one of our factors.
2. **EIU's "stability" went to Safety, not Governance and rights.** Its own indicators (petty and violent crime, the threat of terror, military conflict and civil unrest) are security concerns, not rule of law or civil liberties. This is why Governance and rights draws on only the OECD and Mercer, not the EIU or AARP (which has no matching category at all).
3. **The English Housing Survey stayed scoped to Housing and cost.** Its "better neighbourhood or area" reason for moving is real, but the fact sheet does not break it down further, so stretching it to Safety, Daily amenities or Environment would be a guess rather than a reading of the source.
4. **Climate, Animal friendliness and Urban form and change land on the floor of 1 with zero matches**, not a stretched match. AARP's "environment" names only sustainability and disasters, not weather or temperature, so it was not counted for Climate. None of the five sources mentions pets, wildlife, density, building age or regeneration.
5. **Mercer's fuller, 2024 list of example factors was not used for counting**, because it reads as illustrative rather than exhaustive; the 2018 list of 10 categories is the one with a complete, named set.

## Build order

The nine researched MVP candidates, ranked by weight, then by how many of their researched measured indicators have every backing dataset cleared for public builds (the AND of each indicator's datasets, not the OR: an indicator with one open and one closed dataset is not counted as open).

| Order | Factor | Weight | Researched | Open now | Not yet open |
| --- | --- | --- | --- | --- | --- |
| 1 | Safety | 4 | 5 | 5 | — |
| 2 | Environment | 4 | 6 | 4 | `no2`, `pm25`: the LAEI and Defra background maps' licences are unconfirmed |
| 3 | Education | 4 | 3 | 3 | — |
| 4 | Housing and cost | 4 | 3 | 2 | `buying-cost`: its price dataset, HM Land Registry Price Paid, waits on Royal Mail's address-matching answer; its floor-area dataset is already open |
| 5 | Transport | 3 | 6 | 6 | — |
| 6 | Daily amenities | 2 | 8 | 8 | — |
| 7 | Community and people | 2 | 3 | 3 | — |
| 8 | Natural hazards | 1 | 2 | 2 | — |
| 9 | Digital connectivity | 1 | 2 | 2 | — |

The three "not yet open" gaps are already tracked as owner checks in `docs/progress.md`'s "Next": the LAEI's licence with the GLA, Defra's background maps on UK-AIR, and Royal Mail on Price Paid. None of them changes the order above, since each blocked factor still outranks every factor below it.

## Changes to the factor tree

- Every top-level factor's `default_weight` is set per the table above, each with a `weight_reason`.
- `explorer-core.js`: a top-level factor now always needs a `weight_reason`, not only when its weight differs from 3, since a top-level weight is never an untouched placeholder under D14. Sub-factors keep the old rule (a reason only when their weight differs from 3).
- `catalogue/factors.yaml`'s header comment, `catalogue/README.md`'s field reference, and the factor explorer's subtitle are reworded to match: top-level weights come from evidence, and only sub-factor weights remain a placeholder.

## Testing

- `node --test "docs/factors/*.test.mjs"`: 45 tests pass, including two new cases for the strengthened `weight_reason` rule.
- The catalogue check reports no problems.
- `node docs/factors/embed-catalogue.mjs --check` reports the embedded copy is up to date.
- The link check and markdownlint pass on every changed document.

## Done when

- The checks pass, the Artifact is published again, and the pull request is merged.

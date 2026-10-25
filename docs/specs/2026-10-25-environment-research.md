# Environment research

Status: built. The second MVP factor researched in Phase 0, step 0.2 ([roadmap](../roadmap.md)), with the `/research-factor` recipe. Air quality was researched with the [catalogue format](2026-10-24-catalogue-format.md).

## Scope

- **Researched:** road traffic noise, rail noise, aircraft noise, and the walk to a green space. With NO₂ and PM2.5, that covers the Environment row of the MVP candidates in the [research notes](../factors/research-notes.md).
- **Left as ideas:** tree canopy cover, water nearby and urban heat, which the MVP row does not include. The research notes keep their leads. Light pollution applies across cities, which waits for Phase 3.

## Changes to the factor tree

- **Park area within a 10-minute walk** becomes **Walk to a green space**: the walking minutes to the nearest public green space of at least 2 hectares. Natural England's standard is written as a size and a walking distance, so the indicator follows it. Its id changes from `park-area` to `walk-to-green-space`.
- **Noise** gets a description: it measures daytime noise. Night noise is a later addition.

## Measured indicators

| Measured indicator | Unit | Scoring curve | Evidence type | Comparable across regions | Datasets |
| --- | --- | --- | --- | --- | --- |
| Road traffic noise | dB (daytime) | Ramp: 1 at 50 dB, 0 at 70 dB | estimate | yes | Defra's strategic noise maps of roads |
| Rail noise | dB (daytime) | Ramp: 1 at 50 dB, 0 at 70 dB | estimate | yes | Defra's strategic noise maps of railways |
| Aircraft noise | dB (daytime) | Ramp: 1 at 51 dB, 0 at 63 dB | estimate | yes | Defra's strategic noise maps of airports |
| Walk to a green space | minutes on foot | Ramp: 1 within 4 minutes, 0 at 15 minutes | direct | yes | OS Open Greenspace, OpenStreetMap |

**Where the curves come from.**

- **Road and rail noise.** ProPG, the professional guidance on noise for new homes in England (ANC, IOA and CIEH, 2017), places a site at negligible risk at 50 dB LAeq,16h by day and at high risk at 70 dB (its Figure 1). ProPG applies its scale to all transport noise together, and here it scores each source alone, so that users can weight them apart. The WHO's guidelines (2018) use a different measure, Lden, and serve as context.
- **Aircraft noise.** The government's own thresholds: 51 dB LAeq,16h is the lowest level with adverse effects (Air Navigation Guidance, 2017), and at 63 dB it expects airports to help insulate homes (Aviation Policy Framework, 2013, paragraph 3.39). The WHO's guidelines also set a lower level for aircraft noise than for road or rail noise.
- **Walk to a green space.** Natural England's Accessible Greenspace Standard (user guide, 2024) asks for a natural green space of at least 2 ha within 300 m of home: about 4 minutes at the 4.8 km/h used for Transport. CIHT's guidelines (2000, Table 3.2) give 1,200 m, 15 minutes, as the preferred maximum walking distance for trips other than commuting. The indicator counts any public green space of that size, natural or not.

## Datasets

| Dataset | Tier | Licence | Public builds |
| --- | --- | --- | --- |
| Strategic noise maps of roads, railways and airports, England (Round 4, 2022), from Defra | country | Open Government Licence | yes |
| OS Open Greenspace, from Ordnance Survey | country | Open Government Licence | yes |
| OpenStreetMap, already in the catalogue | global | ODbL 1.0 | yes |

The noise maps are 10 m grids, modelled 4 m above the ground, down to 40 dB by day (35 dB at night). Their records on data.gov.uk name the Open Government Licence without a version and set no access constraints; version 3.0 is the one in force. Ordnance Survey gives its OS OpenData products the Open Government Licence, and names the version in the licence file of each download.

No London-only dataset was needed: the national datasets from Defra and Ordnance Survey cover London at fine resolution.

## Decisions to review

1. **One scale for road and rail noise**, ProPG's, applied to each source alone.
2. **Aircraft noise on the government's aviation thresholds**, not ProPG's scale.
3. **Daytime levels only.** Night noise, LAeq,8h or Lnight, can join each noise sub-factor later.
4. **Noise below the maps' cut-off counts as 40 dB**, which scores 1 for every source.
5. **Green space redefined** around Natural England's size and distance, counting parks that are not natural too.

## Findings for the spikes

- **S5.** How to average a noise grid over a hex cell: by area, by sound energy, or at homes only. Sound energy weights the loudest roads more.
- **S6.** The green space walk needs each site's access points, which OS Open Greenspace provides, and the walking network.

## Testing

- Both catalogue files pass every check, and the explorer's 44 tests pass.
- The browser check passes. Where it hovers over Noise, it now expects "3 of 3 measured indicators researched".

## Done when

- The checks pass, the Artifact is published again, and the pull request is merged.

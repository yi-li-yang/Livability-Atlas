# Transport research

Status: built. The first of the MVP factors researched in Phase 0, step 0.2 ([roadmap](../roadmap.md)), in the [catalogue format](2026-10-24-catalogue-format.md).

## Why

Transport comes first among the MVP factors, because PTAL is Phase 1's walking skeleton. This item researches Transport's measured indicators for the within-city scale, so that the spikes and the walking skeleton know what to compute, from which datasets, and how to score it.

## Scope

- **Researched:** walk to the nearest station, rail and Tube lines nearby, bus routes nearby, service level (PTAL), travel cost, and travel time to places.
- **Left as ideas:** night and step-free travel, and cycling, which the research notes place after the MVP. Airport connectivity and intercity rail apply across cities, which waits for Phase 3.

## Changes to the factor tree

- **Station proximity** is renamed "Walk to the nearest station", a plainer name. It counts any Tube, rail, DLR, Overground, Elizabeth line or tram station.
- **Line choice** splits into two measured indicators, rail and Tube lines nearby and bus routes nearby, because they are counted within different walks and in different units.
- **The walks are PTAL's.** Lines count at stations within a 12-minute walk (960 m) and routes at stops within an 8-minute walk (640 m), at 4.8 km/h. The seed tree said 10 and 5 minutes. PTAL's figures are TfL's own, and they keep every Transport indicator on the same walking assumptions.

## Measured indicators

| Measured indicator | Unit | Scoring curve | Evidence type | Comparable across regions | Datasets, best first |
| --- | --- | --- | --- | --- | --- |
| Walk to the nearest station | minutes on foot | Ramp: 1 within 6 minutes, 0 at 25 minutes | direct | yes | TfL Unified API, NaPTAN, OpenStreetMap |
| Rail and Tube lines nearby | lines | Waits for spike S6 | direct | no | TfL Unified API, OpenStreetMap |
| Bus routes nearby | routes | Waits for spike S6 | direct | no | TfL Unified API, OpenStreetMap |
| Service level | PTAL band | Lookup: equal steps from band 0 (0) to band 6b (1) | direct | no | PTAL |
| Travel cost | fare zone | Lookup: from the 2026 weekly caps, zones 1–2 score 1 and zone 9 scores 0 | direct | no | TfL Unified API |
| Travel time to places | minutes | Waits for spike S4 | direct | yes | TfL Unified API, OpenStreetMap |

**Where the curves come from.**

- **Walk to the nearest station.** CIHT's Guidelines for Providing for Journeys on Foot (2000), Table 3.2, gives walking distances for commuting: 500 m desirable, 1,000 m acceptable, 2,000 m preferred maximum. At TfL's 4.8 km/h, 500 m is about 6 minutes and 2,000 m is 25 minutes.
- **Service level.** TfL grades PTAL in nine bands, from 0 (worst) to 6b (best), and gives the bands no other weighting, so the scores rise in equal steps.
- **Travel cost.** TfL's adult rate prices for 2026 set weekly caps for pay-as-you-go travel from zone 1, from £44.70 for zones 1–2 to £116.40 for zones 1–9. Each zone's score falls in proportion to its cap. The fares are the curve's evidence, like the WHO's guidelines for NO₂, so they need no dataset entry. The scores need updating when fares change.
- **Curves that wait.** No standard says how many lines or routes are enough, so their thresholds wait for spike S6's counts. For travel time, the ONS reported in 2014 that personal well-being was lowest for commutes of 61 to 90 minutes. But the GLA found the effect of commute length small in London (2015), so the thresholds wait for spike S4's travel times. Each `curve_reason` says so.

## Datasets

| Dataset | Tier | Licence | Public builds |
| --- | --- | --- | --- |
| TfL Unified API: stations and stops, the lines serving them, fare zones, journey plans | city | TfL's open data licence | yes |
| Public Transport Accessibility Levels (PTAL), on the London Datastore | city | Open Government Licence v2.0 | yes |
| National Public Transport Access Nodes (NaPTAN), from the Department for Transport | country | Open Government Licence v3.0 | yes |
| OpenStreetMap | global | ODbL 1.0 | yes |

**TfL's licence and D07.** TfL's licence is version 2.0 of the Open Government Licence with TfL's amendments. It allows commercial use and redistribution, with the attribution "Powered by TfL Open Data", so it meets D07. It joins D07's allowed list under the id `LicenseRef-TfL-Open-Data`, because SPDX does not list it. Its amendments add registration for live feeds and a limit of 500 requests a minute per feed, and TfL may revise the licence without notice. The dataset's `licence_note` asks for a fresh check before each public build.

**Bus Open Data Service.** BODS publishes bus timetables for England outside London, where TfL's data serves instead. It becomes the country-tier dataset for bus routes when a second English city is added.

## Findings for the spikes

- **S1.** The London Datastore's PTAL release is from 2015, before the Elizabeth line opened. TfL's WebCAT is being updated, and its team supplies the latest PTAL data on request.
- **S4.** The travel-time curve waits for S4's travel times, as above.
- **S6.** The line and route counts, and the gap between walking routes and straight lines, inform the curves above.

## The factor explorer

- A lookup curve reads by its unit, with each category paired with its score: "by PTAL band: 6b → 1, 6a → 0.875, …".
- Non-breaking spaces keep each number with its unit, and each category with its score, when the tooltip wraps.
- The unit line reads "Unit: PTAL band" rather than "Measured in PTAL band", which suits units that are categories.

## Testing

- Unit tests, written first: TfL's licence passes D07's check; a lookup lists its categories from best to worst, even when they look like numbers; a lookup reads by its unit; and non-breaking spaces hold numbers to units.
- The catalogue check passes on both files.
- The browser check adds Transport. The datasets that public builds may use carry no flag, PTAL's curve reads by band, travel time shows no curve, and Getting around in general shows "5 of 7 measured indicators researched".

## Done when

- The unit tests, the catalogue check and the browser check pass.
- The Artifact is published again.
- The pull request is open, and it merges on the owner's word.

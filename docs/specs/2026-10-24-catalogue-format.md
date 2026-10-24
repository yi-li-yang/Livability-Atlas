# Catalogue format

Status: built. The owner approved the design in conversation. The second work item of Phase 0, step 0.2 ([roadmap](../roadmap.md)).

## Why

The rest of step 0.2 researches every factor. The top-down pass works out each measured indicator: its unit, its scoring curve and the datasets it comes from. The bottom-up pass lists datasets: their tier, their licence and what they can tell us. Both passes need somewhere to write their findings, and the seed catalogue holds only names and weights.

This work item adds that format. It defines the new fields, checks them and shows them in the factor explorer. It then proves the format on real research, Environment's two air-quality indicators, NO₂ and PM2.5, before the MVP factors are researched.

## What it does not do

- It downloads no data and computes nothing for hex cells. The status `built` arrives with the data pipeline.
- It researches no other factor. The MVP factors follow, one top-level factor per pull request.
- It writes no Markdown views of the catalogue. The Phase 0 plan asked for hand-written views of the factor tree, the dataset inventory and the table of which factors use which datasets. Hand-written copies of the YAML would drift from it. The factor explorer shows the same information now, and step 0.3's `just docs` will generate the Markdown views.

## Approach

**Chosen: measured indicators stay in `catalogue/factors.yaml`, as the bottom of the factor tree. Datasets get their own file, `catalogue/datasets.yaml`, and measured indicators name them by id.** Each licence is then recorded and checked once, even when many measured indicators share a dataset, which is what D07 needs.

Two alternatives were rejected:

- **Dataset details inside each measured indicator.** OpenStreetMap's licence would be repeated dozens of times, and the copies would drift apart.
- **One file for both.** It would be too large to review.

## Measured indicators

Every factor without sub-factors is a measured indicator ([glossary](../glossary.md#factors-and-scores)). While it is an idea, it needs only a name and a default weight, as now. Research adds these fields:

| Field | Meaning |
| --- | --- |
| `unit` | The unit of the raw value, such as `µg/m³` |
| `preference_type` | `fixed`, `user-direction`, `user-range` or `user-choice` (D18) |
| `curve` | The scoring curve: a `shape` and its thresholds, below |
| `curve_reason` | Why the curve is what it is, with its sources. Before a curve is chosen, it says what the choice waits for |
| `evidence_type` | `direct`, `estimate`, `indirect`, `perception` or `ranking` |
| `comparable_across_regions` | `true` or `false` |
| `method` | How the data becomes one number per hex cell |
| `datasets` | The ids of its datasets in `datasets.yaml`, best first |

**Scoring curves.** The four shapes of [scoring.md, section 3](../methodology/scoring.md#3-scoring-curves), with its notation. A curve's numbers are in the measured indicator's unit, and scores run from 0 (worst) to 1 (best).

| `shape` | Fields | Rule |
| --- | --- | --- |
| `ramp` | `t0`, `t1` | 0 at `t0` and 1 at `t1`, linear in between and flat beyond. It falls when `t1` is below `t0` |
| `ideal-range` | `l0`, `l1`, `u1`, `u0` | 0 up to `l0`, rising to 1 at `l1`, 1 up to `u1`, falling to 0 at `u0`. Needs `l0 < l1 ≤ u1 < u0` |
| `lookup` | `scores` | A score from 0 to 1 for each category |
| `percentile` | `better` | `higher` or `lower`. Only where no meaningful threshold exists |

scoring.md calls the first shape "rising or falling". From now on, scoring.md and the catalogue both call it a ramp, so that the shape keeps one name.

**What each research status requires.**

| Status | Requires |
| --- | --- |
| `idea` | `name` and `default_weight` |
| `researched` | Also `unit`, `preference_type`, `evidence_type`, `comparable_across_regions`, `method`, at least one dataset, and `curve_reason` |
| `spiked` | Also `curve` |
| `built` | The same as `spiked`, until the data pipeline adds its own requirements |

A field may appear before its status requires it, and is then checked as usual. A `curve` always needs a `curve_reason`, because scoring.md requires a written justification for every curve.

**Factors with sub-factors.** Only measured indicators carry the fields above. A factor with sub-factors has no research status of its own: the explorer shows how many of its measured indicators have been researched.

## Datasets

`catalogue/datasets.yaml` lists every dataset that a measured indicator names, and every dataset the bottom-up pass finds worth recording.

| Field | Required | Meaning |
| --- | --- | --- |
| `id` | yes | A unique kebab-case name, such as `laei` |
| `name` | yes | Its plain name |
| `publisher` | yes | Who publishes it |
| `url` | yes | Its landing page |
| `tier` | yes | `city`, `country` or `global` (dataset tier, D16) |
| `area` | yes | The area it covers, such as `Greater London` |
| `resolution` | yes | How fine it is, such as `20 m grid` or `points` |
| `date` | yes | The period it describes, such as `2022` |
| `licence` | yes | An [SPDX licence id](https://spdx.org/licenses/), such as `OGL-UK-3.0`, or `unknown` until the licence is confirmed |
| `licence_checked` | when `public_build` is true | The date the licence was last checked at the source |
| `public_build` | yes | Whether public builds may use it (D07) |
| `licence_note` | when `public_build` is false | Why public builds may not use it, and what would change that |
| `attribution` | when `public_build` is true | The credit the licence requires |
| `tells` | yes | A list of what it can tell us |
| `credibility` | for published rankings | `high`, `medium` or `low` ([research notes](../factors/research-notes.md#credibility-of-published-rankings)) |
| `credibility_reason` | with `credibility` | Why |

**D07 becomes a rule.** A dataset marked `public_build: true` needs a licence from D07's allowed list, which allows redistribution and commercial use, and the date its licence was checked. The allowed list, by SPDX id:

- the Open Government Licence: `OGL-UK-1.0`, `OGL-UK-2.0`, `OGL-UK-3.0`
- Creative Commons: `CC-BY-3.0`, `CC-BY-4.0`, `CC-BY-SA-3.0`, `CC-BY-SA-4.0`, `CC0-1.0`
- `ODbL-1.0`
- `CDLA-Permissive-1.0`, `CDLA-Permissive-2.0`
- `Apache-2.0`

D07 records the same list. A dataset whose licence is `unknown` stays out of public builds until its licence is confirmed at the source.

## Checks

The checks live in `docs/factors/explorer-core.js`, beside the existing ones, and are written test first. From step 0.3, `atlas validate` takes them over. They reject:

- an unknown field, in a factor or a dataset, so that a misspelt field name does not pass unseen
- a value outside its allowed list: preference type, evidence type, curve shape, tier, credibility
- a curve that breaks its shape's rule, or has no `curve_reason`
- a `user-range` measured indicator without an `ideal-range` curve, because its user drags a band
- a measured indicator that lacks a field its status requires
- measured-indicator fields, or a status, on a factor with sub-factors
- a dataset id that `datasets.yaml` does not have, or that is listed twice
- a measured indicator of evidence type `ranking` whose datasets have no credibility rating
- a dataset that lacks a required field, or has a malformed `url` or `licence_checked` date
- `public_build: true` without an allowed licence, a `licence_checked` date and an `attribution`
- `public_build: false` without a `licence_note`

YAML reads an unquoted `2022` as a number and an unquoted `2026-10-24` as a date. The checks accept both forms, so that `date: 2022` and `licence_checked: 2026-10-24` need no quotes.

## The factor explorer

- **Two embedded files.** The page embeds `datasets.yaml` beside `factors.yaml`, each in its own `<script type="text/yaml">` block, with the ids `factors` and `datasets`. `embed-catalogue.mjs` refreshes both, and its drift test covers both. If either file fails to parse or fails a check, the page draws nothing and lists every problem.
- **The tooltip of a measured indicator** adds four things:
  - its unit
  - its scoring curve, in words, such as "1 at 10 µg/m³ or less, falling to 0 at 40 µg/m³ or more"
  - its evidence type
  - its datasets, best first, each with its tier and licence. A dataset that public builds may not use is flagged "not in public builds", in words, not by colour alone.
- **Research status.** A measured indicator's tooltip shows its status. A factor with sub-factors shows how many of its measured indicators at this scale are researched or further, such as "2 of 2 measured indicators researched".
- **Design.** This extends the existing page, in the web-design-engineer skill's sense: the new tooltip lines reuse its type, sizes and ink colours. The flag is the one new style, set in ink at weight 600 so that it stands out without colour. Colour on the page still means only data.

## Proving the format: NO₂ and PM2.5

Both measured indicators move to status `researched`, with these findings.

**Scoring curves.** Both are ramps that fall, with both thresholds from published standards, and match scoring.md's examples:

- NO₂ scores 1 at 10 µg/m³, the WHO's 2021 guideline for the annual mean, and 0 at 40 µg/m³, the UK's legal limit for the annual mean, which is also the WHO's first interim target.
- PM2.5 scores 1 at 5 µg/m³, the WHO's 2021 guideline, and 0 at 25 µg/m³, the WHO's second interim target. The first interim target, 35 µg/m³, would leave most of the curve unused in the UK, where every compliance zone met the legal limit of 20 µg/m³ in 2023 and 2024.

**Evidence type: estimate.** Both datasets are modelled concentrations, worked out by a model from emissions and a sparse network of monitors. That is the glossary's meaning of "estimate". The approved design's example said `direct`, as an illustration only.

**Datasets, best first.**

| Dataset | Tier | Resolution | Licence |
| --- | --- | --- | --- |
| London Atmospheric Emissions Inventory (LAEI) 2022, from the GLA and TfL | city | 20 m grid | The London Datastore gives the licence as "Not Specified", for the 2022 and 2019 editions alike. Its terms let anyone use its data for any purpose, but name no licence |
| Background maps for local air quality management, from Defra and the devolved administrations | country | 1 km grid | Not confirmed. UK-AIR, which hosts the files, was offline on the day of the check. A council's copy credits the maps as Crown copyright under the Open Government Licence, but also calls them "specifically for LAQM purposes only" |

Neither licence can be confirmed yet, so both datasets are marked `public_build: false`, each with a `licence_note`. Air quality can go into local builds now, and into a public build once the GLA confirms the LAEI's licence or UK-AIR's terms are checked. Both actions go into the progress log as next steps for the owner.

The LAEI comes first because its 20 m grid resolves the higher concentrations beside roads. Defra's maps give background concentrations only: what remains if local sources such as roads are removed. They stand in where no city dataset exists, and they cover the whole UK.

## Living documents

- `catalogue/README.md`: the field reference for both files, kept as the living copy of the tables above.
- `catalogue/factors.yaml`: a header that points to the reference.
- [glossary.md](../glossary.md): "Ramp" under "Scoring method", and "Public build" under "Data pipeline", both in the contributors' part.
- [scoring.md](../methodology/scoring.md), section 3: the rising or falling curve is named "ramp". D06 gets a history line.
- [decisions.md](../decisions.md), D07: the allowed list by SPDX id, and a history line.
- `CONTRIBUTING.md`: the recipes for adding a factor and a dataset point to the field reference.
- [research-notes.md](../factors/research-notes.md): "Catalogue fields still to come" keeps only what is still to come: each dataset's update cadence, access method and cost.
- `docs/factors/README.md`, `docs/codemap.md` and `docs/tech-stack.md`: the second embedded file.
- [progress.md](../progress.md): pull request #2 merged, this item, and the two licence actions.

## Testing

The unit tests are written before the code:

- The worked example of scoring.md still passes every check, with or without datasets.
- Every rule under [Checks](#checks) has a case that breaks it and expects its problem, naming the factor or dataset.
- A researched measured indicator with every field passes. Removing any one of its required fields fails, naming that field.
- `public_build: true` passes with an allowed licence, a date and an attribution, and fails with `unknown`, `CC-BY-NC-4.0` or a missing date.
- The curve in words reads correctly for a falling ramp, a rising ramp, an ideal range, a lookup and a percentile.
- The research status of a factor with sub-factors counts its measured indicators at the current scale.
- The embedded copies of both files match the catalogue, and refreshing one block leaves the other alone.

The browser check, run from a scratch folder as before, adds:

- The page loads both files with no problems.
- Hovering over NO₂ shows its unit, its curve in words, its evidence type and both datasets, each flagged "not in public builds".
- Hovering over Air quality shows "2 of 2 measured indicators researched".
- The tooltip stays inside the window at phone width.

## Done when

- The unit tests and the browser check pass, and the embedded copies are current.
- The Artifact is published again and shows the research.
- The pull request is open. It merges on the owner's word.

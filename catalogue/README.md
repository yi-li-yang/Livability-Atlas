# Factor catalogue

The machine-readable factor catalogue. The [glossary](../docs/glossary.md) defines its terms, and the [catalogue format spec](../docs/specs/2026-10-24-catalogue-format.md) explains its design.

| File | What it holds |
| --- | --- |
| `factors.yaml` | The factor tree, with every factor's default weight and the reason for it. A factor without sub-factors is a measured indicator, and research fills in how it is measured and scored |
| `datasets.yaml` | Every dataset that a measured indicator uses or may use, with its tier and licence, and what it can tell us |

The regions and the presets arrive in later steps.

## factors.yaml

Every factor has these fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `id` | yes | A unique kebab-case name, such as `air-quality` |
| `name` | yes | The plain name the app shows |
| `default_weight` | yes | A whole number from 0 to 5 |
| `weight_reason` | on every top-level factor, and elsewhere when the weight is not 3 | Why the default weight is what it is. A top-level factor's reason names how many of D14's five sources weigh it ([spec](../docs/specs/2026-10-28-default-weights.md)) |
| `description` | no | One sentence |
| `scales` | on top-level factors | `within-city`, `across-cities`, or both. A sub-factor inherits its parent's scales, or lists a subset of them |
| `children` | no | The sub-factors |

### Measured indicators

A factor without sub-factors is a measured indicator. These fields belong to measured indicators only:

| Field | Meaning |
| --- | --- |
| `status` | Its research status: `idea` (if left out), `researched`, `spiked` or `built` |
| `unit` | The unit of the raw value, such as `µg/m³` |
| `preference_type` | `fixed`, `user-direction`, `user-range` or `user-choice` (D18) |
| `curve` | The scoring curve, below |
| `curve_reason` | Why the curve is what it is, with its sources. Before a curve is chosen, it says what the choice waits for |
| `evidence_type` | `direct`, `estimate`, `indirect`, `perception` or `ranking` |
| `comparable_across_regions` | `true` or `false` |
| `method` | How the data becomes one number per hex cell |
| `datasets` | The ids of its datasets in `datasets.yaml`, best first |

The research status decides which fields are required:

| Status | Requires |
| --- | --- |
| `idea` | Only `name` and `default_weight` |
| `researched` | `unit`, `preference_type`, `evidence_type`, `comparable_across_regions`, `method`, at least one dataset, and `curve_reason` |
| `spiked` | Also `curve` |
| `built` | The same as `spiked`, until the data pipeline adds its own requirements |

A field may appear before its status requires it. A factor with sub-factors has no status of its own: the factor explorer shows how many of its measured indicators are researched.

### Scoring curves

A curve's numbers are in the measured indicator's unit, and scores run from 0 (worst) to 1 (best), as in [scoring.md](../docs/methodology/scoring.md#3-scoring-curves). Every curve needs a `curve_reason`.

| `shape` | Fields | Rule | Example |
| --- | --- | --- | --- |
| `ramp` | `t0`, `t1` | 0 at `t0` and 1 at `t1`, linear in between and flat beyond | `{shape: ramp, t0: 25, t1: 5}` |
| `ideal-range` | `l0`, `l1`, `u1`, `u0` | 0 up to `l0`, 1 from `l1` to `u1`, 0 from `u0`, linear in between. Needs `l0 < l1 ≤ u1 < u0` | `{shape: ideal-range, l0: 14, l1: 20, u1: 26, u0: 32}` |
| `lookup` | `scores` | A score from 0 to 1 for each category | `{shape: lookup, scores: {low: 1, medium: 0.4, high: 0}}` |
| `percentile` | `better` | `higher` or `lower`. Only where no meaningful threshold exists | `{shape: percentile, better: lower}` |

A `user-range` measured indicator needs an `ideal-range` curve, because its user drags the band.

## datasets.yaml

| Field | Required | Meaning |
| --- | --- | --- |
| `id` | yes | A unique kebab-case name, such as `laei` |
| `name` | yes | Its plain name |
| `publisher` | yes | Who publishes it |
| `url` | yes | Its landing page |
| `tier` | yes | `city`, `country` or `global` |
| `area` | yes | The area it covers |
| `resolution` | yes | How fine it is, such as `20 m grid` or `points` |
| `date` | yes | The period it describes, such as `2022` |
| `licence` | yes | An [SPDX licence id](https://spdx.org/licenses/), such as `OGL-UK-3.0`, or `unknown` until the licence is confirmed at the source. A licence that SPDX does not list takes a `LicenseRef-` id, such as `LicenseRef-TfL-Open-Data`. A dataset under several licences at once joins them with AND, such as `CDLA-Permissive-2.0 AND Apache-2.0` |
| `licence_checked` | when `public_build` is true | The date the licence was last checked at the source |
| `public_build` | yes | Whether public builds may use it (D07) |
| `licence_note` | when `public_build` is false | Why public builds may not use it, and what would change that |
| `attribution` | when `public_build` is true | The credit the licence requires |
| `tells` | yes | A list of what it can tell us |
| `credibility` | for published rankings | `high`, `medium` or `low`. A measured indicator of evidence type `ranking` needs it on each of its datasets |
| `credibility_reason` | with `credibility` | Why |

**Public builds (D07).** A dataset may go into public builds only under a licence that allows redistribution and commercial use. By SPDX id, those are:

- `OGL-UK-1.0`, `OGL-UK-2.0` and `OGL-UK-3.0`
- `CC-BY-3.0`, `CC-BY-4.0`, `CC-BY-SA-3.0`, `CC-BY-SA-4.0` and `CC0-1.0`
- `ODbL-1.0`
- `CDLA-Permissive-1.0` and `CDLA-Permissive-2.0`
- `Apache-2.0`
- `LicenseRef-TfL-Open-Data`: TfL's open data licence, version 2.0 of the Open Government Licence with TfL's amendments

A dataset marked `public_build: true` also needs its `licence_checked` date and its `attribution`. When its licences are joined with AND, every one of them must be on the list.

## Checks

`atlas validate` checks both files, and `just validate` and CI run it. Its rules are the Pydantic models in `pipeline/src/atlas/catalogue/models.py`, and the checks across records in `checks.py`. The checks reject unknown fields, so a misspelt field name does not pass unseen. The [factor explorer](../docs/factors/README.md) keeps its own copy of the checks until it moves into the web app, and lists any problem whenever it loads, instead of drawing.

YAML reads an unquoted `2022` as a number and an unquoted `2026-10-24` as a date. The checks accept both, so neither needs quotes. Two more points about YAML:

- Text that contains a colon followed by a space, such as `Source: Office for National Statistics`, needs quotes or a `>-` block, or YAML reads it as a new field.
- An anchor shares one text between several factors: `&name` marks the first copy and `*name` repeats it, as the crime indicators do for their method.

After editing either file, refresh the explorer's copy and run its tests:

```sh
just docs
just check
```

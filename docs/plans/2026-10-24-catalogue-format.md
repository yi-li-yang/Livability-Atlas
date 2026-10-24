# Catalogue format implementation plan

> **For agentic workers:** carry out this plan task by task, inline, with superpowers:executing-plans and superpowers:test-driven-development. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the catalogue format in [the spec](../specs/2026-10-24-catalogue-format.md): measured-indicator fields in `catalogue/factors.yaml`, a new `catalogue/datasets.yaml`, their checks, and the factor explorer showing them. Then prove it on NO₂ and PM2.5.

**Architecture:** The checks, the curve in words and the research-status count go into `docs/factors/explorer-core.js`, which the page and the tests both load. `embed-catalogue.mjs` copies both YAML files into the page, each into its own block. The page parses both, lists any problem from either, and adds the new lines to its tooltip.

**Tech stack:** as for the factor explorer. Plain JavaScript, Node 24's test runner, js-yaml 4.1 and D3 7.9 from cdnjs, and `playwright-core` in a scratch folder for the browser check.

---

## Shared setup

Commands run from the repo root, `E:/GitHub/Livability-Atlas`, in Git Bash. `SP` is the session's scratchpad. It holds the tools from the factor explorer work: the documentation check (`check_links.py` and markdownlint in `mdtools/`), and the browser check (`check-explorer.cjs`, with `playwright-core` in `browser-check/`). In a new session, recreate them first, as the [factor explorer plan](2026-10-24-factor-explorer.md) describes.

## Files

| File | Task | Change |
| --- | --- | --- |
| `docs/plans/2026-10-24-catalogue-format.md`, `docs/specs/2026-10-24-catalogue-format.md`, `docs/progress.md` | 1 | This plan and the spec; progress records pull request #2 as merged |
| `docs/factors/explorer-core.js`, `docs/factors/explorer-core.test.mjs` | 2–4 | The checks for measured indicators and datasets; normalising datasets; the curve in words; research progress |
| `docs/factors/embed-catalogue.mjs`, `docs/factors/embed-catalogue.test.mjs` | 5 | Two embedded blocks, `factors` and `datasets` |
| `catalogue/datasets.yaml`, `catalogue/factors.yaml` | 6 | The two datasets; NO₂ and PM2.5 researched |
| `docs/factors/explorer.html` | 7 | Loads both blocks; the new tooltip lines |
| scratch only: `check-explorer.cjs` | 8 | The browser check's new steps |
| `catalogue/README.md`, glossary, scoring.md, decisions.md, `CONTRIBUTING.md`, research notes, `docs/factors/README.md`, codemap, tech stack, progress | 9 | The living documents |

## Task 1: Spec, plan and progress

- [ ] Write the spec and this plan.
- [ ] In `docs/progress.md`, record that pull request #2 merged, and make this item "Now".
- [ ] Run the documentation check (links and markdownlint) on the three files, then commit: `docs: add the catalogue format spec and plan`.

## Task 2: Checks for measured indicators (test first)

`validateCatalogue(catalogue, datasetsDoc = { datasets: [] })` keeps its current checks and adds the measured-indicator rules. The second argument is the parsed `datasets.yaml`, used only to check references.

- [ ] Add a test helper `researched()` that returns a complete researched measured indicator, and a helper `datasetsDoc()` that returns one valid dataset.
- [ ] Write failing tests:
  - The worked example passes, with and without `datasetsDoc()`.
  - A complete researched measured indicator passes.
  - Removing each of `unit`, `preference_type`, `evidence_type`, `comparable_across_regions`, `method`, `datasets` and `curve_reason` from it fails, naming the field.
  - At status `spiked`, a missing `curve` fails.
  - Each value outside its list fails: preference type, evidence type, curve shape, `better`.
  - Broken curves fail: a ramp with `t0` equal to `t1`, a ramp without numbers, an ideal range out of order, a lookup with a score above 1, a curve without `curve_reason`.
  - `user-range` with a ramp fails.
  - A factor with sub-factors fails when it has a `unit` or a `status`.
  - An unknown field fails, naming it.
  - An unknown dataset id fails, and so does a dataset id listed twice.
  - Evidence type `ranking` fails when a dataset has no credibility rating, and passes when it has one.
- [ ] Run `node --test "docs/factors/*.test.mjs"` and see the new tests fail.
- [ ] Implement the rules in `explorer-core.js`, with each allowed list as a constant.
- [ ] Run the tests and see all pass. Commit: `feat(catalogue): check measured indicators`.

## Task 3: Checks for datasets (test first)

`validateDatasets(datasetsDoc)` returns problems, each starting `dataset <id>:`.

- [ ] Write failing tests:
  - `datasetsDoc()` passes, and an empty list passes.
  - A document without a `datasets` list fails.
  - Each required field, when missing, fails: `name`, `publisher`, `url`, `tier`, `area`, `resolution`, `date`, `licence`, `public_build`, `tells`.
  - A duplicate id, a non-kebab-case id, an unknown tier, a `url` without `http`, and an unknown field each fail.
  - `public_build: true` passes with `OGL-UK-3.0`, a `licence_checked` date given as a string or a date, and an `attribution`. It fails with `unknown`, with `CC-BY-NC-4.0`, without `licence_checked`, and without `attribution`.
  - `public_build: false` fails without a `licence_note`.
  - `credibility` outside high, medium and low fails, and so does `credibility` without `credibility_reason`.
  - `date: 2022`, read by YAML as a number, passes.
- [ ] See them fail, implement `validateDatasets` with `OPEN_LICENCES` as the D07 list, and see them pass. Commit: `feat(catalogue): check datasets and enforce D07`.

## Task 4: Normalising and describing (test first)

- [ ] Write failing tests:
  - `normaliseCatalogue` carries the measured-indicator fields, and `buildTree` shows them on each view.
  - `buildTree` gives each view `progress`: the count of its measured indicators at that scale, and how many are researched or further. Air quality in a catalogue with two researched measured indicators shows 2 of 2. At the other scale, where they do not apply, it is itself a measured indicator at status idea, 0 of 1.
  - `normaliseDatasets` returns a map by id, with `licence_checked` as `YYYY-MM-DD` whether YAML gave a string or a date, and `date` as text.
  - `describeCurve` gives:
    - for a falling ramp: `1 at 10 µg/m³ or less, falling to 0 at 40 µg/m³ or more`
    - for a rising ramp: `0 at 2 km² or less, rising to 1 at 8 km² or more`
    - for an ideal range: `1 from 20 to 26 °C, falling to 0 at 14 °C or less and at 32 °C or more`
    - for a lookup: `by category: very low 1, low 0.75, high 0`
    - for a percentile: `by rank within the region, where higher values score better`
    - with the unit `%`, no space before the unit
- [ ] See them fail, implement, and see them pass. `buildTree` builds each view from the normalised node's own fields, so new fields reach the view without being listed twice. Commit: `feat(explorer): carry the research into the tree, and describe curves`.

## Task 5: Two embedded blocks (test first)

- [ ] Change the tests to the new interface. `embed(html, name, yaml)` and `embeddedCopy(html, name)` take `name` as `factors` or `datasets`. `SOURCES` maps each name to its YAML file.
- [ ] Write failing tests:
  - Embedding the `datasets` block leaves the `factors` block unchanged.
  - A page without the named block throws, naming it.
  - The drift test checks both blocks against their files.
- [ ] See them fail, implement, and see them pass. The command line refreshes both blocks. With `--check`, it names each block that is out of date. Commit: `feat(explorer): embed datasets.yaml beside factors.yaml`.

The drift test fails until Task 7 adds the `datasets` block to the page. Tasks 5 to 7 are therefore committed together, once the drift test passes.

## Task 6: The catalogue

- [ ] Write `catalogue/datasets.yaml`, with a header and the datasets `laei` and `defra-background-maps`, as in the spec.
- [ ] In `catalogue/factors.yaml`, fill in `no2` and `pm25` as in the spec, and update the header to point to `catalogue/README.md`.
- [ ] Check both files once, with conda's PyYAML turning them into JSON for `explorer-core.js`:

```bash
for f in factors datasets; do PYTHONUTF8=1 python -I -c "import json, sys, yaml; json.dump(yaml.safe_load(open(sys.argv[1], encoding='utf-8')), sys.stdout, default=str)" "catalogue/$f.yaml" > "$SP/$f.json"; done
node -e "
const core = require('./docs/factors/explorer-core.js');
const read = (f) => JSON.parse(require('fs').readFileSync(process.argv[1] + '/' + f + '.json', 'utf8'));
const factors = read('factors'), datasets = read('datasets');
const problems = [...core.validateDatasets(datasets), ...core.validateCatalogue(factors, datasets)];
console.log(problems.length ? problems.join('\n') : 'OK: no problems');
" "$SP"
```

Expected: `OK: no problems`.

## Task 7: The page

- [ ] Rename the `catalogue` block to `factors`, add an empty `datasets` block after it, and run `node docs/factors/embed-catalogue.mjs`.
- [ ] `load()` reads both blocks. A YAML error names its file and line. The page then lists the problems from `validateDatasets` and `validateCatalogue` together.
- [ ] The tooltip:
  - A measured indicator shows its research status. A factor with sub-factors shows its progress, as "N of M measured indicators researched".
  - A measured indicator with a unit adds "Measured in …", the curve in words, its evidence type, and a list of its datasets, each with its tier and licence, plus "not in public builds" where that applies.
- [ ] The styles: a list inside the tooltip, and `.flag` in ink at weight 600. Nothing else changes.
- [ ] Run the unit tests and `node docs/factors/embed-catalogue.mjs --check`. Commit Tasks 5 to 7: `feat(explorer): show the research behind measured indicators`.

## Task 8: Browser check

- [ ] Extend `$SP/check-explorer.cjs`:
  - The page loads with no problems listed and no console errors.
  - Open Environment, then Air quality. Hovering over NO₂ shows `µg/m³`, `falling to 0 at 40`, `estimate`, both dataset names, and "not in public builds" twice.
  - Hovering over Air quality shows "2 of 2 measured indicators researched".
  - At phone width, the tooltip stays inside the window.
- [ ] Run it: `node "$SP/check-explorer.cjs" "$SP/browser-check" "E:/GitHub/Livability-Atlas" "$SP/shots"`. Expected: `Browser check passed.`
- [ ] Take screenshots of the NO₂ tooltip in the light and dark themes, and look at them. Fix what is wrong, and commit any fixes: `fix(explorer): fixes from the browser check`.

## Task 9: Living documents, Artifact and pull request

- [ ] Update the living documents listed in the spec. Run the documentation check on every changed Markdown file. Commit: `docs: document the catalogue format`.
- [ ] Write the Artifact copy and publish it again, with `explorer-core.js` beside it.
- [ ] Push `feat/catalogue-format` and open a pull request. It merges on the owner's word.

## Verification, end to end

- `node --test "docs/factors/*.test.mjs"` passes every test.
- `node docs/factors/embed-catalogue.mjs --check` reports both blocks up to date.
- The Task 6 check prints `OK: no problems`.
- The browser check passes, and the screenshots show the new tooltip lines with no clipping, in both themes.
- Every relative link resolves, and markdownlint passes on the changed Markdown files.

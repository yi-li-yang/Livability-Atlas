---
description: Research one factor of the factor catalogue, from its measured indicators to an open pull request
argument-hint: <factor id, such as environment>
---

# Research a factor

Research the factor `$ARGUMENTS` in the factor catalogue, as step 0.2 of the roadmap does for each MVP factor. This recipe was done by hand for air quality and for Transport. Their specs show the expected result: `docs/specs/2026-10-24-catalogue-format.md` and `docs/specs/2026-10-24-transport-research.md`.

## 1. Read first

- "Now" and "Next" in `docs/progress.md`, and the terms in `docs/glossary.md`.
- The field reference in `catalogue/README.md`, and the scoring curves in `docs/methodology/scoring.md`.
- The factor's subtree in `catalogue/factors.yaml`, the datasets already in `catalogue/datasets.yaml`, and the factor's rows in `docs/factors/research-notes.md`.
- The decisions that apply, above all D07 (dataset licences), D08 (sensitive data), D16 (dataset tiers) and D18 (preference types).

## 2. Scope

- Research the measured indicators that the first region needs at the within-city scale. Leave the others as ideas, and say why in the spec.
- A sub-factor may become a factor with sub-factors, when what it holds is measured in different units or within different distances.

## 3. Each measured indicator

- `unit`, `preference_type`, `evidence_type` (with the glossary's meanings), `comparable_across_regions`, `method`, and `datasets` best first: city tier, then country, then global.
- A `curve` only when a standard or published evidence sets its thresholds. Otherwise `curve_reason` says what the curve waits for, such as a spike's data.
- Every number in a `curve_reason` names its source.

## 4. Each dataset

- Check the licence at the source: the publisher's own page, API record or terms. A secondary source, such as a mirror or a news report, is not enough.
- Record an SPDX id, a `LicenseRef-` id for a licence that SPDX does not list, or `unknown`. Add `licence_checked` with the date, `public_build` under D07, `attribution`, and `tells`.
- If the licence cannot be confirmed, or is not on D07's list, set `public_build: false` and say why in `licence_note`.
- A licence that should join D07's list is a decision for the owner: record it in the spec, and stop at the open pull request.

## 5. Check

In Git Bash, from the repo root, with `SP` the scratchpad:

```bash
for f in factors datasets; do PYTHONUTF8=1 python -I -c "import json, sys, yaml; json.dump(yaml.safe_load(open(sys.argv[1], encoding='utf-8')), sys.stdout, default=str)" "catalogue/$f.yaml" > "$SP/$f.json"; done
node -e "
const core = require('./docs/factors/explorer-core.js');
const read = (f) => JSON.parse(require('fs').readFileSync(process.argv[1] + '/' + f + '.json', 'utf8'));
const factors = read('factors'), datasets = read('datasets');
const problems = [...core.validateDatasets(datasets), ...core.validateCatalogue(factors, datasets)];
console.log(problems.length ? problems.join('\n') : 'OK: no problems');
" "$SP"
node docs/factors/embed-catalogue.mjs
node --test "docs/factors/*.test.mjs"
```

Then run the browser check from the scratchpad, if it exists, and look at a tooltip of the new research.

## 6. Record

- Write `docs/specs/<date>-<factor>-research.md`, following the Transport research: scope, changes to the factor tree, the measured indicators, where each curve comes from, the datasets and their licences, decisions to review, and findings for the spikes. The plan is this recipe, so a separate plan file is not needed.
- Update the living documents: `docs/factors/research-notes.md` (delete or shrink what moved into the catalogue), `docs/glossary.md` (new terms the app shows), `docs/progress.md`, `docs/codemap.md`, and `docs/decisions.md` if a decision changes.
- Check every relative link, and lint the changed Markdown.

## 7. Publish

- Branch `data/<factor>-research`, with Conventional Commits.
- Publish the factor explorer's Artifact again: `node docs/factors/artifact-page.mjs <output.html>`, with `explorer-core.js` beside it.
- Push, and open a pull request that lists the decisions to review. It merges on the owner's word.

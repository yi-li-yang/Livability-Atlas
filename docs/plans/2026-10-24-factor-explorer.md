# Factor explorer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use superpowers:executing-plans to carry out this plan task by task, inline in this session, because the tasks are small and run in order. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the factor explorer described in `docs/specs/2026-10-24-factor-explorer.md`. It is one page that draws the seed factor tree as a treemap and a sunburst side by side, with live weight sliders and drill-down. It is published as a private Artifact so that the owner can choose the layout (D17).

**Architecture:** `catalogue/factors.yaml` is the single source. A standalone HTML page embeds a copy of it, parses it with js-yaml and draws it with D3, both loaded from cdnjs. The page's logic lives in `explorer-core.js`, a classic script that the page loads and Node's built-in test runner tests. Two small Node scripts copy the catalogue into the page and write the copy that is published as an Artifact.

**Tech stack:** HTML, CSS and plain JavaScript; D3 7.9.0 and js-yaml 4.1.0 from cdnjs, with integrity hashes; Node 24 (`node:test`, no packages); `playwright-core` 1.64.1 in a scratch folder only, driving the installed Edge for the browser check.

---

## Context

Step 0.2 of Phase 0 builds the factor catalogue, and D17 must decide how the app draws the factor tree. The owner approved the factor explorer spec, which is committed on the local branch `feat/factor-explorer` as `5da6b60`, and asked for this implementation plan. This plan replaces the approved Phase 0 plan in this plan file. That plan's decisions are already in the repo's documents, and Task 1 saves its remaining research tables into the repo.

Planning found four refinements to the spec, which Task 1 writes in:

1. **The test command.** Node 24 treats `node --test docs/factors/` as a single file, not a folder. The command becomes `node --test "docs/factors/*.test.mjs"`. Node expands the quoted glob itself, in PowerShell and Git Bash alike.
2. **Colour.** The chart guidance allows at most eight categorical colours, and never cycles them. Eighteen top-level factors cannot each get a colour that every reader can tell apart, so colour shows structure instead:
   - A factor drawn with its sub-factors is a deeper blue: blue 500 in the light theme, blue 350 in the dark.
   - A factor drawn without them is a lighter blue: blue 250 in the light theme, blue 600 in the dark.
   - The palette validator passes both pairs, and every label inside a shape clears 4.5:1 contrast.
   - Labels name each factor, and hovering highlights a factor and its family in both drawings.
3. **The Artifact copy.** The Artifact host wraps the page in its own `<!doctype>`, `<html>`, `<head>` and `<body>`. The repo file still needs its own wrapper, so that it opens in standards mode with a double-click. `docs/factors/artifact-page.mjs` writes the copy without it.
4. **Weight reasons.** The spec's field table makes `weight_reason` required for any weight other than the placeholder 3, but its list of tests left the check out. The checks now enforce it.

Also verified while planning:

- Both cdnjs URLs answer, and their integrity hashes match when recomputed locally.
- `playwright-core` 1.64.1 is current, and Edge and Chrome are installed.
- With `* text=auto`, the working tree has CRLF line endings, so every script normalises line endings.

The type is Barlow, a typeface drawn from road signs. Its semi-condensed cut sets the labels that must fit small tiles.

## Files

| File | Task | Purpose |
| --- | --- | --- |
| `docs/plans/2026-10-24-factor-explorer.md` | 1 | This plan, kept in the repo |
| `docs/factors/research-notes.md` | 1 | Research tables from the Phase 0 plan, for the rest of step 0.2 |
| `docs/specs/2026-10-24-factor-explorer.md` | 1 | Modified with the four refinements |
| `docs/factors/explorer-core.js` | 2, 3 | Catalogue checks, the scale filter, shares of total weight, paths |
| `docs/factors/explorer-core.test.mjs` | 2, 3 | Its tests |
| `catalogue/factors.yaml`, `catalogue/README.md` | 4 | The seed factor tree |
| `docs/factors/embed-catalogue.mjs`, `docs/factors/embed-catalogue.test.mjs` | 5, 6 | Copying the catalogue into the page, and the drift check |
| `docs/factors/explorer.html` | 6 | The page |
| `docs/factors/artifact-page.mjs`, `docs/factors/artifact-page.test.mjs` | 6 | The Artifact copy |
| `docs/factors/README.md`, and the living documents | 8 | How to use the explorer: codemap, tech stack, glossary, `CLAUDE.md`, docs index, roadmap and progress |

## Tasks

1. Keep the plan, save the research notes and refine the spec.
2. Catalogue checks (test first).
3. Scales and shares of total weight (test first).
4. The seed factor tree.
5. Copying the catalogue into the page (test first).
6. The page, its drift test and the Artifact copy (the scripts test first).
7. The browser check in Edge, fixes and screenshots.
8. The living documents.
9. Publish the Artifact, push the branch and open a pull request.

## Verification, end to end

- `node --test "docs/factors/*.test.mjs"` passes all 14 tests.
- `node docs/factors/embed-catalogue.mjs --check` reports that the embedded copy is up to date.
- The browser check passes in Edge with no console errors (Task 7).
- The light, dark and phone screenshots show no clipped labels, overlaps or sideways scrolling (Task 7).
- Every relative link resolves, and markdownlint passes on every changed Markdown file.
- The Artifact opens from its link and behaves as it did in the browser check.

## Shared setup

Every command runs from the repo root, `E:/GitHub/Livability-Atlas`, in Git Bash. `SP` is this session's scratchpad. It already holds `check_links.py` and the markdownlint install (`mdtools/`) from earlier work. In a new session, recreate both first.

```bash
SP="<this session's scratchpad folder>"
cd "E:/GitHub/Livability-Atlas" && git switch feat/factor-explorer
```

The documentation check, used in Tasks 1 and 8:

```bash
PYTHONUTF8=1 python -I "$SP/check_links.py" . && "$SP/mdtools/node_modules/.bin/markdownlint-cli2" --config "$SP/lint.markdownlint-cli2.jsonc" <changed .md files>
```

Expected output: `OK: all relative links and anchors resolve` and `Summary: 0 issues in 0 files`.

---

## Task 1: Keep the plan, save the research notes and refine the spec

**Files:**

- Create: `docs/plans/2026-10-24-factor-explorer.md`, a copy of this plan file
- Create: `docs/factors/research-notes.md`
- Modify: `docs/specs/2026-10-24-factor-explorer.md`

- [ ] **Step 1: Copy this plan into the repo**

```bash
mkdir -p docs/plans docs/factors && cp "<the plan-mode plan file>" docs/plans/2026-10-24-factor-explorer.md
```

- [ ] **Step 2: Write `docs/factors/research-notes.md`**

````markdown
# Research notes

Starting points for the rest of step 0.2, carried over from the approved Phase 0 plan. Each section moves to its home when its task is done, into `catalogue/datasets.yaml`, `docs/factors/rankings.md` or `docs/methodology/hard-to-measure.md`. Delete a section once it has moved.

## What some datasets can tell us

For the bottom-up pass.

| Dataset | What can be dug out of it |
| --- | --- |
| Census 2021 (ONS) | Age profile, household types, renters versus owners, car-free households, how people commute, ethnicity, religion, country of birth, main language, qualifications, self-reported health, students |
| HM Land Registry Price Paid | Median price, price per m² (with EPC floor areas), 5-year price trend, sales volume, new-build share, flats versus houses |
| Police.uk | Crime by category, trend, monthly pattern, share of cases resolved |
| OpenStreetMap and Overture | Amenities by type, cuisine variety, places of worship by faith, pubs and nightlife, cycle lanes, parks, street trees |
| EPC register | Home size, energy rating, building age, heating type, likely damp or cold homes |
| TfL data | Stations, lines, PTAL, fare zones, step-free access, night services |

## Likely datasets for the MVP candidates

| Top-level factor | Sub-factors | Likely datasets |
| --- | --- | --- |
| Housing and cost | Buying cost (price per m²); renting cost; council tax (Band D, by borough) | HM Land Registry Price Paid with EPC floor areas; ONS private rents (by borough, the finest open rent data); the GLA London rents map if it is current; MHCLG for council tax |
| Transport | Getting around in general: PTAL, station proximity, line choice, fare zone. Travel time to the default places and to a user's places | TfL, London Datastore, NaPTAN; GTFS timetables or the TfL API |
| Safety | Crime rate by category | Police.uk bulk data |
| Environment | NO₂ and PM2.5; road, rail and aircraft noise; green space within a 10-minute walk | London Atmospheric Emissions Inventory or DEFRA background maps; DEFRA strategic noise maps; OS Open Greenspace and OpenStreetMap |
| Daily amenities | Everyday amenities and restaurants within a 10-minute walk; cuisine variety; food hygiene | Overture Places, Foursquare Open Source Places or OpenStreetMap; NHS GP list; Food Standards Agency |
| Community and people | Community composition; places of worship by faith | Census 2021 through ONS and Nomis; OpenStreetMap |
| Natural hazards | Flood risk | Environment Agency |
| Digital connectivity | Full-fibre availability, 5G coverage | Ofcom Connected Nations, whose resolution is still to be checked |
| Education | Nearby schools by phase and inspection outcome | DfE GIAS and Ofsted. Ofsted dropped single-word grades in 2024, so "rating" needs a new definition |

Most of these datasets are expected to be under the Open Government Licence. There are three exceptions:

- OpenStreetMap is under ODbL.
- Overture Places is under CDLA-Permissive-2.0.
- TfL data must carry the line "Powered by TfL Open Data".

Non-commercial datasets, such as Ookla's speed tests, never go into public builds (D07).

## Transport: getting around in general

| Sub-factor | Measured indicator | London dataset | MVP |
| --- | --- | --- | --- |
| Station proximity | Walking minutes to the nearest station, for each mode | TfL StopPoint data or NaPTAN, with a walking network | yes |
| Line choice | Distinct rail and Tube lines within a 10-minute walk; bus routes within a 5-minute walk | TfL Line and StopPoint data, BODS | yes |
| Service level | PTAL | London Datastore | yes |
| Travel cost | Fare zone of the nearest station | TfL | yes |
| Night and step-free travel | Night services within a walk; the nearest step-free station | TfL | later |
| Cycling | Protected lanes, cycle-hire docks, slope | TfL Cycle Infrastructure Database, OpenStreetMap, elevation data | later |

## Credibility of published rankings

Each published ranking gets a credibility rating of high, medium or low. The rating weighs six questions:

- Is the method published?
- How much data is behind it?
- Is the publisher independent? An estate agent, for example, is not.
- Is it recent?
- Does it cover our places?
- Does its licence let us store it?

Many rankings are proprietary. For those, store only the rank and a citation, and keep them out of public builds unless the licence allows more (D07).

## Culture: the evidence ladder

| Kind of evidence | Culture example | Evidence type |
| --- | --- | --- |
| Direct counts | Cultural venues within a 15-minute walk: theatres, music venues, galleries, cinemas, libraries (GLA Cultural Infrastructure Map) | direct |
| Access | Cultural venues within 30 minutes by public transport | direct |
| Variety | The number of distinct cuisines nearby | indirect |
| Character | Listed buildings and conservation areas (Historic England) | indirect |
| Activity | Event listings; geotagged Wikipedia articles and their page views | indirect |
| Perception, by ML | Street-level photos rated for liveliness and beauty; area descriptions tagged by an LLM | perception |
| Published rankings | Time Out neighbourhood lists, Sunday Times Best Places to Live | ranking |
| A user's own ratings | A personal notes layer, stored in the browser | the user's own |

The same ladder applies to other factors that are hard to measure, such as community life or feeling safe. Spike S7 tests it.

## Food and drink: quality signals

| Kind of evidence | Example | Dataset and licence | Evidence type |
| --- | --- | --- | --- |
| Choice | Restaurants and cafés within a 10-minute walk | OpenStreetMap, Overture, Foursquare Open Source Places | direct |
| Variety | The number of distinct cuisines nearby | OpenStreetMap cuisine tags | indirect |
| Your cuisines | Restaurants serving the cuisines a user picks | OpenStreetMap cuisine tags | direct |
| Hygiene | Food hygiene ratings of nearby restaurants | UK Food Standards Agency (open; country tier) | direct for hygiene, indirect for quality |
| Guide recognition | Michelin stars and Bib Gourmand, the Good Food Guide, The World's 50 Best | Wikidata (CC0) records the Michelin stars of many restaurants, though not all. The guides themselves are proprietary, so keep only counts and a citation | ranking |
| Independents | The share of restaurants that are not chains | OpenStreetMap and Overture brand tags | indirect |
| Ratings and reviews | Average rating and review count | Google, Yelp, Tripadvisor, OpenRice (Hong Kong), Tabelog (Japan), Dianping (China). Their terms forbid storing the data or require a partnership | perception |

Build from the open rows first. Treat each country's ratings platform as a country-tier dataset that needs a licence. Until it has one, ratings stay out of public builds (D07, D19). Spike S8 tests the open signals.

## Brand presence: shopping centres and brand groups

| Signal | Measured indicator | Example |
| --- | --- | --- |
| Shopping centres | The size of the shopping centres within reach | Westfield London, Westfield Stratford City |
| Brand variety | Distinct national and international chains within a 15-minute walk | |
| Brand groups | Brands grouped by what their choice of sites signals: premium, high footfall, large catchment, value | Premium: Gail's, Waitrose. High footfall: Pret, Starbucks. Large catchment: Costco, IKEA. Value: Aldi, Lidl |

Brand groups are listed per country. Each brand's group is checked against data before use, for example whether its presence tracks house prices, and brands that show no pattern are dropped. Brand presence partly mirrors house prices, so it gets a low default weight. Spike S8 checks how complete brand tags are for London.

## Your industry, across cities

An industry's strength in a city combines four signals:

- industry specialisation: the industry's share of local jobs, compared with its share worldwide
- its firms and headquarters, from Wikidata
- its flagship institutions and events
- credible rankings of the industry

## Catalogue fields still to come

From the Phase 0 plan, for the top-down and bottom-up passes:

- **A measured indicator** gets its dataset options by tier, unit, preference type, default direction or range, scoring curve and evidence type, and whether it is comparable across regions.
- **A dataset** gets:
  - its id, name, publisher and URL
  - its tier, area, resolution and date
  - its licence and attribution text
  - its update cadence, access method and cost
  - what it can tell us
  - for a published ranking, its credibility rating
````

- [ ] **Step 3: Apply the refinements to the spec.** Make each replacement in `docs/specs/2026-10-24-factor-explorer.md` with the Edit tool.

1. Replace `It opens with a double-click, needing only an internet connection for its two libraries, and it publishes as an Artifact unchanged.` with `It opens with a double-click, needing only an internet connection for its two libraries. Without its document wrapper, the same page publishes as an Artifact.`
2. Replace the row `` | `docs/factors/explorer-core.test.mjs` | The tests, run with `node --test docs/factors/` | `` with `` | `docs/factors/*.test.mjs` | The tests, run with `node --test "docs/factors/*.test.mjs"` | ``.
3. After the row that begins `` | `docs/factors/embed-catalogue.mjs` ``, add two rows:
   - `` | `docs/factors/artifact-page.mjs` | Writes the copy of the page that is published as an Artifact, without the document wrapper that the Artifact host adds itself | ``
   - `` | `docs/factors/research-notes.md` | Research tables from the Phase 0 plan, kept for the rest of step 0.2 | ``
4. Replace the whole **Colour and labels** paragraph with: `**Colour and labels.** Colour shows structure, not identity. A factor drawn with its sub-factors is a deeper blue, and a factor drawn without them is a lighter blue. Eighteen top-level factors are too many to tell apart by colour, for any reader, so labels and tooltips name every factor. Hovering over a factor highlights it and its family in both drawings. Both blues keep labels above 4.5:1 contrast, in light and dark themes.`
5. Replace `` 3. Run `node --test docs/factors/`. `` with `` 3. Run `node --test "docs/factors/*.test.mjs"`. ``.
6. Replace `` The unit tests cover `explorer-core.js` and the embedded copy: `` with `` The unit tests cover `explorer-core.js`, the embedded copy and the Artifact copy: ``.
7. Replace `- The checks reject a duplicate id, a weight outside 0–5, a missing name, an unknown scale or status, and a sub-factor scale that its parent lacks.` with `- The checks reject a duplicate id, an id that is not kebab-case, a weight outside 0–5, a weight other than 3 without a reason, a missing name, an unknown scale or status, and a sub-factor scale that its parent lacks.`
8. After `` - The embedded copy matches `catalogue/factors.yaml`. ``, add `- The Artifact copy drops exactly the document wrapper, and nothing else.`
9. In **Publishing**, after its first sentence, add: `` `artifact-page.mjs` first writes the page without its document wrapper, because the Artifact host adds its own. ``

- [ ] **Step 4: Check and commit**

Run the documentation check on `docs/plans/2026-10-24-factor-explorer.md docs/factors/research-notes.md docs/specs/2026-10-24-factor-explorer.md`. Then:

```bash
git add docs/plans docs/factors/research-notes.md docs/specs/2026-10-24-factor-explorer.md
git commit -F - <<'EOF'
docs: add the factor explorer plan and the Phase 0 research notes

The implementation plan for the factor explorer, and the research tables
from the Phase 0 plan that were not yet in the repo. The spec gains four
refinements found while planning: the test command, colour by structure,
the Artifact copy, and the check for weight reasons.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```

---

## Task 2: Catalogue checks

**Files:**

- Create: `docs/factors/explorer-core.test.mjs`
- Create: `docs/factors/explorer-core.js`

- [ ] **Step 1: Write the failing tests**

```js
// Tests for explorer-core.js. Run: node --test "docs/factors/*.test.mjs"
import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const core = require("./explorer-core.js");

// The worked example in docs/methodology/scoring.md, section 8.
function example() {
  return {
    factors: [
      { id: "housing", name: "Housing and cost", default_weight: 4, weight_reason: "Example.", scales: ["within-city"] },
      { id: "transport", name: "Transport", default_weight: 4, weight_reason: "Example.", scales: ["within-city"] },
      {
        id: "environment",
        name: "Environment",
        default_weight: 2,
        weight_reason: "Example.",
        scales: ["within-city"],
        children: [
          {
            id: "air-quality",
            name: "Air quality",
            default_weight: 3,
            children: [
              { id: "no2", name: "NO₂", default_weight: 2, weight_reason: "Example." },
              { id: "pm25", name: "PM2.5", default_weight: 2, weight_reason: "Example." },
            ],
          },
          { id: "noise", name: "Noise", default_weight: 3 },
          { id: "green-space", name: "Green space", default_weight: 0, weight_reason: "Example." },
        ],
      },
    ],
  };
}

test("the worked example passes every check", () => {
  assert.deepEqual(core.validateCatalogue(example()), []);
});

test("an empty catalogue is rejected", () => {
  assert.deepEqual(core.validateCatalogue({}), ["The catalogue needs a non-empty list under factors."]);
});

test("each check names its problem and the factor it concerns", () => {
  const cases = [
    [(c) => { c.factors[1].id = "housing"; }, /^housing: this id is used more than once/],
    [(c) => { c.factors[0].id = "Housing_Cost"; }, /id must be kebab-case/],
    [(c) => { delete c.factors[0].name; }, /^housing: name is missing/],
    [(c) => { c.factors[0].default_weight = 7; }, /^housing: default_weight must be a whole number from 0 to 5/],
    [(c) => { c.factors[0].default_weight = 2.5; }, /default_weight must be a whole number/],
    [(c) => { delete c.factors[0].weight_reason; }, /^housing: a default_weight other than 3 needs a weight_reason/],
    [(c) => { c.factors[0].scales = ["regional"]; }, /^housing: scales must list/],
    [(c) => { delete c.factors[0].scales; }, /^housing: a top-level factor must list its scales/],
    [(c) => { c.factors[2].children[1].scales = ["across-cities"]; }, /^noise: it lists a scale that its parent does not have/],
    [(c) => { c.factors[2].children[1].status = "done"; }, /^noise: status must be one of idea, researched, spiked, built/],
    [(c) => { c.factors[2].children[1].children = []; }, /^noise: children must be a non-empty list/],
  ];
  for (const [change, expected] of cases) {
    const catalogue = example();
    change(catalogue);
    const problems = core.validateCatalogue(catalogue);
    assert.ok(problems.some((p) => expected.test(p)), `expected ${expected}, got ${JSON.stringify(problems)}`);
  }
});
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `node --test "docs/factors/*.test.mjs"`
Expected: FAIL, with `Cannot find module './explorer-core.js'`.

- [ ] **Step 3: Write `docs/factors/explorer-core.js` with the checks**

```js
// Factor explorer logic, without any drawing: it checks the factor catalogue.
// explorer.html loads it as a classic script, and the tests load it with require().
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.ExplorerCore = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const SCALES = ["within-city", "across-cities"];
  const STATUSES = ["idea", "researched", "spiked", "built"];
  // Until default weights are set from evidence (D14), 3 is the placeholder,
  // and any other default weight must give its reason.
  const PLACEHOLDER_WEIGHT = 3;
  const ID_PATTERN = /^[a-z0-9]+(-[a-z0-9]+)*$/;

  // Returns a list of problems, each naming the factor it concerns.
  // An empty list means that the catalogue can be drawn.
  function validateCatalogue(catalogue) {
    if (!catalogue || !Array.isArray(catalogue.factors) || catalogue.factors.length === 0) {
      return ["The catalogue needs a non-empty list under factors."];
    }
    const problems = [];
    const seen = new Set();

    function check(node, parentScales, where) {
      if (node === null || typeof node !== "object" || Array.isArray(node)) {
        problems.push(`${where}: each factor must be a mapping of fields.`);
        return;
      }
      const label = typeof node.id === "string" ? node.id : where;
      if (typeof node.id !== "string" || !ID_PATTERN.test(node.id)) {
        problems.push(`${label}: id must be kebab-case, such as air-quality.`);
      } else if (seen.has(node.id)) {
        problems.push(`${label}: this id is used more than once.`);
      } else {
        seen.add(node.id);
      }
      if (typeof node.name !== "string" || node.name.trim() === "") {
        problems.push(`${label}: name is missing.`);
      }
      const weight = node.default_weight;
      if (!Number.isInteger(weight) || weight < 0 || weight > 5) {
        problems.push(`${label}: default_weight must be a whole number from 0 to 5.`);
      } else if (weight !== PLACEHOLDER_WEIGHT && !(typeof node.weight_reason === "string" && node.weight_reason.trim())) {
        problems.push(`${label}: a default_weight other than ${PLACEHOLDER_WEIGHT} needs a weight_reason.`);
      }
      if (node.status !== undefined && !STATUSES.includes(node.status)) {
        problems.push(`${label}: status must be one of ${STATUSES.join(", ")}.`);
      }
      let scales = parentScales || SCALES;
      if (node.scales === undefined) {
        if (parentScales === null) problems.push(`${label}: a top-level factor must list its scales.`);
      } else if (!Array.isArray(node.scales) || node.scales.length === 0 || node.scales.some((s) => !SCALES.includes(s))) {
        problems.push(`${label}: scales must list ${SCALES.join(", ")}, or both.`);
      } else if (parentScales !== null && node.scales.some((s) => !parentScales.includes(s))) {
        problems.push(`${label}: it lists a scale that its parent does not have.`);
      } else {
        scales = node.scales;
      }
      if (node.children !== undefined) {
        if (!Array.isArray(node.children) || node.children.length === 0) {
          problems.push(`${label}: children must be a non-empty list.`);
        } else {
          node.children.forEach((child, i) => check(child, scales, `${label}, child ${i + 1}`));
        }
      }
    }

    catalogue.factors.forEach((factor, i) => check(factor, null, `factor ${i + 1}`));
    return problems;
  }

  return { SCALES, STATUSES, PLACEHOLDER_WEIGHT, validateCatalogue };
});
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `node --test "docs/factors/*.test.mjs"`
Expected: `ℹ tests 3`, `ℹ pass 3`, `ℹ fail 0`.

- [ ] **Step 5: Commit**

```bash
git add docs/factors/explorer-core.js docs/factors/explorer-core.test.mjs
git commit -F - <<'EOF'
feat(explorer): check the factor catalogue

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```

---

## Task 3: Scales and shares of total weight

**Files:**

- Modify: `docs/factors/explorer-core.test.mjs` (append)
- Modify: `docs/factors/explorer-core.js` (replace with the full version below)

- [ ] **Step 1: Append the failing tests to `docs/factors/explorer-core.test.mjs`**

```js
function treeOf(catalogue, weights = {}, scale = "within-city") {
  return core.buildTree(core.normaliseCatalogue(catalogue), scale, weights);
}
function close(actual, expected) {
  assert.ok(Math.abs(actual - expected) < 1e-9, `${actual} is not ${expected}`);
}
const ids = (views) => views.map((v) => v.id);

test("shares of total weight match the worked example in scoring.md", () => {
  const { byId } = treeOf(example());
  close(byId.get("housing").share, 0.4);
  close(byId.get("transport").share, 0.4);
  close(byId.get("environment").share, 0.2);
  close(byId.get("air-quality").share, 0.1);
  close(byId.get("noise").share, 0.1);
  close(byId.get("no2").share, 0.05);
  close(byId.get("pm25").share, 0.05);
});

test("a factor that starts at weight 0 is listed as not counted", () => {
  const { byId } = treeOf(example());
  assert.deepEqual(ids(byId.get("environment").notCounted), ["green-space"]);
  assert.equal(byId.get("green-space").share, 0);
});

test("setting a weight to 0 removes the factor, and its siblings share its part", () => {
  const { byId } = treeOf(example(), { transport: 0 });
  assert.deepEqual(ids(byId.get("root").notCounted), ["transport"]);
  close(byId.get("housing").share, 4 / 6);
  close(byId.get("environment").share, 2 / 6);
  assert.equal(byId.get("transport").share, 0);
});

test("a factor whose sub-factors all have weight 0 counts as weight 0", () => {
  const { byId } = treeOf(example(), { no2: 0, pm25: 0 });
  assert.equal(byId.get("air-quality").countsAsZero, true);
  assert.equal(byId.get("air-quality").share, 0);
  assert.deepEqual(ids(byId.get("environment").notCounted), ["air-quality", "green-space"]);
  close(byId.get("noise").share, 0.2);
});

test("the scale filter keeps the factors for that scale, and sub-factors inherit scales", () => {
  const root = core.normaliseCatalogue({
    factors: [
      { id: "climate", name: "Climate", default_weight: 3, scales: ["across-cities"] },
      {
        id: "environment",
        name: "Environment",
        default_weight: 3,
        scales: ["within-city", "across-cities"],
        children: [
          { id: "noise", name: "Noise", default_weight: 3, scales: ["within-city"] },
          { id: "air-quality", name: "Air quality", default_weight: 3 },
        ],
      },
    ],
  });
  const within = core.buildTree(root, "within-city", {});
  const across = core.buildTree(root, "across-cities", {});
  assert.deepEqual(ids(within.root.counted), ["environment"]);
  assert.deepEqual(ids(across.root.counted), ["climate", "environment"]);
  assert.deepEqual(ids(within.byId.get("environment").counted), ["noise", "air-quality"]);
  assert.deepEqual(ids(across.byId.get("environment").counted), ["air-quality"]);
});

test("pathTo lists the ids from the root down to a factor", () => {
  const root = core.normaliseCatalogue(example());
  assert.deepEqual(core.pathTo(root, "no2"), ["root", "environment", "air-quality", "no2"]);
  assert.deepEqual(core.pathTo(root, "missing"), []);
});
```

- [ ] **Step 2: Run the tests to see the new ones fail**

Run: `node --test "docs/factors/*.test.mjs"`
Expected: 6 tests FAIL, with `core.normaliseCatalogue is not a function`, and 3 pass.

- [ ] **Step 3: Replace `docs/factors/explorer-core.js` with the full version**

```js
// Factor explorer logic, without any drawing. It checks the factor catalogue,
// fills in inherited scales, and computes each factor's share of total weight
// (docs/methodology/scoring.md, section 5). explorer.html loads it as a
// classic script, and the tests load it with require().
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.ExplorerCore = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const ROOT_ID = "root";
  const SCALES = ["within-city", "across-cities"];
  const STATUSES = ["idea", "researched", "spiked", "built"];
  // Until default weights are set from evidence (D14), 3 is the placeholder,
  // and any other default weight must give its reason.
  const PLACEHOLDER_WEIGHT = 3;
  const ID_PATTERN = /^[a-z0-9]+(-[a-z0-9]+)*$/;

  // Returns a list of problems, each naming the factor it concerns.
  // An empty list means that the catalogue can be drawn.
  function validateCatalogue(catalogue) {
    if (!catalogue || !Array.isArray(catalogue.factors) || catalogue.factors.length === 0) {
      return ["The catalogue needs a non-empty list under factors."];
    }
    const problems = [];
    const seen = new Set();

    function check(node, parentScales, where) {
      if (node === null || typeof node !== "object" || Array.isArray(node)) {
        problems.push(`${where}: each factor must be a mapping of fields.`);
        return;
      }
      const label = typeof node.id === "string" ? node.id : where;
      if (typeof node.id !== "string" || !ID_PATTERN.test(node.id)) {
        problems.push(`${label}: id must be kebab-case, such as air-quality.`);
      } else if (seen.has(node.id)) {
        problems.push(`${label}: this id is used more than once.`);
      } else {
        seen.add(node.id);
      }
      if (typeof node.name !== "string" || node.name.trim() === "") {
        problems.push(`${label}: name is missing.`);
      }
      const weight = node.default_weight;
      if (!Number.isInteger(weight) || weight < 0 || weight > 5) {
        problems.push(`${label}: default_weight must be a whole number from 0 to 5.`);
      } else if (weight !== PLACEHOLDER_WEIGHT && !(typeof node.weight_reason === "string" && node.weight_reason.trim())) {
        problems.push(`${label}: a default_weight other than ${PLACEHOLDER_WEIGHT} needs a weight_reason.`);
      }
      if (node.status !== undefined && !STATUSES.includes(node.status)) {
        problems.push(`${label}: status must be one of ${STATUSES.join(", ")}.`);
      }
      let scales = parentScales || SCALES;
      if (node.scales === undefined) {
        if (parentScales === null) problems.push(`${label}: a top-level factor must list its scales.`);
      } else if (!Array.isArray(node.scales) || node.scales.length === 0 || node.scales.some((s) => !SCALES.includes(s))) {
        problems.push(`${label}: scales must list ${SCALES.join(", ")}, or both.`);
      } else if (parentScales !== null && node.scales.some((s) => !parentScales.includes(s))) {
        problems.push(`${label}: it lists a scale that its parent does not have.`);
      } else {
        scales = node.scales;
      }
      if (node.children !== undefined) {
        if (!Array.isArray(node.children) || node.children.length === 0) {
          problems.push(`${label}: children must be a non-empty list.`);
        } else {
          node.children.forEach((child, i) => check(child, scales, `${label}, child ${i + 1}`));
        }
      }
    }

    catalogue.factors.forEach((factor, i) => check(factor, null, `factor ${i + 1}`));
    return problems;
  }

  // Returns the catalogue as a tree with every field filled in: inherited
  // scales, the default status, and a root above the top-level factors.
  function normaliseCatalogue(catalogue) {
    function copy(node, parentScales) {
      const scales = node.scales || parentScales;
      return {
        id: node.id,
        name: node.name,
        description: node.description || "",
        defaultWeight: node.default_weight,
        weightReason: node.weight_reason || "",
        scales,
        status: node.status || "idea",
        children: (node.children || []).map((child) => copy(child, scales)),
      };
    }
    return {
      id: ROOT_ID,
      name: "All factors",
      description: "",
      defaultWeight: 1,
      weightReason: "",
      scales: SCALES.slice(),
      status: "idea",
      children: catalogue.factors.map((factor) => copy(factor, SCALES)),
    };
  }

  // Returns the tree for one scale, with the user's weights applied.
  // `weights` maps a factor's id to the weight the user set; every other
  // factor keeps its default. Each node of the result holds:
  //   weight        the weight in use
  //   countsAsZero  true when the weight is 0, or every sub-factor counts as 0
  //   share         its share of total weight, 0 when it counts as 0
  //   counted, notCounted  its sub-factors at this scale, split by whether they count
  //   parentId      its parent's id, or null for the root
  // byId maps each id to its node.
  function buildTree(root, scale, weights) {
    const byId = new Map();

    function build(node, parentId) {
      const subFactors = node.children
        .filter((child) => child.scales.includes(scale))
        .map((child) => build(child, node.id));
      const weight = node.id === ROOT_ID ? 1 : weights[node.id] !== undefined ? weights[node.id] : node.defaultWeight;
      const counted = subFactors.filter((s) => !s.countsAsZero);
      const view = {
        id: node.id,
        name: node.name,
        description: node.description,
        weightReason: node.weightReason,
        status: node.status,
        scales: node.scales,
        defaultWeight: node.defaultWeight,
        weight,
        countsAsZero: weight === 0 || (subFactors.length > 0 && counted.length === 0),
        share: 0,
        counted,
        notCounted: subFactors.filter((s) => s.countsAsZero),
        parentId,
      };
      byId.set(node.id, view);
      return view;
    }

    function assignShares(view, share) {
      view.share = share;
      const total = view.counted.reduce((sum, s) => sum + s.weight, 0);
      view.counted.forEach((s) => assignShares(s, (share * s.weight) / total));
    }

    const top = build(root, null);
    assignShares(top, top.countsAsZero ? 0 : 1);
    return { root: top, byId };
  }

  // Returns the ids from the root down to the factor with this id,
  // or an empty list when no factor has it.
  function pathTo(root, id) {
    if (root.id === id) return [root.id];
    for (const child of root.children) {
      const path = pathTo(child, id);
      if (path.length > 0) return [root.id, ...path];
    }
    return [];
  }

  return { ROOT_ID, SCALES, STATUSES, PLACEHOLDER_WEIGHT, validateCatalogue, normaliseCatalogue, buildTree, pathTo };
});
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `node --test "docs/factors/*.test.mjs"`
Expected: `ℹ tests 9`, `ℹ pass 9`, `ℹ fail 0`.

- [ ] **Step 5: Commit**

```bash
git add docs/factors/explorer-core.js docs/factors/explorer-core.test.mjs
git commit -F - <<'EOF'
feat(explorer): compute shares of total weight by scale

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```

---

## Task 4: The seed factor tree

**Files:**

- Create: `catalogue/factors.yaml`
- Create: `catalogue/README.md`

- [ ] **Step 1: Write `catalogue/factors.yaml`**

```yaml
# The factor tree: every factor a user can weight, from broad to specific.
# Terms are defined in docs/glossary.md.
#
# This is the seed version, written in step 0.2 from the approved Phase 0 plan.
# Measured indicators, datasets and scoring curves arrive with the top-down pass.
#
# Rules until default weights are set from evidence (D14):
# - default_weight is a placeholder: 3 for every factor, 1 for the two
#   supporting factors, and 0 for choice factors and community composition.
#   A default_weight other than 3 needs a weight_reason.
# - A sub-factor inherits its parent's scales, or lists a subset of them.
# - status is idea unless stated.
#
# After editing, refresh the factor explorer and run its tests:
#   node docs/factors/embed-catalogue.mjs
#   node --test "docs/factors/*.test.mjs"

factors:
  - id: housing-and-cost
    name: Housing and cost
    description: What it costs to buy or rent a home, and to live in the area.
    default_weight: 3
    scales: [within-city, across-cities]
    children:
      - {id: buying-cost, name: "Buying cost", default_weight: 3, scales: [within-city], description: "Price per square metre."}
      - {id: renting-cost, name: "Renting cost", default_weight: 3, scales: [within-city], description: "Monthly rent by home size."}
      - {id: council-tax, name: "Council tax", default_weight: 3, scales: [within-city]}
      - {id: home-energy-efficiency, name: "Home energy efficiency", default_weight: 3, scales: [within-city]}
      - {id: rent-and-price-levels, name: "Rent and price levels", default_weight: 3, scales: [across-cities]}
      - {id: purchasing-power, name: "Purchasing power", default_weight: 3, scales: [across-cities]}
      - {id: tax-burden, name: "Tax burden", default_weight: 3, scales: [across-cities]}

  - id: transport
    name: Transport
    description: How easily you get around, and how long it takes to reach the places you go.
    default_weight: 3
    scales: [within-city, across-cities]
    children:
      - id: getting-around
        name: Getting around in general
        description: The same for every user. Stations, lines and services near each hex cell.
        default_weight: 3
        scales: [within-city]
        children:
          - {id: station-proximity, name: "Station proximity", default_weight: 3, description: "Walking minutes to the nearest station, for each mode."}
          - {id: line-choice, name: "Line choice", default_weight: 3, description: "Rail and Tube lines within a 10-minute walk, and bus routes within 5 minutes."}
          - {id: service-level, name: "Service level", default_weight: 3, description: "TfL's PTAL index, which combines walking time and service frequency."}
          - {id: travel-cost, name: "Travel cost", default_weight: 3, description: "Fare zone of the nearest station."}
          - {id: night-and-step-free, name: "Night and step-free travel", default_weight: 3}
          - {id: cycling, name: "Cycling", default_weight: 3, description: "Protected lanes, cycle-hire docks and slope."}
      - {id: travel-time-to-places, name: "Travel time to places", default_weight: 3, scales: [within-city], description: "Door-to-door public-transport time to the default places, or to the user's own places."}
      - {id: airport-connectivity, name: "Airport connectivity", default_weight: 3, scales: [across-cities]}
      - {id: intercity-rail, name: "Intercity rail", default_weight: 3, scales: [across-cities]}

  - id: daily-amenities
    name: Daily amenities
    description: Shops, food and services within an easy walk.
    default_weight: 3
    scales: [within-city, across-cities]
    children:
      - id: everyday-amenities
        name: Everyday amenities
        description: Everyday shops and services within a 10-minute walk.
        default_weight: 3
        scales: [within-city]
        children:
          - {id: groceries, name: "Groceries", default_weight: 3}
          - {id: pharmacies, name: "Pharmacies", default_weight: 3}
          - {id: cafes, name: "Cafés", default_weight: 3}
          - {id: gyms, name: "Gyms", default_weight: 3}
          - {id: libraries, name: "Libraries", default_weight: 3}
      - id: food-and-drink
        name: Food and drink
        description: The choice, variety and quality of places to eat.
        default_weight: 3
        children:
          - {id: restaurant-choice, name: "Restaurant choice", default_weight: 3, scales: [within-city], description: "Restaurants within a 10-minute walk."}
          - {id: cuisine-variety, name: "Cuisine variety", default_weight: 3}
          - {id: your-cuisines, name: "Your cuisines", default_weight: 0, weight_reason: "Choice factor: weight 0 until the user picks cuisines (D18)."}
          - {id: food-hygiene, name: "Food hygiene", default_weight: 3, scales: [within-city]}
          - {id: guide-recognition, name: "Guide recognition", default_weight: 3, description: "Michelin and other guides, through Wikidata."}
          - {id: independents, name: "Independent restaurants", default_weight: 3, scales: [within-city], description: "The share of restaurants that are not chains."}
      - id: brand-presence
        name: Brand presence
        description: Chain brands and shopping centres nearby, as a sign of how large companies rate the area.
        default_weight: 3
        scales: [within-city]
        children:
          - {id: shopping-centres, name: "Shopping centres", default_weight: 3}
          - {id: brand-variety, name: "Brand variety", default_weight: 3}
          - {id: brand-groups, name: "Brand groups", default_weight: 3, description: "Premium, high-footfall, large-catchment and value brands."}
      - {id: shopping, name: "Shopping", default_weight: 3, scales: [across-cities], description: "Shopping centres, and flagship and big-box stores."}
      - {id: destinations, name: "Destinations", default_weight: 0, scales: [within-city], weight_reason: "Choice factor: weight 0 until the user picks destinations (D18). Planned for Phase 2.", description: "Distance to public places or chains the user picks, such as IKEA or the nearest airport."}

  - id: environment
    name: Environment
    description: Air, noise, green space, water and heat where you live.
    default_weight: 3
    scales: [within-city, across-cities]
    children:
      - id: air-quality
        name: Air quality
        default_weight: 3
        children:
          - {id: no2, name: "NO₂, annual mean", default_weight: 3, scales: [within-city]}
          - {id: pm25, name: "PM2.5, annual mean", default_weight: 3, scales: [within-city]}
      - id: noise
        name: Noise
        default_weight: 3
        scales: [within-city]
        children:
          - {id: road-noise, name: "Road traffic noise", default_weight: 3}
          - {id: rail-noise, name: "Rail noise", default_weight: 3}
          - {id: aircraft-noise, name: "Aircraft noise", default_weight: 3}
      - id: green-space
        name: Green space
        default_weight: 3
        children:
          - {id: park-area, name: "Park area within a 10-minute walk", default_weight: 3, scales: [within-city]}
          - {id: tree-canopy, name: "Tree canopy cover", default_weight: 3, scales: [within-city]}
      - {id: water-nearby, name: "Water nearby", default_weight: 3, scales: [within-city], description: "A river, canal or lake."}
      - {id: urban-heat, name: "Urban heat", default_weight: 3, scales: [within-city]}
      - {id: light-pollution, name: "Light pollution", default_weight: 3, scales: [across-cities]}

  - id: climate
    name: Climate
    description: Weather and climate. They differ between cities, but barely within one.
    default_weight: 3
    scales: [across-cities]
    children:
      - {id: temperature, name: "Temperature", default_weight: 3}
      - {id: sunshine, name: "Sunshine duration", default_weight: 3, description: "Hours of sunshine, per year and per month."}
      - {id: daylight, name: "Daylight length", default_weight: 3}
      - {id: humidity, name: "Humidity", default_weight: 3}
      - {id: rain, name: "Rain", default_weight: 3}
      - {id: wind, name: "Wind", default_weight: 3}
      - {id: snow, name: "Snow", default_weight: 3}
      - {id: weather-extremes, name: "Weather extremes", default_weight: 3}
      - {id: future-climate, name: "Future climate", default_weight: 3}

  - id: natural-hazards
    name: Natural hazards
    description: Risks from floods, ground movement and other natural events.
    default_weight: 3
    scales: [within-city, across-cities]
    children:
      - id: flood-risk
        name: Flood risk
        default_weight: 3
        scales: [within-city]
        children:
          - {id: river-and-sea-flooding, name: "Rivers and sea", default_weight: 3}
          - {id: surface-water-flooding, name: "Surface water", default_weight: 3}
      - {id: subsidence, name: "Subsidence", default_weight: 3, scales: [within-city]}
      - {id: earthquakes, name: "Earthquakes", default_weight: 3, scales: [across-cities]}
      - {id: storms, name: "Storms", default_weight: 3, scales: [across-cities]}
      - {id: wildfire, name: "Wildfire", default_weight: 3, scales: [across-cities]}
      - {id: sea-level-rise, name: "Sea-level rise", default_weight: 3, scales: [across-cities]}

  - id: safety
    name: Safety
    description: Crime and road danger.
    default_weight: 3
    scales: [within-city, across-cities]
    children:
      - {id: crime, name: "Crime by category", default_weight: 3, scales: [within-city]}
      - {id: road-collisions, name: "Road collisions", default_weight: 3, scales: [within-city]}
      - {id: homicide-rate, name: "Homicide rate", default_weight: 3, scales: [across-cities]}
      - {id: political-stability, name: "Political stability", default_weight: 3, scales: [across-cities]}

  - id: health-care
    name: Health care
    description: Access to GPs, hospitals and dentists.
    default_weight: 3
    scales: [within-city, across-cities]
    children:
      # GP access sits here, not under Daily amenities. Life expectancy sits under Resident wellbeing.
      - {id: gp-access, name: "GP access and list size", default_weight: 3, scales: [within-city]}
      - {id: ae-travel-time, name: "A&E travel time", default_weight: 3, scales: [within-city]}
      - {id: dentists, name: "Dentists", default_weight: 3, scales: [within-city]}
      - {id: health-care-quality, name: "Health-care quality and cost", default_weight: 3, scales: [across-cities]}

  - id: education
    name: Education
    description: Schools, nurseries and universities.
    default_weight: 3
    scales: [within-city, across-cities]
    children:
      - {id: schools, name: "Schools by phase and inspection outcome", default_weight: 3, scales: [within-city]}
      - {id: nurseries, name: "Nurseries", default_weight: 3, scales: [within-city]}
      - {id: school-league-tables, name: "School league tables", default_weight: 3, scales: [within-city]}
      - {id: school-quality, name: "School quality", default_weight: 3, scales: [across-cities]}
      - {id: international-schools, name: "International schools", default_weight: 3, scales: [across-cities]}
      - {id: universities, name: "Universities", default_weight: 3, scales: [across-cities]}

  - id: community-and-people
    name: Community and people
    description: Who lives nearby, and the community life they share.
    default_weight: 3
    scales: [within-city, across-cities]
    children:
      - id: community-composition
        name: Community composition
        description: Framed as the presence of a group the user picks, and as diversity (D08).
        default_weight: 0
        weight_reason: Starts at 0, so composition counts only if the user asks for it (D08).
        children:
          - {id: your-community, name: "Your community", default_weight: 0, weight_reason: "Choice factor: weight 0 until the user picks a group (D18).", description: "The presence of a group the user picks, by ethnicity, country of birth or language."}
          - {id: diversity, name: "Diversity", default_weight: 3, scales: [within-city]}
      - {id: faith, name: "Faith", default_weight: 0, scales: [within-city], weight_reason: "Choice factor: weight 0 until the user picks a faith (D18).", description: "Places of worship of the user's faith, and residents who share it."}
      - id: community-life
        name: Community life
        default_weight: 3
        scales: [within-city]
        children:
          - {id: community-spaces, name: "Community spaces", default_weight: 3}
          - {id: lgbtq-friendly-venues, name: "LGBTQ+-friendly venues", default_weight: 3}
          - {id: election-turnout, name: "Local election turnout", default_weight: 3}
          - {id: residents-stay, name: "How long residents stay", default_weight: 3}
      - {id: english-proficiency, name: "English proficiency", default_weight: 3, scales: [across-cities]}
      - {id: expat-communities, name: "Expat communities", default_weight: 3, scales: [across-cities]}
      - {id: religious-freedom, name: "Religious freedom", default_weight: 3, scales: [across-cities]}
      - {id: gender-equality, name: "Gender equality", default_weight: 3, scales: [across-cities]}

  - id: culture-and-leisure
    name: Culture and leisure
    description: Culture, nightlife and things to do.
    default_weight: 3
    scales: [within-city, across-cities]
    children:
      - id: culture
        name: Culture
        default_weight: 3
        children:
          - {id: cultural-venues-nearby, name: "Cultural venues within a 15-minute walk", default_weight: 3, scales: [within-city]}
          - {id: cultural-venues-in-reach, name: "Cultural venues within 30 minutes by public transport", default_weight: 3, scales: [within-city]}
          - {id: local-character, name: "Local character", default_weight: 3, scales: [within-city], description: "Listed buildings and conservation areas."}
          - {id: cultural-activity, name: "Cultural activity", default_weight: 3, scales: [within-city], description: "Events, and well-known places on Wikipedia."}
      - {id: nightlife, name: "Nightlife", default_weight: 3, description: "Some users want it nearby and others want quiet, so the user sets the direction."}
      - {id: outdoor-access, name: "Outdoor access", default_weight: 3, scales: [across-cities]}

  - id: animal-friendliness
    name: Animal friendliness
    description: How well the area suits pets and wildlife.
    default_weight: 3
    scales: [within-city, across-cities]
    children:
      - id: pets
        name: Pets
        default_weight: 3
        children:
          - {id: vets, name: "Vets", default_weight: 3, scales: [within-city]}
          - {id: pet-shops, name: "Pet shops", default_weight: 3, scales: [within-city]}
          - {id: dog-friendly-parks, name: "Dog-friendly parks and off-lead areas", default_weight: 3, scales: [within-city]}
          - {id: pet-friendly-venues, name: "Pet-friendly cafés and pubs", default_weight: 3, scales: [within-city]}
          - {id: pet-friendly-rentals, name: "Pet-friendly rentals", default_weight: 3, scales: [within-city], description: "No open data yet."}
          - {id: pet-rental-rules, name: "Pet rules in rental law", default_weight: 3, scales: [across-cities]}
      - id: wildlife
        name: Wildlife
        default_weight: 3
        children:
          - {id: nature-sites, name: "Nature sites", default_weight: 3, scales: [within-city]}
          - {id: biodiversity, name: "Biodiversity", default_weight: 3}
      - {id: animal-protection-laws, name: "Animal-protection laws", default_weight: 3, scales: [across-cities]}

  - id: work-and-economy
    name: Work and economy
    description: Jobs, pay and the local economy.
    default_weight: 3
    scales: [within-city, across-cities]
    children:
      # Jobs within reach sits here, not under Transport.
      - {id: job-density, name: "Job density", default_weight: 3, scales: [within-city]}
      - {id: jobs-within-reach, name: "Jobs within reach", default_weight: 3, scales: [within-city], description: "Jobs reachable within 45 minutes by public transport."}
      - {id: coworking, name: "Coworking", default_weight: 3, scales: [within-city]}
      - {id: your-industry, name: "Your industry", default_weight: 0, weight_reason: "Choice factor: weight 0 until the user picks an industry (D18).", description: "Jobs in a chosen industry within reach, or how strong that industry is in a city."}
      - {id: salaries, name: "Salaries", default_weight: 3, scales: [across-cities]}
      - {id: unemployment, name: "Unemployment", default_weight: 3, scales: [across-cities]}
      - {id: residency-and-visas, name: "Ease of residency and visas", default_weight: 3, scales: [across-cities]}

  - id: digital-connectivity
    name: Digital connectivity
    description: Broadband and mobile coverage.
    default_weight: 3
    scales: [within-city, across-cities]
    children:
      - {id: full-fibre, name: "Full-fibre availability", default_weight: 3, scales: [within-city]}
      - {id: 5g-coverage, name: "5G coverage", default_weight: 3, scales: [within-city]}
      - {id: broadband-speed, name: "Broadband speed", default_weight: 3, scales: [across-cities]}
      - {id: internet-freedom, name: "Internet freedom", default_weight: 3, scales: [across-cities]}

  - id: urban-form-and-change
    name: Urban form and change
    description: Density, building age, and how the area is changing.
    default_weight: 3
    scales: [within-city, across-cities]
    children:
      - {id: density, name: "Density", default_weight: 3, scales: [within-city], description: "Some users want a busy area and others a quiet one, so the user sets the direction."}
      - {id: building-age, name: "Building age", default_weight: 3, scales: [within-city], description: "The user sets an ideal range."}
      - {id: regeneration, name: "Regeneration and planning", default_weight: 3, scales: [within-city]}
      - {id: urban-growth, name: "Urban growth", default_weight: 3, scales: [across-cities]}

  - id: governance-and-rights
    name: Governance and rights
    description: How a country is governed, and the rights people have there.
    default_weight: 3
    scales: [across-cities]
    children:
      - {id: rule-of-law, name: "Rule of law", default_weight: 3}
      - {id: democracy, name: "Democracy", default_weight: 3}
      - {id: press-freedom, name: "Press freedom", default_weight: 3}
      - {id: corruption, name: "Corruption", default_weight: 3}
      - {id: lgbtq-friendliness, name: "LGBTQ+ friendliness", default_weight: 3, description: "Legal rights and public acceptance."}

  - id: published-rankings
    name: Published rankings
    description: Outside lists and indices of places, kept as a supporting factor.
    default_weight: 1
    weight_reason: Supporting factor. It partly repeats the other factors, so it starts low (D14).
    scales: [within-city, across-cities]
    children:
      - {id: sunday-times-best-places, name: "Sunday Times Best Places to Live", default_weight: 3, scales: [within-city]}
      - {id: time-out-neighbourhoods, name: "Time Out neighbourhood lists", default_weight: 3, scales: [within-city]}
      - {id: eiu-liveability, name: "EIU Global Liveability Index", default_weight: 3, scales: [across-cities]}
      - {id: mercer-quality-of-living, name: "Mercer Quality of Living", default_weight: 3, scales: [across-cities]}
      - {id: monocle-quality-of-life, name: "Monocle Quality of Life", default_weight: 3, scales: [across-cities]}
      - {id: oecd-better-life, name: "OECD Better Life Index", default_weight: 3, scales: [across-cities]}

  - id: resident-wellbeing
    name: Resident wellbeing
    description: How residents rate their lives, and how long they live.
    default_weight: 1
    weight_reason: Supporting factor. It partly repeats the other factors, so it starts low (D14).
    scales: [within-city, across-cities]
    children:
      - {id: life-satisfaction, name: "Life satisfaction", default_weight: 3, scales: [within-city]}
      - {id: happiness, name: "Happiness", default_weight: 3, scales: [across-cities]}
      - {id: life-expectancy, name: "Life expectancy", default_weight: 3}
```

- [ ] **Step 2: Check the seed once.** This uses conda's PyYAML for a one-off check that is not committed. In step 0.3, `atlas validate` takes this job over.

```bash
PYTHONUTF8=1 python -I -c "import json, sys, yaml; json.dump(yaml.safe_load(open('catalogue/factors.yaml', encoding='utf-8')), sys.stdout)" | node -e "
const core = require('./docs/factors/explorer-core.js');
let text = '';
process.stdin.on('data', (d) => (text += d)).on('end', () => {
  const catalogue = JSON.parse(text);
  const problems = core.validateCatalogue(catalogue);
  if (problems.length > 0) { console.log(problems.join('\n')); process.exit(1); }
  const root = core.normaliseCatalogue(catalogue);
  for (const scale of core.SCALES) {
    const top = core.buildTree(root, scale, {}).root;
    console.log(scale, top.counted.length + top.notCounted.length);
  }
});"
```

Expected: `within-city 16` and `across-cities 18`.

- [ ] **Step 3: Write `catalogue/README.md`**

````markdown
# Factor catalogue

The machine-readable factor catalogue. The [glossary](../docs/glossary.md) defines its terms.

`factors.yaml` holds the factor tree, with every factor's default weight and the reason for it. Its first version is the seed tree from the Phase 0 plan. The datasets, the regions and the presets arrive in later steps.

## Checks

Until step 0.3, the [factor explorer](../docs/factors/README.md) checks `factors.yaml` whenever it loads, and lists any problem instead of drawing. From step 0.3, `atlas validate` checks the whole catalogue in CI.

After editing `factors.yaml`, refresh the explorer's copy and run its tests:

```sh
node docs/factors/embed-catalogue.mjs
node --test "docs/factors/*.test.mjs"
```
````

- [ ] **Step 4: Commit**

```bash
git add catalogue
git commit -F - <<'EOF'
feat(catalogue): add the seed factor tree

The 18 top-level factors and their sub-factors from the Phase 0 plan,
with placeholder default weights until D14 sets them from evidence.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```

---

## Task 5: Copying the catalogue into the page

**Files:**

- Create: `docs/factors/embed-catalogue.test.mjs`
- Create: `docs/factors/embed-catalogue.mjs`

- [ ] **Step 1: Write the failing tests**

```js
// Tests for embed-catalogue.mjs. Run: node --test "docs/factors/*.test.mjs"
import test from "node:test";
import assert from "node:assert/strict";
import { embed, embeddedCopy } from "./embed-catalogue.mjs";

const page = '<p>Before</p>\r\n<script type="text/yaml" id="catalogue">\r\nold: 1\r\n</script>\r\n<p>After</p>\r\n';

test("embed puts the catalogue between the markers, and embeddedCopy reads it back", () => {
  const out = embed(page, "factors: []\r\n");
  assert.equal(embeddedCopy(out), "factors: []\n");
  assert.ok(out.startsWith("<p>Before</p>\n"));
  assert.ok(out.endsWith("</script>\n<p>After</p>\n"));
});

test("embed refuses text that would end the script block early", () => {
  assert.throws(() => embed(page, "a: </script>"), /must not contain/);
  assert.throws(() => embed(page, "a: <!-- b"), /must not contain/);
});
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `node --test "docs/factors/*.test.mjs"`
Expected: `embed-catalogue.test.mjs` FAILS with `Cannot find module`, and the 9 earlier tests pass.

- [ ] **Step 3: Write `docs/factors/embed-catalogue.mjs`**

```js
// Copies catalogue/factors.yaml into explorer.html, inside the
// <script type="text/yaml" id="catalogue"> block. With --check it changes
// nothing, and exits with status 1 when the copy is out of date.
// Usage: node docs/factors/embed-catalogue.mjs [--check]
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
export const CATALOGUE = path.join(here, "..", "..", "catalogue", "factors.yaml");
export const PAGE = path.join(here, "explorer.html");
const OPEN = '<script type="text/yaml" id="catalogue">';
const CLOSE = "</script>";

const lf = (text) => text.replace(/\r\n/g, "\n");

function blockBounds(html) {
  const start = html.indexOf(OPEN);
  if (start === -1) throw new Error(`explorer.html has no ${OPEN} block.`);
  const end = html.indexOf(CLOSE, start + OPEN.length);
  return { start: start + OPEN.length, end };
}

// Returns the catalogue text embedded in the page, with LF line endings.
export function embeddedCopy(html) {
  const text = lf(html);
  const { start, end } = blockBounds(text);
  return text.slice(start, end).replace(/^\n/, "");
}

// Returns the page with the catalogue embedded, with LF line endings.
export function embed(html, yaml) {
  if (/<\/script|<!--/i.test(yaml)) {
    throw new Error("factors.yaml must not contain '</script' or '<!--', because they would end the script block early.");
  }
  const text = lf(html);
  const { start, end } = blockBounds(text);
  return `${text.slice(0, start)}\n${lf(yaml)}${text.slice(end)}`;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const yaml = readFileSync(CATALOGUE, "utf8");
  const html = readFileSync(PAGE, "utf8");
  if (process.argv.includes("--check")) {
    const current = embeddedCopy(html) === lf(yaml);
    console.log(current
      ? "The embedded catalogue is up to date."
      : "The embedded catalogue is out of date. Run: node docs/factors/embed-catalogue.mjs");
    process.exit(current ? 0 : 1);
  }
  writeFileSync(PAGE, embed(html, yaml));
  console.log("Copied catalogue/factors.yaml into docs/factors/explorer.html.");
}
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `node --test "docs/factors/*.test.mjs"`
Expected: `ℹ tests 11`, `ℹ pass 11`, `ℹ fail 0`.

- [ ] **Step 5: Commit**

```bash
git add docs/factors/embed-catalogue.mjs docs/factors/embed-catalogue.test.mjs
git commit -F - <<'EOF'
feat(explorer): copy the catalogue into the page

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```

---

## Task 6: The page, its drift test and the Artifact copy

**Files:**

- Create: `docs/factors/explorer.html`
- Modify: `docs/factors/embed-catalogue.test.mjs` (append the drift test)
- Create: `docs/factors/artifact-page.test.mjs`
- Create: `docs/factors/artifact-page.mjs`

- [ ] **Step 1: Write `docs/factors/explorer.html`**

The catalogue block starts empty, and Step 2 fills it.

```html
<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Factor explorer</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&family=Barlow+Semi+Condensed:wght@500;600&display=swap">
<style>
/* Layout: a header row, then the weights panel beside two equal square
   drawings; one column below 1100px. Colour shows structure only: a factor
   drawn with its sub-factors is deeper blue, the others lighter blue. */
:root {
  --plane: #f9f9f7;
  --surface: #fcfcfb;
  --ink: #0b0b0b;
  --ink-2: #52514e;
  --hairline: #e1e0d9;
  --accent: #256abf;
  --accent-ink: #ffffff;
  --group: #256abf;
  --group-ink: #ffffff;
  --tile: #86b6ef;
  --tile-ink: #0b0b0b;
  --critical: #d03b3b;
  --shadow: rgba(11, 11, 11, 0.14);
  --font-body: "Barlow", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-label: "Barlow Semi Condensed", "Barlow", system-ui, -apple-system, "Segoe UI", sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --plane: #0d0d0d;
    --surface: #1a1a19;
    --ink: #f0efec;
    --ink-2: #c3c2b7;
    --hairline: #2c2c2a;
    --accent: #5598e7;
    --accent-ink: #0b0b0b;
    --group: #5598e7;
    --group-ink: #0b0b0b;
    --tile: #184f95;
    --tile-ink: #f0efec;
    --shadow: rgba(0, 0, 0, 0.5);
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --plane: #0d0d0d;
  --surface: #1a1a19;
  --ink: #f0efec;
  --ink-2: #c3c2b7;
  --hairline: #2c2c2a;
  --accent: #5598e7;
  --accent-ink: #0b0b0b;
  --group: #5598e7;
  --group-ink: #0b0b0b;
  --tile: #184f95;
  --tile-ink: #f0efec;
  --shadow: rgba(0, 0, 0, 0.5);
  color-scheme: dark;
}
*, *::before, *::after { box-sizing: border-box; }
[hidden] { display: none !important; }
body {
  margin: 0;
  background: var(--plane);
  color: var(--ink);
  font: 400 15px/1.45 var(--font-body);
  padding-block: 20px 32px;
  padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px));
}
h1, h2, h3 { margin: 0; text-wrap: balance; }
h1 { font-size: 1.625rem; font-weight: 600; line-height: 1.2; }
h2 { font-size: 0.75rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink-2); }
h3 { font-size: 0.9375rem; font-weight: 600; }
p { margin: 0; }
button, input { font: inherit; color: inherit; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.page { display: grid; gap: 16px; max-width: 1600px; margin: 0 auto; }
.bar { display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between; gap: 12px 24px; }
.subtitle { margin-top: 4px; max-width: 65ch; color: var(--ink-2); }
.controls { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; }
.scale { display: inline-flex; margin: 0; padding: 2px; border: 1px solid var(--hairline); border-radius: 6px; background: var(--surface); }
.scale legend { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
.scale input { position: absolute; opacity: 0; pointer-events: none; }
.scale label { padding: 5px 12px; border-radius: 4px; cursor: pointer; }
.scale input:checked + label { background: var(--accent); color: var(--accent-ink); }
.scale input:focus-visible + label { outline: 2px solid var(--accent); outline-offset: 2px; }
.quiet { padding: 6px 12px; border: 1px solid var(--hairline); border-radius: 6px; background: var(--surface); cursor: pointer; }
.quiet:hover:not(:disabled) { border-color: var(--ink-2); }
.quiet:disabled { opacity: 0.45; cursor: default; }
.crumbs { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 16px; }
.crumbs ol { display: flex; flex-wrap: wrap; gap: 4px 6px; margin: 0; padding: 0; list-style: none; }
.crumbs li { display: flex; align-items: center; gap: 6px; }
.crumbs li + li::before { content: "›"; color: var(--ink-2); }
.crumbs li button { padding: 0; border: 0; background: none; color: var(--accent); text-decoration: underline; text-underline-offset: 3px; cursor: pointer; }
.crumbs [aria-current="page"] { font-weight: 600; }
.workspace { display: grid; grid-template-columns: minmax(250px, 320px) minmax(0, 1fr) minmax(0, 1fr); align-items: start; gap: 16px; }
@media (max-width: 1100px) { .workspace { grid-template-columns: minmax(0, 1fr); } }
.panel { display: grid; gap: 12px; min-width: 0; padding: 14px; border: 1px solid var(--hairline); border-radius: 8px; background: var(--surface); }
.panel-part { display: grid; gap: 8px; }
.hint, .reason, .figures { color: var(--ink-2); font-size: 0.875rem; }
.sliders, .not-counted, #problem-list { display: grid; gap: 12px; margin: 0; padding: 0; list-style: none; }
.slider-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: baseline; gap: 2px 8px; }
.slider-row label { min-width: 0; overflow-wrap: anywhere; }
.figures { font-variant-numeric: tabular-nums; white-space: nowrap; }
.slider-row input[type="range"] { grid-column: 1 / -1; width: 100%; margin: 0; accent-color: var(--accent); }
.slider-row .quiet { grid-column: 1 / -1; justify-self: start; padding: 3px 10px; font-size: 0.875rem; }
.not-counted li { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 6px 12px; }
.drawing svg { display: block; width: 100%; max-width: 100%; height: auto; aspect-ratio: 1 / 1; }
.drawing text { font-family: var(--font-label); font-size: 12px; font-weight: 500; pointer-events: none; }
.node rect, .arc path { fill: var(--tile); cursor: pointer; transition: opacity 150ms; }
.node.is-group rect, .arc.is-group path { fill: var(--group); }
.node text, .arc text { fill: var(--tile-ink); }
.node.is-group text, .arc.is-group text { fill: var(--group-ink); font-weight: 600; }
.centre circle { fill: var(--surface); }
.centre text { fill: var(--ink); font-size: 13px; font-weight: 600; }
.centre .go-up { fill: var(--accent); font-weight: 500; }
.centre.can-go-up { cursor: pointer; }
.empty { fill: var(--ink-2); font-size: 14px; }
.is-dim { opacity: 0.3; }
.problems { display: grid; gap: 8px; padding: 12px 16px; border-left: 4px solid var(--critical); border-radius: 4px; background: var(--surface); }
.tooltip { position: fixed; z-index: 20; max-width: 300px; padding: 10px 12px; border: 1px solid var(--hairline); border-radius: 6px; background: var(--surface); color: var(--ink); box-shadow: 0 6px 20px var(--shadow); font-size: 0.875rem; pointer-events: none; }
.tooltip p { margin-top: 4px; color: var(--ink-2); }
@media (prefers-reduced-motion: reduce) { .node rect, .arc path { transition: none; } }
</style>
</head>
<body>
<div class="page">
  <header class="bar">
    <div>
      <h1>Factor explorer</h1>
      <p class="subtitle">The factor catalogue's tree, drawn as a treemap and as a sunburst. Each area is a factor's share of total weight. The default weights are placeholders until they are set from evidence (D14).</p>
    </div>
    <div class="controls">
      <fieldset class="scale">
        <legend>Scale</legend>
        <input type="radio" name="scale" id="scale-within-city" value="within-city" checked>
        <label for="scale-within-city">Within a city</label>
        <input type="radio" name="scale" id="scale-across-cities" value="across-cities">
        <label for="scale-across-cities">Across cities</label>
      </fieldset>
      <button type="button" id="reset" class="quiet">Reset weights</button>
    </div>
  </header>
  <section id="problems" class="problems" hidden>
    <h3>The catalogue has problems, so nothing is drawn</h3>
    <ul id="problem-list"></ul>
  </section>
  <nav id="path" class="crumbs" aria-label="Path">
    <ol id="crumbs"></ol>
    <button type="button" id="back" class="quiet">Back</button>
  </nav>
  <main id="workspace" class="workspace">
    <section class="panel" aria-labelledby="weights-title">
      <h2 id="weights-title">Weights</h2>
      <p class="hint">Each row shows the weight (0–5), then the share of total weight.</p>
      <ul id="sliders" class="sliders"></ul>
      <div id="not-counted-block" class="panel-part" hidden>
        <h3>Not counted</h3>
        <ul id="not-counted" class="not-counted"></ul>
      </div>
    </section>
    <section class="panel drawing" aria-labelledby="treemap-title">
      <h2 id="treemap-title">Treemap</h2>
      <svg id="treemap" role="img" aria-labelledby="treemap-title"></svg>
    </section>
    <section class="panel drawing" aria-labelledby="sunburst-title">
      <h2 id="sunburst-title">Sunburst</h2>
      <svg id="sunburst" role="img" aria-labelledby="sunburst-title"></svg>
    </section>
  </main>
</div>
<div id="tooltip" class="tooltip" hidden></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js" integrity="sha512-vc58qvvBdrDR4etbxMdlTt4GBQk1qjvyORR2nrsPsFPyrs+/u5c3+1Ct6upOgdZoIl7eq6k3a1UPDSNAQi/32A==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/js-yaml/4.1.0/js-yaml.min.js" integrity="sha512-CSBhVREyzHAjAFfBlIBakjoRUKp5h7VSweP0InR/pAJyptH7peuhCsqAI/snV+TwZmXZqoUklpXp6R6wMnYf5Q==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
<script src="explorer-core.js"></script>
<script type="text/yaml" id="catalogue">
</script>
<script>
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const MOTION = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 300;
  const HEADER = 20; // px above a group's sub-factors in the treemap, for its name
  const percent = new Intl.NumberFormat("en-GB", { style: "percent", maximumFractionDigits: 1 });

  function el(tag, attributes, ...children) {
    const node = document.createElement(tag);
    for (const [name, value] of Object.entries(attributes)) node.setAttribute(name, value);
    node.append(...children);
    return node;
  }

  function showProblems(problems) {
    $("problem-list").replaceChildren(...problems.map((problem) => el("li", {}, problem)));
    $("problems").hidden = false;
    $("path").hidden = true;
    $("workspace").hidden = true;
  }

  if (!window.d3 || !window.jsyaml || !window.ExplorerCore) {
    showProblems(["D3, js-yaml or explorer-core.js did not load. The page needs an internet connection for D3 and js-yaml, and explorer-core.js beside it."]);
    return;
  }

  const core = window.ExplorerCore;
  const state = { scale: "within-city", openId: core.ROOT_ID, weights: {}, committed: {} };
  let catalogueRoot = null;
  let tree = null;

  // Loading

  function load() {
    let catalogue;
    try {
      catalogue = jsyaml.load($("catalogue").textContent);
    } catch (error) {
      const where = error.mark ? ` at line ${error.mark.line + 1}` : "";
      showProblems([`factors.yaml cannot be read${where}: ${error.reason || error.message}.`]);
      return;
    }
    const problems = core.validateCatalogue(catalogue);
    if (problems.length > 0) {
      showProblems(problems);
      return;
    }
    catalogueRoot = core.normaliseCatalogue(catalogue);
    render();
  }

  // State changes

  function render(focusId) {
    tree = core.buildTree(catalogueRoot, state.scale, state.weights);
    if (!tree.byId.has(state.openId)) {
      // The open factor does not apply at this scale: go up to its nearest parent that does.
      const path = core.pathTo(catalogueRoot, state.openId).reverse();
      state.openId = path.find((id) => tree.byId.has(id)) || core.ROOT_ID;
    }
    const open = tree.byId.get(state.openId);
    renderPath(open);
    renderWeights(open);
    draw(open);
    if (focusId) {
      const target = document.querySelector(`[data-focus="${focusId}"]`);
      if (target) target.focus();
    }
  }

  function openFactor(id) {
    state.openId = id;
    highlight(null);
    hideTooltip();
    render();
  }

  function goUp() {
    const open = tree.byId.get(state.openId);
    if (open.parentId !== null) openFactor(open.parentId);
  }

  // While a slider moves: update the figures and the drawings, keep the rows.
  function setWeight(id, weight) {
    state.weights[id] = weight;
    tree = core.buildTree(catalogueRoot, state.scale, state.weights);
    const open = tree.byId.get(state.openId);
    for (const view of open.counted.concat(open.notCounted)) {
      const cell = $(`figures-${view.id}`);
      if (cell) cell.textContent = figures(view);
    }
    draw(open);
  }

  // When a slider is released: rebuild the rows, so a factor at 0 moves to "Not counted".
  function commitWeight(id, weight) {
    if (weight > 0) state.committed[id] = weight;
    state.weights[id] = weight;
    render(id);
  }

  function bringBack(id) {
    const view = tree.byId.get(id);
    const last = state.committed[id] !== undefined ? state.committed[id] : view.defaultWeight;
    const weight = last > 0 ? last : 1;
    state.committed[id] = weight;
    state.weights[id] = weight;
    render(id);
  }

  // The path and the weights panel

  function hasSubFactors(view) {
    return view.counted.length + view.notCounted.length > 0;
  }

  function figures(view) {
    return `${view.weight} · ${percent.format(view.share)}`;
  }

  function renderPath(open) {
    const items = core.pathTo(catalogueRoot, open.id).map((id) => {
      const view = tree.byId.get(id);
      if (id === open.id) return el("li", {}, el("span", { "aria-current": "page" }, view.name));
      const button = el("button", { type: "button" }, view.name);
      button.addEventListener("click", () => openFactor(id));
      return el("li", {}, button);
    });
    $("crumbs").replaceChildren(...items);
    $("back").disabled = open.parentId === null;
  }

  function renderWeights(open) {
    $("sliders").replaceChildren(...open.counted.map(sliderRow));
    $("not-counted").replaceChildren(...open.notCounted.map(notCountedRow));
    $("not-counted-block").hidden = open.notCounted.length === 0;
  }

  function sliderRow(view) {
    const inputId = `weight-${view.id}`;
    const input = el("input", { type: "range", id: inputId, min: "0", max: "5", step: "1", value: String(view.weight), "data-focus": view.id });
    input.addEventListener("input", () => setWeight(view.id, Number(input.value)));
    input.addEventListener("change", () => commitWeight(view.id, Number(input.value)));
    input.addEventListener("focus", () => showDetails(view.id, { anchor: input }));
    input.addEventListener("blur", hideTooltip);
    const row = el("li", { class: "slider-row" },
      el("label", { for: inputId }, view.name),
      el("span", { class: "figures", id: `figures-${view.id}` }, figures(view)),
      input);
    if (hasSubFactors(view)) {
      const button = el("button", { type: "button", class: "quiet", "aria-label": `Open ${view.name}` }, "Open");
      button.addEventListener("click", () => openFactor(view.id));
      row.append(button);
    }
    return row;
  }

  function notCountedRow(view) {
    const ownWeightIsZero = view.weight === 0;
    const action = ownWeightIsZero ? "Bring back" : "Open";
    const button = el("button", { type: "button", class: "quiet", "data-focus": view.id, "aria-label": `${action} ${view.name}` }, action);
    button.addEventListener("click", () => (ownWeightIsZero ? bringBack(view.id) : openFactor(view.id)));
    const reason = ownWeightIsZero ? "weight 0" : "all its sub-factors are at weight 0";
    return el("li", {}, el("span", {}, `${view.name} `, el("span", { class: "reason" }, `· ${reason}`)), button);
  }

  // The drawings

  function draw(open) {
    const data = twoLevels(open, 0);
    drawTreemap(data);
    drawSunburst(data, open);
  }

  // The open factor and two levels below it, keeping only the factors that count.
  function twoLevels(view, depth) {
    return {
      id: view.id,
      name: view.name,
      share: view.share,
      opens: hasSubFactors(view),
      children: depth < 2 ? view.counted.map((child) => twoLevels(child, depth + 1)) : [],
    };
  }

  function hierarchyOf(data) {
    return d3.hierarchy(data).sum((d) => (d.children.length > 0 ? 0 : d.share));
  }

  function sizeOf(svg) {
    const box = svg.getBoundingClientRect();
    return { width: Math.max(1, Math.round(box.width)), height: Math.max(1, Math.round(box.height)) };
  }

  // A "›" marks a factor that opens further than the drawing shows.
  function labelText(d) {
    return d.data.opens && !d.children ? `${d.data.name} ›` : d.data.name;
  }

  function bindEvents(selection) {
    selection
      .on("mouseenter", (event, d) => {
        highlight(d.data.id);
        showDetails(d.data.id, { event });
      })
      .on("mousemove", (event) => placeAtPointer(event))
      .on("mouseleave", () => {
        highlight(null);
        hideTooltip();
      })
      .on("click", (event, d) => {
        if (d.data.opens) openFactor(d.data.id);
        else showDetails(d.data.id, { event });
      });
  }

  function drawTreemap(data) {
    const svg = d3.select("#treemap");
    const { width, height } = sizeOf(svg.node());
    svg.attr("viewBox", `0 0 ${width} ${height}`);
    const root = hierarchyOf(data);
    d3.treemap()
      .size([width, height])
      .tile(d3.treemapSquarify)
      .round(true)
      .paddingInner(2)
      .paddingOuter((d) => (d.depth === 1 ? 2 : 0))
      .paddingTop((d) => (d.depth === 1 && d.children ? HEADER : 0))(root);
    const nodes = root.value > 0 ? root.descendants().filter((d) => d.depth > 0) : [];

    const cells = svg.selectAll("g.node").data(nodes, (d) => d.data.id);
    cells.exit().attr("class", "node-exit").transition().duration(MOTION).style("opacity", 0).remove();
    const entered = cells.enter().append("g").attr("class", "node").style("opacity", 0)
      .attr("transform", (d) => `translate(${d.x0},${d.y0})`);
    entered.append("rect").attr("width", (d) => d.x1 - d.x0).attr("height", (d) => d.y1 - d.y0);
    entered.append("text").attr("x", 6).attr("y", 14);
    const all = entered.merge(cells).order()
      .attr("data-id", (d) => d.data.id)
      .attr("data-depth", (d) => d.depth)
      .classed("is-group", (d) => Boolean(d.children))
      .call(bindEvents);
    all.transition().duration(MOTION).style("opacity", 1)
      .attr("transform", (d) => `translate(${d.x0},${d.y0})`);
    all.select("rect").transition().duration(MOTION)
      .attr("width", (d) => Math.max(0, d.x1 - d.x0))
      .attr("height", (d) => Math.max(0, d.y1 - d.y0));
    // Show a name only where it fits. The tooltip carries the rest.
    all.select("text").text(labelText).attr("visibility", function (d) {
      const room = d.children ? HEADER : d.y1 - d.y0;
      return this.getComputedTextLength() + 12 <= d.x1 - d.x0 && room >= 18 ? "visible" : "hidden";
    });
    emptyState(svg, nodes.length === 0, width / 2, height / 2);
  }

  function drawSunburst(data, open) {
    const svg = d3.select("#sunburst");
    const { width, height } = sizeOf(svg.node());
    svg.attr("viewBox", `${-width / 2} ${-height / 2} ${width} ${height}`);
    const radius = Math.min(width, height) / 2 - 2;
    const root = hierarchyOf(data);
    const levels = root.height + 1;
    const ring = radius / levels;
    d3.partition().size([2 * Math.PI, levels])(root);
    const arc = d3.arc()
      .startAngle((d) => d.x0)
      .endAngle((d) => d.x1)
      .padAngle((d) => Math.min((d.x1 - d.x0) / 2, 2 / radius))
      .padRadius(radius)
      .innerRadius((d) => d.y0 * ring + 1)
      .outerRadius((d) => d.y1 * ring - 1);
    const nodes = root.value > 0 ? root.descendants().filter((d) => d.depth > 0) : [];

    const arcs = svg.selectAll("g.arc").data(nodes, (d) => d.data.id);
    arcs.exit().attr("class", "arc-exit").transition().duration(MOTION).style("opacity", 0).remove();
    const entered = arcs.enter().append("g").attr("class", "arc").style("opacity", 0);
    entered.append("path");
    entered.append("text").attr("dy", "0.35em").attr("text-anchor", "middle");
    const all = entered.merge(arcs).order()
      .attr("data-id", (d) => d.data.id)
      .attr("data-depth", (d) => d.depth)
      .classed("is-group", (d) => Boolean(d.children))
      .call(bindEvents);
    all.transition().duration(MOTION).style("opacity", 1);
    all.select("path").transition().duration(MOTION).attrTween("d", function (d) {
      const target = { x0: d.x0, x1: d.x1, y0: d.y0, y1: d.y1 };
      const interpolate = d3.interpolate(this.__previous || target, target);
      this.__previous = target;
      return (t) => arc(interpolate(t));
    });
    // Names run along the radius where a ring has room, and flip on the left half.
    all.select("text").text(labelText)
      .attr("visibility", function (d) {
        const along = this.getComputedTextLength() + 10 <= ring - 2;
        const across = (d.x1 - d.x0) * ((d.y0 + d.y1) / 2) * ring >= 14;
        return along && across ? "visible" : "hidden";
      })
      .transition().duration(MOTION)
      .attr("transform", (d) => {
        const angle = (((d.x0 + d.x1) / 2) * 180) / Math.PI;
        const r = ((d.y0 + d.y1) / 2) * ring;
        return `rotate(${angle - 90}) translate(${r},0) rotate(${angle < 180 ? 0 : 180})`;
      });

    // The centre names the open factor. Clicking it goes back up.
    const centre = svg.selectAll("g.centre").data([open.id]);
    const centreEntered = centre.enter().append("g").attr("class", "centre");
    centreEntered.append("circle");
    centreEntered.append("text").attr("class", "centre-name").attr("text-anchor", "middle");
    centreEntered.append("text").attr("class", "go-up").attr("text-anchor", "middle");
    const canGoUp = open.parentId !== null;
    const centreAll = centreEntered.merge(centre).classed("can-go-up", canGoUp).on("click", goUp);
    centreAll.select("circle").attr("r", Math.max(0, ring - 1));
    centreAll.select(".centre-name").attr("y", canGoUp ? -2 : 4).text(open.name)
      .attr("visibility", function () {
        return this.getComputedTextLength() <= 2 * ring - 12 ? "visible" : "hidden";
      });
    centreAll.select(".go-up").attr("y", 16).text(canGoUp ? "‹ Back" : "");
    emptyState(svg, nodes.length === 0, 0, ring * 1.6);
  }

  function emptyState(svg, show, x, y) {
    const note = svg.selectAll("text.empty").data(show ? [0] : []);
    note.exit().remove();
    note.enter().append("text").attr("class", "empty").attr("text-anchor", "middle")
      .text("Nothing to draw: every sub-factor here is at weight 0.")
      .merge(note).attr("x", x).attr("y", y);
  }

  // Hover: highlight a factor and its family in both drawings.
  function highlight(id) {
    const lineage = id === null ? null : core.pathTo(catalogueRoot, id);
    d3.selectAll("#treemap g.node, #sunburst g.arc").classed("is-dim", (d) => {
      if (lineage === null) return false;
      const own = d.ancestors().map((a) => a.data.id);
      return !own.includes(id) && !lineage.includes(d.data.id);
    });
  }

  // Tooltip

  function showDetails(id, { event, anchor }) {
    const view = tree.byId.get(id);
    if (!view) return;
    const lines = [el("strong", {}, view.name)];
    if (view.description) lines.push(el("p", {}, view.description));
    lines.push(el("p", {}, `Weight ${view.weight}, ${percent.format(view.share)} of total weight`));
    lines.push(el("p", {}, `Status: ${view.status}`));
    if (view.weightReason) lines.push(el("p", {}, view.weightReason));
    const tip = $("tooltip");
    tip.replaceChildren(...lines);
    tip.hidden = false;
    if (event) {
      placeAtPointer(event);
    } else if (anchor) {
      const box = anchor.getBoundingClientRect();
      place(box.right + 12, box.top);
    }
  }

  function placeAtPointer(event) {
    place(event.clientX + 14, event.clientY + 14);
  }

  function place(x, y) {
    const tip = $("tooltip");
    tip.style.left = `${Math.max(8, Math.min(x, window.innerWidth - tip.offsetWidth - 8))}px`;
    tip.style.top = `${Math.max(8, Math.min(y, window.innerHeight - tip.offsetHeight - 8))}px`;
  }

  function hideTooltip() {
    $("tooltip").hidden = true;
  }

  // Controls

  document.querySelectorAll('input[name="scale"]').forEach((radio) => {
    radio.addEventListener("change", () => {
      state.scale = radio.value;
      highlight(null);
      hideTooltip();
      render();
    });
  });
  $("reset").addEventListener("click", () => {
    state.weights = {};
    state.committed = {};
    render();
  });
  $("back").addEventListener("click", goUp);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") hideTooltip();
  });
  let frame = 0;
  new ResizeObserver(() => {
    if (!tree) return;
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(() => draw(tree.byId.get(state.openId)));
  }).observe($("treemap"));

  // Wait for the fonts, so that labels are measured in the font they are drawn in.
  document.fonts.ready.then(load);
})();
</script>
</body>
</html>
```

- [ ] **Step 2: Embed the catalogue**

Run: `node docs/factors/embed-catalogue.mjs`
Expected: `Copied catalogue/factors.yaml into docs/factors/explorer.html.`

- [ ] **Step 3: Append the drift test to `docs/factors/embed-catalogue.test.mjs`, and run the tests**

At the top of the file, add `import { readFileSync } from "node:fs";`, and extend the existing import to `import { CATALOGUE, PAGE, embed, embeddedCopy } from "./embed-catalogue.mjs";`. Then append:

```js
test("the page's embedded copy matches catalogue/factors.yaml", () => {
  const yaml = readFileSync(CATALOGUE, "utf8").replace(/\r\n/g, "\n");
  assert.equal(embeddedCopy(readFileSync(PAGE, "utf8")), yaml, "Run: node docs/factors/embed-catalogue.mjs");
});
```

Run: `node --test "docs/factors/*.test.mjs"`, then `node docs/factors/embed-catalogue.mjs --check`
Expected: `ℹ tests 12`, `ℹ pass 12`, `ℹ fail 0`, then `The embedded catalogue is up to date.`

- [ ] **Step 4: Write the failing tests for the Artifact copy, `docs/factors/artifact-page.test.mjs`**

```js
// Tests for artifact-page.mjs. Run: node --test "docs/factors/*.test.mjs"
import test from "node:test";
import assert from "node:assert/strict";
import { artifactPage } from "./artifact-page.mjs";

test("artifactPage drops the document wrapper and keeps everything else", () => {
  const html = [
    "<!doctype html>",
    '<html lang="en-GB">',
    "<head>",
    '<meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
    "<title>Factor explorer</title>",
    "</head>",
    "<body>",
    "<main>Hello</main>",
    "</body>",
    "</html>",
    "",
  ].join("\r\n");
  assert.equal(artifactPage(html), "<title>Factor explorer</title>\n<main>Hello</main>\n");
});

test("artifactPage fails loudly when the wrapper is not where it expects", () => {
  assert.throws(() => artifactPage("<main>Hello</main>"), /Expected to remove 9 wrapper lines/);
});
```

Run: `node --test "docs/factors/*.test.mjs"`
Expected: `artifact-page.test.mjs` FAILS with `Cannot find module`.

- [ ] **Step 5: Write `docs/factors/artifact-page.mjs`**

```js
// Writes the Artifact copy of the explorer: the same page without the
// <!doctype>, <html>, <head> and <body> wrapper, which the Artifact host adds
// itself. Usage: node docs/factors/artifact-page.mjs <output.html>
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const PAGE = path.join(path.dirname(fileURLToPath(import.meta.url)), "explorer.html");
const WRAPPER = [
  /^<!doctype html>$/i,
  /^<html\b[^>]*>$/i,
  /^<head>$/i,
  /^<meta charset="utf-8">$/i,
  /^<meta name="viewport"[^>]*>$/i,
  /^<\/head>$/i,
  /^<body>$/i,
  /^<\/body>$/i,
  /^<\/html>$/i,
];

export function artifactPage(html) {
  const lines = html.split(/\r?\n/);
  const kept = lines.filter((line) => !WRAPPER.some((pattern) => pattern.test(line.trim())));
  const removed = lines.length - kept.length;
  if (removed !== WRAPPER.length) {
    throw new Error(`Expected to remove ${WRAPPER.length} wrapper lines, but removed ${removed}. Check the first and last lines of explorer.html.`);
  }
  return kept.join("\n");
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const output = process.argv[2];
  if (!output) {
    console.error("Usage: node docs/factors/artifact-page.mjs <output.html>");
    process.exit(2);
  }
  writeFileSync(output, artifactPage(readFileSync(PAGE, "utf8")));
  console.log(`Wrote the Artifact copy to ${output}.`);
}
```

Run: `node --test "docs/factors/*.test.mjs"`
Expected: `ℹ tests 14`, `ℹ pass 14`, `ℹ fail 0`.

- [ ] **Step 6: Commit**

```bash
git add docs/factors/explorer.html docs/factors/embed-catalogue.test.mjs docs/factors/artifact-page.mjs docs/factors/artifact-page.test.mjs
git commit -F - <<'EOF'
feat(explorer): add the factor explorer page

The treemap and the sunburst side by side, with weight sliders, a
"Not counted" list, drill-down, and a switch between the two scales.
The embedded catalogue is checked against catalogue/factors.yaml, and
artifact-page.mjs writes the copy that is published as an Artifact.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```

---

## Task 7: The browser check in Edge

**Files:** scratch only, never committed: `$SP/browser-check/` for `playwright-core`, `$SP/check-explorer.cjs`, and `$SP/shots/` for the screenshots.

- [ ] **Step 1: Install `playwright-core` in its own scratch folder.** It drives the installed Edge, so no browser is downloaded.

```bash
mkdir -p "$SP/browser-check" "$SP/shots" && cd "$SP/browser-check" && npm init -y >/dev/null && npm install --no-audit --no-fund playwright-core@1.64.1 && cd "E:/GitHub/Livability-Atlas"
```

- [ ] **Step 2: Write `$SP/check-explorer.cjs`**

```js
// Browser check for the factor explorer. It is not committed, because
// Playwright arrives with the web app in step 0.3.
// Usage: node check-explorer.cjs <tools-dir> <repo-root> <screenshot-dir>
const path = require("node:path");
const assert = require("node:assert/strict");
const { pathToFileURL } = require("node:url");

const [toolsDir, repo, shots] = process.argv.slice(2);
const { chromium } = require(path.join(path.resolve(toolsDir), "node_modules", "playwright-core"));
const pageUrl = pathToFileURL(path.join(repo, "docs", "factors", "explorer.html")).href;
const SETTLE = 450; // ms, longer than the page's 300 ms transitions

(async () => {
  const browser = await chromium.launch({ channel: "msedge", headless: true });
  const errors = [];

  async function open(viewport, colorScheme) {
    const context = await browser.newContext({ viewport, colorScheme });
    const page = await context.newPage();
    page.on("console", (message) => { if (message.type() === "error") errors.push(message.text()); });
    page.on("pageerror", (error) => errors.push(String(error)));
    await page.goto(pageUrl);
    await page.waitForSelector('#treemap g.node[data-depth="1"]');
    await page.waitForTimeout(SETTLE);
    return page;
  }
  const settle = (page) => page.waitForTimeout(SETTLE);
  const count = (page, selector) => page.locator(selector).count();
  const topLevel = (page, drawing) => count(page, `#${drawing} [data-depth="1"]`);
  const current = (page) => page.textContent('#crumbs [aria-current="page"]');
  const tileArea = (page, id) => page.evaluate((id) => {
    const d = document.querySelector(`#treemap g.node[data-id="${id}"]`).__data__;
    return (d.x1 - d.x0) * (d.y1 - d.y0);
  }, id);
  const arcAngle = (page, id) => page.evaluate((id) => {
    const d = document.querySelector(`#sunburst g.arc[data-id="${id}"]`).__data__;
    return d.x1 - d.x0;
  }, id);
  const clickInSvg = (page, selector) => page.evaluate((selector) => {
    document.querySelector(selector).dispatchEvent(new MouseEvent("click", { bubbles: true }));
  }, selector);

  const page = await open({ width: 1440, height: 1000 }, "light");

  // 1. The seed tree loads with no problems: 16 top-level factors within a city, 18 across cities.
  assert.equal(await page.isHidden("#problems"), true, "the page lists catalogue problems");
  assert.equal(await topLevel(page, "treemap"), 16);
  assert.equal(await topLevel(page, "sunburst"), 16);
  await page.click('label[for="scale-across-cities"]');
  await settle(page);
  assert.equal(await topLevel(page, "treemap"), 18);
  assert.equal(await topLevel(page, "sunburst"), 18);
  await page.click('label[for="scale-within-city"]');
  await settle(page);

  // 2. Moving a slider resizes that factor and its siblings, in both drawings.
  const before = {
    tile: await tileArea(page, "transport"), siblingTile: await tileArea(page, "safety"),
    arc: await arcAngle(page, "transport"), siblingArc: await arcAngle(page, "safety"),
  };
  await page.fill("#weight-transport", "5");
  await settle(page);
  assert.ok((await tileArea(page, "transport")) > before.tile, "Transport did not grow in the treemap");
  assert.ok((await tileArea(page, "safety")) < before.siblingTile, "Safety did not shrink in the treemap");
  assert.ok((await arcAngle(page, "transport")) > before.arc, "Transport did not grow in the sunburst");
  assert.ok((await arcAngle(page, "safety")) < before.siblingArc, "Safety did not shrink in the sunburst");

  // 3. Drilling down and going back work from both drawings.
  await page.click('#treemap g.node[data-id="environment"]', { position: { x: 12, y: 8 } });
  await settle(page);
  assert.equal(await current(page), "Environment");
  assert.equal(await topLevel(page, "treemap"), 5);
  assert.equal(await topLevel(page, "sunburst"), 5);
  await page.click("#back");
  await settle(page);
  assert.equal(await topLevel(page, "treemap"), 16);
  await clickInSvg(page, '#sunburst g.arc[data-id="environment"]');
  await settle(page);
  assert.equal(await current(page), "Environment");
  await clickInSvg(page, "#sunburst g.centre");
  await settle(page);
  assert.equal(await current(page), "All factors");

  // 4. A factor set to 0 moves to "Not counted", and "Bring back" restores its last weight.
  await page.fill("#weight-transport", "0");
  await settle(page);
  assert.equal(await count(page, '#treemap g.node[data-id="transport"]'), 0);
  assert.match(await page.textContent("#not-counted"), /Transport/);
  await page.click('#not-counted button[aria-label="Bring back Transport"]');
  await settle(page);
  assert.equal(await page.inputValue("#weight-transport"), "5");

  // 5. Switching scale goes up from a factor that does not apply at the new scale.
  await page.click('label[for="scale-across-cities"]');
  await settle(page);
  await page.click('#treemap g.node[data-id="climate"]', { position: { x: 12, y: 8 } });
  await settle(page);
  assert.equal(await current(page), "Climate");
  await page.click('label[for="scale-within-city"]');
  await settle(page);
  assert.equal(await current(page), "All factors");

  // 6. Screenshots in light and dark themes and at phone width, with no sideways scrolling.
  await page.click("#reset");
  await settle(page);
  await page.screenshot({ path: path.join(shots, "desktop-light.png"), fullPage: true });
  const dark = await open({ width: 1440, height: 1000 }, "dark");
  await dark.screenshot({ path: path.join(shots, "desktop-dark.png"), fullPage: true });
  const phone = await open({ width: 400, height: 900 }, "light");
  assert.ok(await phone.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), "the page scrolls sideways at phone width");
  await phone.screenshot({ path: path.join(shots, "phone-light.png"), fullPage: true });

  await browser.close();
  assert.deepEqual(errors, [], `console errors: ${errors.join(" | ")}`);
  console.log("Browser check passed.");
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
```

- [ ] **Step 3: Run the check**

Run: `node "$SP/check-explorer.cjs" "$SP/browser-check" "E:/GitHub/Livability-Atlas" "$SP/shots"`
Expected: `Browser check passed.`

If an assertion fails, use superpowers:systematic-debugging, fix the page or `explorer-core.js`, and run the unit tests and then this check again. A fix to `explorer-core.js` starts with a failing unit test.

- [ ] **Step 4: Look at the screenshots**

Read `$SP/shots/desktop-light.png`, `desktop-dark.png` and `phone-light.png`. Look for clipped or overlapping labels, unreadable text in either theme, and a layout that breaks at phone width. Fix what is wrong, then run the check once more.

- [ ] **Step 5: Commit any fixes**

```bash
git add docs/factors
git commit -F - <<'EOF'
fix(explorer): fixes from the browser check

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```

Skip this step when nothing changed.

---

## Task 8: The living documents

**Files:**

- Create: `docs/factors/README.md`
- Modify: `docs/codemap.md`, `docs/tech-stack.md`, `docs/glossary.md`, `CLAUDE.md`, `docs/README.md` and `docs/roadmap.md`

- [ ] **Step 1: Write `docs/factors/README.md`**

````markdown
# Factor explorer and research notes

Tools and notes for building the factor catalogue in step 0.2 of Phase 0.

| File | What it is |
| --- | --- |
| [explorer.html](explorer.html) | The factor explorer: the factor tree drawn as a treemap and as a sunburst, with weight sliders. Its design is in the [spec](../specs/2026-10-24-factor-explorer.md) |
| `explorer-core.js` | The explorer's logic, without any drawing |
| `embed-catalogue.mjs` | Copies `catalogue/factors.yaml` into the page |
| `artifact-page.mjs` | Writes the copy of the page that is published as an Artifact |
| `*.test.mjs` | The tests, run with Node's built-in test runner |
| [research-notes.md](research-notes.md) | Starting points for the rest of step 0.2, carried over from the Phase 0 plan |

## Open the explorer

Open `explorer.html` in a browser. It needs an internet connection for D3 and js-yaml. The owner reviews the published Artifact.

## After editing the catalogue

```sh
node docs/factors/embed-catalogue.mjs
node --test "docs/factors/*.test.mjs"
```

Then publish the Artifact again. `node docs/factors/artifact-page.mjs <output.html>` writes the Artifact copy, which is published with `explorer-core.js` beside it.
````

- [ ] **Step 2: Update `docs/codemap.md` with three replacements**

1. Replace this block:

   ```text
   ├── .gitattributes         # line-ending normalisation
   └── docs/
   ```

   with:

   ```text
   ├── .gitattributes         # line-ending normalisation
   ├── catalogue/             # the factor catalogue
   │   ├── README.md          # what it holds, and how it is checked
   │   └── factors.yaml       # the factor tree, with default weights
   └── docs/
   ```

2. Replace this block:

   ```text
       ├── codemap.md         # this file
       ├── methodology/
   ```

   with:

   ```text
       ├── codemap.md         # this file
       ├── factors/           # the factor explorer and research notes (step 0.2)
       │   ├── README.md            # how to open, refresh, test and publish the explorer
       │   ├── explorer.html        # the factor explorer page
       │   ├── explorer-core.js     # its logic, without drawing
       │   ├── embed-catalogue.mjs  # copies catalogue/factors.yaml into the page
       │   ├── artifact-page.mjs    # writes the copy published as an Artifact
       │   ├── *.test.mjs           # tests, run with Node's test runner
       │   └── research-notes.md    # research tables from the Phase 0 plan
       ├── methodology/
   ```

3. Replace this block:

   ```text
       └── specs/             # design specs, one per work item
           └── 2026-10-24-factor-explorer.md
   ```

   with:

   ```text
       ├── plans/             # implementation plans, one per work item
       │   └── 2026-10-24-factor-explorer.md
       └── specs/             # design specs, one per work item
           └── 2026-10-24-factor-explorer.md
   ```

- [ ] **Step 3: Update `docs/tech-stack.md` with three replacements**

1. Replace `Status: planned. Nothing is installed yet. Step 0.3 of Phase 0` with `Status: planned. Nothing is installed yet: the factor explorer (step 0.2) loads its two libraries from cdnjs and runs its tests with Node's built-in test runner. Step 0.3 of Phase 0`.
2. Replace the `d3-hierarchy` row with these two rows:
   - `` | [D3](https://d3js.org/) 7.9: d3-hierarchy, d3-shape and d3-transition | Treemap and sunburst layouts and drawing for the visual factor tree | Full control over sizing, drill-down and animation | ECharts (less control) | 0.2 (factor explorer, from cdnjs) | ``
   - `` | [js-yaml](https://github.com/nodeca/js-yaml) 4.1 | Reads the embedded `catalogue/factors.yaml` inside the factor explorer | The page keeps the catalogue as YAML, with no build step | Converting to JSON first, which needs a build step before step 0.3 | 0.2 (factor explorer, from cdnjs) | ``
3. After the `just` row, add: `` | [Node's test runner](https://nodejs.org/api/test.html) (`node --test`) | Tests for the factor explorer before the scaffold exists | Built into Node 24, so nothing is installed | Vitest, which arrives with the web app | 0.2 | ``

- [ ] **Step 4: Update the remaining documents**

- `docs/glossary.md`. In the "For contributors" part, under "Data pipeline", add after the "Factor catalogue" row: `| Research status | How far a factor has got: idea, researched, spiked (tried in a spike) or built | Every factor in the seed tree is an idea |`
- `CLAUDE.md`. Replace ``None yet. Step 0.3 adds a `justfile`, and every command (setup, check, test, validate, build, dev, docs) will then run through `just`. Until then, only git is used.`` with:

  ```markdown
  Step 0.3 adds a `justfile`, and every command (setup, check, test, validate, build, dev, docs) will then run through `just`. Until then:

  - `node --test "docs/factors/*.test.mjs"` runs the factor explorer's tests.
  - `node docs/factors/embed-catalogue.mjs` refreshes the explorer after an edit to `catalogue/factors.yaml`.
  ```

- `docs/README.md`. Replace ``- `plans/` for implementation plans`` with `- [plans/](plans/) for implementation plans`. After the `interface.md` row, add `| [factors/README.md](factors/README.md) | The factor explorer, and research notes for building the factor catalogue |`.
- `docs/roadmap.md`. At the end of the "Factor explorer:" item, after a space, add `Built and published; the layout choice is next.`

- [ ] **Step 5: Check and commit**

Run the documentation check on `docs/factors/README.md docs/codemap.md docs/tech-stack.md docs/glossary.md CLAUDE.md docs/README.md docs/roadmap.md`. Then:

```bash
git add docs/factors/README.md docs/codemap.md docs/tech-stack.md docs/glossary.md CLAUDE.md docs/README.md docs/roadmap.md
git commit -F - <<'EOF'
docs: document the factor explorer

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```

---

## Task 9: Publish the Artifact and open the pull request

**Files:**

- Modify: `docs/progress.md`

- [ ] **Step 1: Write the Artifact copy**

```bash
mkdir -p "$SP/artifact" && node docs/factors/artifact-page.mjs "$SP/artifact/explorer.html"
```

Expected: `Wrote the Artifact copy to …/artifact/explorer.html.`

- [ ] **Step 2: Publish it with the Artifact tool**

- `file_path`: `$SP/artifact/explorer.html`, the absolute scratchpad path
- `files`: `{"explorer-core.js": "docs/factors/explorer-core.js"}`
- `icon`: `chart`
- `description`: `The factor catalogue's tree as a treemap and a sunburst side by side, with live weight sliders, for choosing how the app draws it.`

Open the link once and confirm that it draws both layouts. The page's own checks have already run in Task 7.

- [ ] **Step 3: Update `docs/progress.md`**

- Replace the second "Now" bullet with: ``- Step 0.2: the factor explorer is built and published as a private Artifact for the owner. Its pull request is open from `feat/factor-explorer`.``
- Replace "Next" items 1 and 2 with:
  1. `The owner tries both layouts in the factor explorer and chooses one. Record the choice in D17 and interface.md, then merge the pull request.`
  2. `The rest of step 0.2: expand the factor catalogue top-down and bottom-up, starting from [research-notes.md](factors/research-notes.md).`
- At the top of the 2026-10-24 log entry, add: ``- **Factor explorer built.** The seed factor tree is in `catalogue/factors.yaml`, and the page has its tests and a browser check in Edge. It is published as a private Artifact, and its pull request is open.``

The Artifact's link stays out of the public repo, because it is private to the owner.

Run the documentation check on `docs/progress.md`, then commit:

```bash
git add docs/progress.md
git commit -F - <<'EOF'
docs: record the factor explorer in the progress log

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```

- [ ] **Step 4: Push and open the pull request.** Approving this plan approves this step. Merging waits for the owner's word.

```bash
git push -u origin feat/factor-explorer
gh pr create --base main --head feat/factor-explorer --title "feat: factor explorer (step 0.2)" --body-file - <<'EOF'
## Summary

The first work item of step 0.2: a page that draws the factor catalogue's tree as a treemap and a sunburst side by side, so that the layout of the app's visual factor tree can be chosen (D17).

- `catalogue/factors.yaml`: the seed factor tree, with 18 top-level factors and placeholder default weights until D14.
- `docs/factors/explorer.html`: the page, with weight sliders, a "Not counted" list, drill-down and a switch between the two scales.
- `docs/factors/explorer-core.js`: the page's logic, tested with Node's built-in test runner.
- Two scripts: one copies the catalogue into the page, and one writes the copy that is published as an Artifact.
- `docs/factors/research-notes.md`: research tables from the Phase 0 plan, for the rest of step 0.2.
- The spec and this implementation plan, in `docs/specs/` and `docs/plans/`.

## Checks

- `node --test "docs/factors/*.test.mjs"`: 14 tests pass.
- A browser check in Edge passes: sliders resize both drawings, drill-down and "Back" work, a factor at weight 0 moves to "Not counted", and the page works in light and dark themes and at phone width.
- Links resolve, and markdownlint passes.
- There is no CI yet. Step 0.3 adds it.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
```

- [ ] **Step 5: Hand over.** Give the owner the Artifact link and the pull request link. When the owner chooses the layout, record the choice in D17 (`docs/decisions.md`, with a dated history line) and in `docs/interface.md` on the same branch, then merge when the owner says so.

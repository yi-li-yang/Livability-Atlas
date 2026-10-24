# Factor explorer

Status: built, and revised after the owner's first review. The first work item of Phase 0, step 0.2 ([roadmap](../roadmap.md)).

## Why

Step 0.2 builds the factor catalogue, and D17 must decide how the app draws the factor tree: as a treemap or as a sunburst. Both tasks need the tree on screen. The factor explorer is one page that draws the factor catalogue's tree in both layouts. The owner uses it to review the catalogue as it grows, and used it to choose the layout. Having tried the two side by side, the owner chose to keep both, with a switch between them, and asked for each factor to have its own colour (D17).

The page also tries out the three interactions that the app's visual factor tree needs ([interface.md](../interface.md#visual-factor-tree)):

- Moving a weight slider resizes that factor and its siblings.
- Clicking a factor opens its sub-factors.
- A factor at weight 0 leaves the drawing for a "Not counted" list.

## What it does not do

- It scores no hex cells and draws no map.
- It does not save weights. Reloading the page restores the default weights.
- It does not edit the catalogue. The catalogue is edited as YAML.
- It shows only what the catalogue holds. Datasets and scoring curves appear once the top-down pass adds them.

## Approach

**Chosen: one HTML page that draws with D3 loaded from a CDN.** The page needs no build step and no installed packages, so it works before the step 0.3 scaffold exists. It opens with a double-click, needing only an internet connection for its two libraries. Without its document wrapper, the same page publishes as an Artifact. D3's hierarchy layouts are the ones [tech-stack.md](../tech-stack.md) plans for the app, so the sizing behaviour carries over.

Two alternatives were rejected:

- **Starting the React app now.** The code would carry into Phase 1. But it pulls the step 0.3 scaffold forward before the catalogue exists, and it would fix the app's components before the layout is chosen.
- **A charting library with ready-made treemaps and sunbursts, such as ECharts.** It needs less code. But it gives less control over sizing and drill-down, which are what the explorer tests. tech-stack.md rejects ECharts for the same reason.

The page's code is a prototype. Phase 1 rebuilds the visual factor tree in the app. The catalogue and the tested sizing rules carry over.

## Files

| File | What it does |
| --- | --- |
| `catalogue/factors.yaml` | The factor tree: the single source for factors, their default weights and the reasons for them. This work item writes its first version, the seed tree |
| `catalogue/README.md` | What the catalogue holds, and how it is checked |
| `docs/factors/explorer.html` | The page. It holds an embedded copy of `factors.yaml` and draws it |
| `docs/factors/explorer-core.js` | The page's logic, without any drawing. It checks the catalogue, filters it by scale and computes each factor's share of total weight. The page and the tests both load it |
| `docs/factors/*.test.mjs` | The tests, run with `node --test "docs/factors/*.test.mjs"` |
| `docs/factors/embed-catalogue.mjs` | Copies `factors.yaml` into the page. With `--check`, it only reports whether the copy is out of date |
| `docs/factors/artifact-page.mjs` | Writes the copy of the page that is published as an Artifact, without the document wrapper that the Artifact host adds itself |
| `docs/factors/research-notes.md` | Research tables from the Phase 0 plan, kept for the rest of step 0.2 |
| `docs/factors/README.md` | How to open, refresh, test and publish the explorer |

The scripts use only Node's built-in modules. The page loads two libraries from cdnjs, D3 and js-yaml, at pinned versions with integrity hashes.

## The seed factor tree

The first `catalogue/factors.yaml` holds the 18 top-level factors and their sub-factors from the approved Phase 0 plan. Environment keeps the deeper tree from [scoring.md](../methodology/scoring.md#2-the-factor-tree). Measured indicators, datasets and scoring curves arrive with the top-down pass.

Each node has these fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `id` | yes | A unique kebab-case name, such as `air-quality`. The checks reject duplicates |
| `name` | yes | The plain name the page shows |
| `default_weight` | yes | A whole number from 0 to 5 |
| `weight_reason` | when the weight is not the placeholder 3 | Why the default weight is what it is |
| `description` | no | One sentence |
| `scales` | on top-level factors | `within-city`, `across-cities`, or both. A sub-factor inherits its parent's scales, or lists a subset of them |
| `status` | no | `idea` (if left out), `researched`, `spiked` or `built` |
| `children` | no | The sub-factors |

**The default weights are placeholders.** D14 sets default weights from evidence later in step 0.2. Until then three rules apply:

- Every factor gets 3, so that no factor looks more important by accident.
- The two supporting factors, published rankings and resident wellbeing, get 1, because D14 starts supporting factors low.
- Choice factors get 0 until the user picks something (D18): your industry, your cuisines, your community, faith and destinations. Community composition also starts at 0 (D08).

**Scales.** Climate and Governance and rights apply across cities only. Within London, climate barely varies, and its one varying part, urban heat, sits under Environment. The other 16 top-level factors apply at both scales, with different sub-factors at each.

**Overlaps listed once.** The plan's factor table names three things twice. The seed keeps each in one place:

- GP access under Health care, not under Daily amenities
- life expectancy under Resident wellbeing, not under Health care
- jobs within reach under Work and economy, not under Transport

## The page

**Layout.** A header holds the title, the layout switch ("Treemap" or "Sunburst"), the scale switch ("Within a city" or "Across cities") and a "Reset weights" button. Below it are the weights panel and one drawing, in the chosen layout. The treemap shows first, and the browser remembers the viewer's choice. On a narrow screen the drawing comes first, above the weights panel.

**What is drawn.** The drawing shows the open factor and two levels of sub-factors below it. At first the open factor is the root, so the drawing shows the top-level factors and their sub-factors. Each area is proportional to its share of total weight, computed as in [scoring.md, section 5](../methodology/scoring.md#5-weights-and-aggregation-up-the-tree):

- Each factor splits its share among its sub-factors in proportion to their weights.
- A factor at weight 0 is not drawn.
- A factor whose sub-factors all have weight 0 counts as weight 0.

**Interactions.**

- The weights panel lists the sub-factors of the factor that is drawn. Each has a slider from 0 to 5 in whole steps, and its share of total weight. Moving a slider resizes that factor and its siblings in the drawing at once.
- A factor set to 0 leaves the drawing and the sliders, and joins a "Not counted" list. "Bring back" restores its last weight above 0, or 1 if it never had one.
- Clicking a factor that has sub-factors opens it. Clicking one without sub-factors only shows its details. A breadcrumb shows the path. "Back", the breadcrumb and the sunburst's centre all go back up.
- Hovering over a factor in the drawing, or focusing its row in the weights panel, shows its name, description, weight, share of total weight, status and weight reason.
- The layout switch redraws the open factor in the other layout, and keeps the weights set so far.
- The scale switch redraws the tree for the other scale and keeps the weights set so far. If the open factor does not apply at the new scale, the drawing goes up to its nearest parent that does.

**Colour and labels.** Each factor has its own colour, from the categorical palette of the Salt design system (J.P. Morgan, Apache-2.0). Its 20 colours have equal lightness, and each carries white text at 4.5:1 contrast or more.

- Top-level factors take 18 of the 20 colours, leaving out Salt's two greys. Their order keeps neighbouring factors clearly apart, for normal and colour-blind vision, in both scales: by the measure in the project's chart guidance (OKLab Delta E), at least 15.1 and 8.9, above its floors of 15 and 8. Where the order allows, colour fits meaning: Environment is green, Climate blue and Animal friendliness "fur" brown.
- A colour follows the factor's position in the catalogue, so it does not change when the scale or the weights hide a sibling.
- When a factor is open, its sub-factors take colours from a second sequence of nine, whose neighbours stay apart for any number of sub-factors up to nine.
- Sub-factors one level further down take a tint of their factor's colour: Salt's step 200 in the light theme and step 800 in the dark. Full colours carry white labels and tints carry ink labels, at 4.5:1 contrast or more.
- The weights panel shows each factor's colour beside its name, so it doubles as the legend, and each slider takes its factor's colour.
- Colour is never the only cue. Eighteen colours cannot all stay distinct: some tints come close, such as Natural hazards and Digital connectivity. So labels and tooltips name every factor, each family sits inside its own frame or beside its parent's ring, and hovering over a factor highlights it and its family.
- The interface itself uses ink, not colour, for selected controls and focus, so colour on the page always means data.

**Keyboard.** Every action works from the keyboard. The sliders are standard controls, and each row of the weights panel has an "Open" button for factors with sub-factors.

**Motion.** Resizing and drill-down animate for 300 ms. When the browser asks for reduced motion, they change at once.

**Errors.** If the catalogue fails to parse or fails a check, the page draws nothing and lists each problem: the line number for a YAML error, and the factor's id for a failed check.

## Refreshing the embedded copy

Until step 0.3, a change to the catalogue takes four steps:

1. Edit `catalogue/factors.yaml`.
2. Run `node docs/factors/embed-catalogue.mjs`.
3. Run `node --test "docs/factors/*.test.mjs"`.
4. Publish the Artifact again.

From step 0.3, `just docs` runs steps 2 and 3, and `atlas validate` takes over the catalogue checks.

## Testing

The tests are written before the code, as the task loop requires. The unit tests cover `explorer-core.js`, the embedded copy and the Artifact copy:

- The shares of total weight match the worked example in scoring.md: 0.40, 0.40 and 0.20 at the top, 0.10 for Air quality, and 0.05 for NO₂.
- Setting a weight to 0 removes the factor and rescales its siblings.
- A factor whose sub-factors all have weight 0 counts as weight 0.
- The scale filter keeps only the factors for that scale, and sub-factors inherit scales.
- The checks reject a duplicate id, an id that is not kebab-case, a weight outside 0–5, a weight other than 3 without a reason, a missing name, an unknown scale or status, and a sub-factor scale that its parent lacks.
- The embedded copy matches `catalogue/factors.yaml`.
- The Artifact copy drops exactly the document wrapper, and nothing else.

A browser check runs Playwright against the installed Edge, from a scratch folder. It is not committed, because Playwright arrives with the web app in step 0.3. It confirms that:

- the seed tree loads with no errors, and shows 16 top-level factors within a city and 18 across cities
- the layout switch shows one layout at a time, and the browser remembers it
- moving a slider resizes that factor and its siblings, in both layouts
- drilling down and going back work in both layouts
- each top-level factor has its own colour, which does not change with the scale, and an open factor's sub-factors have their own colours
- every visible label keeps 4.5:1 contrast with its shape, in light and dark themes
- a factor set to 0 moves to "Not counted", and "Bring back" restores it
- the page works at phone width and in light and dark themes, judged from screenshots

## Publishing

The page and `explorer-core.js` are published together as a private Artifact called "Factor explorer", so the owner can open it from a link. `artifact-page.mjs` first writes the page without its document wrapper, because the Artifact host adds its own. It is published again after each change to the catalogue during step 0.2.

## Done when

- The unit tests and the browser check pass.
- The Artifact is published and the owner has its link.

The layout choice comes after. When the owner chooses the treemap or the sunburst, D17 and interface.md record the choice.

## Later

These are left out until the catalogue needs them:

- colouring by status, once statuses vary
- showing each measured indicator's datasets and scoring curve, once the top-down pass adds them
- saving or sharing a set of weights

# Interface

Status: planned (D17, proposed). The layout of the visual factor tree, treemap or sunburst, will be chosen after the factor explorer prototype in step 0.2 of Phase 0.

## Progressive disclosure

The surface shows what a decision needs. Each further layer opens only when the user asks, and every layer is one action away from the layer above it.

| Layer | What the user sees | How they get there |
| --- | --- | --- |
| 1. Map | Hex cells coloured by livability score; a short legend; the top neighbourhoods by name and score | The default view |
| 2. Quick look | Neighbourhood name, score and rank, its two biggest strengths and its biggest weakness (e.g. "+ Transport, + Green space, − Cost") | Hover over or tap a hex cell |
| 3. Why this score | One bar per top-level factor, showing its score contribution | Click the hex cell |
| 4. Inside a factor | That factor's sub-factor scores | Open the factor's dropdown |
| 5. Evidence | Raw value and unit, scoring curve, dataset, date, licence and evidence type | The "details" link on a measured indicator |

The same rule applies across the app:

- The preferences panel shows top-level factors, and sub-factors open in dropdowns.
- Inside a dropdown, subjective factors show a "more ↔ less" switch or an ideal-range slider, and choice factors show a picker.
- Scoring curves and data-coverage settings sit behind "Advanced".
- Dataset credits sit behind "About the data".
- On a phone, panels become bottom sheets that slide up over the map.

## Visual factor tree

The preferences panel draws the factor tree, and each factor's area is its share of the total weight.

- **Resizing.** Moving a weight slider resizes that factor at once, and the others shrink or grow to match. This is exactly how weights act in the score.
- **Drill-down.** Clicking a factor zooms into its sub-factors, which resize the same way. "Back" returns to the level above.
- **Weight 0.** A factor at weight 0 leaves the drawing and moves to a short "not counted" list, from which it can be brought back.
- **Layout.** A treemap (nested rectangles) or a sunburst (rings around a centre). The factor explorer shows both, and one is chosen.

## Controls inside a factor

| Control | For | Example |
| --- | --- | --- |
| Weight slider, 0–5 | Every factor | |
| "More ↔ less" switch | Measured indicators of preference type "user direction" | Rain, nightlife nearby |
| Ideal-range slider | Preference type "user range" | Summer temperature |
| Picker | Preference type "user choice" | Industry, cuisines, community group, faith |
| Hard limit | Any measured indicator with a must-have threshold | Rent no higher than a cap |

## Plain and accessible

- Labels use only the words in the glossary's [In the app](glossary.md#in-the-app) part, which carry no jargon.
- Colours stay readable for colour-blind users.
- Everything works with a keyboard.
- The ranked list is a full alternative to the map for screen-reader users.

# Interface

Status: planned (D17, accepted). The factor explorer in step 0.2 of Phase 0 prototypes the visual factor tree.

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
- The legend's "Show on the map" list colours the map by one factor's or one measured indicator's own score in place of the livability score ([spec](specs/2026-10-29-map-by-factor.md)). The ranking, the top neighbourhoods and the hard limits stay as they are, and the quick look and the reasons add the score on the map beside the livability score.
- On a phone, panels become bottom sheets that slide up over the map.

## Visual factor tree

The preferences panel draws the factor tree, and each factor's area is its share of the total weight.

- **Resizing.** Moving a weight slider resizes that factor at once, and the others shrink or grow to match. This is exactly how weights act in the score.
- **Drill-down.** Clicking a factor zooms into its sub-factors, which resize the same way. "Back" returns to the level above.
- **Weight 0.** A factor at weight 0 leaves the drawing and moves to a short "not counted" list, from which it can be brought back.
- **Layout.** A treemap (nested rectangles) or a sunburst (rings around a centre), with a switch between them. The treemap shows first (D17). The app calls them "Boxes" and "Rings", the switch sits beside the heading, and the choice is kept in the browser and not in the link, since it is how the user likes to see the factors and not what they want.
- **The rings.** An inner ring of the factors at this level, each as wide as its share of the weight, with the counted sub-factors of each in a lighter ring outside it, sharing its angle. The centre names the level. Pointing at an arc names it and gives its share, clicking an arc opens the factor (an outer arc opens its factor and the sub-factor inside it), and clicking the centre goes up a level. The sliders beside the drawing stay the way to set a weight, and the way to use a keyboard.
- **Colour.** Each factor has its own colour, from the categorical palette of the Salt design system. Its sub-factors take a tint of it. The weights panel shows each colour beside its factor's name, so it doubles as the legend, and labels name every shape, so colour is never the only cue.

## Controls inside a factor

| Control | For | Example |
| --- | --- | --- |
| Weight slider, 0–5 | Every factor | |
| "More ↔ less" switch | Measured indicators of preference type "user direction" | Rain, nightlife nearby |
| Ideal-range slider | Preference type "user range" | Summer temperature |
| Picker | Preference type "user choice" | Industry, cuisines, community group, faith |
| Hard limit | Any measured indicator with a must-have threshold. They are set in their own "Hard limits" section under the factor tree: choose a measure, then at most or at least a number, or the categories allowed. A hex cell that fails one is greyed out and not ranked | Rent no higher than a cap |

## Plain and accessible

- Labels use only the words in the glossary's [In the app](glossary.md#in-the-app) part, which carry no jargon.
- Colours stay readable for colour-blind users.
- Everything works with a keyboard.
- The ranked list is a full alternative to the map for screen-reader users.

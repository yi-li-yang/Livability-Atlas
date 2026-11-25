---
# generated from tokens.json by dev/visual-preference/build.py · visual-preference 1.0.0 · do not edit
# Copy into the project as DESIGN.md and replace {{project}} with its name; change nothing else.
name: "Livability Atlas"
description: "Built on Yili Yang's visual system 1.0.0. Dark is home; one accent: lichen."
colors:
  ground: "#141413"
  surface: "#1c1c1b"
  raised: "#242522"
  rule: "#363734"
  edge: "#6e6f6c"
  muted: "#a0a09d"
  ink: "#e8e7e3"
  accent: "#a3b86c"
  data-sky: "#a9cfe6"
  data-rust: "#c4573a"
  data-spruce: "#4f9a7d"
  data-sand: "#d8c48e"
  data-dusk: "#8a7fb8"
  data-ochre: "#c9962e"
  data-glacier: "#86b2d4"
  data-rose: "#d98ca0"
  data-olive: "#b0ac5a"
colors-light:
  ground: "#f4f2f0"
  surface: "#ebe9e6"
  raised: "#ffffff"
  rule: "#d2d1cd"
  edge: "#82837f"
  muted: "#5e5f5c"
  ink: "#1b1c1a"
  accent: "#566a26"
  data-sky: "#48606e"
  data-rust: "#9c3f27"
  data-spruce: "#307f67"
  data-sand: "#9e8a59"
  data-dusk: "#72679f"
  data-ochre: "#9e7002"
  data-glacier: "#6490b0"
  data-rose: "#bc7387"
  data-olive: "#7a801b"
typography:
  label:
    fontFamily: "\"Albert Sans\", system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 500
    lineHeight: 1.55
    letterSpacing: "0.1em"
  small:
    fontFamily: "\"Albert Sans\", system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.55
  body:
    fontFamily: "\"Albert Sans\", system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.55
  h3:
    fontFamily: "\"Albert Sans\", system-ui, sans-serif"
    fontSize: "20px"
    fontWeight: 600
    lineHeight: 1.15
  h2:
    fontFamily: "\"Albert Sans\", system-ui, sans-serif"
    fontSize: "25px"
    fontWeight: 600
    lineHeight: 1.15
  h1:
    fontFamily: "\"Albert Sans\", system-ui, sans-serif"
    fontSize: "31px"
    fontWeight: 600
    lineHeight: 1.15
  display:
    fontFamily: "\"Albert Sans\", system-ui, sans-serif"
    fontSize: "49px"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  num:
    fontFamily: "\"IBM Plex Mono\", ui-monospace, monospace"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.55
  code:
    fontFamily: "\"IBM Plex Mono\", ui-monospace, monospace"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.55
  doc-h1:
    fontFamily: "\"Source Serif 4\", Georgia, serif"
    fontSize: "31px"
    fontWeight: 600
    lineHeight: 1.15
  doc-h2:
    fontFamily: "\"Source Serif 4\", Georgia, serif"
    fontSize: "25px"
    fontWeight: 600
    lineHeight: 1.15
  doc-h3:
    fontFamily: "\"Source Serif 4\", Georgia, serif"
    fontSize: "20px"
    fontWeight: 600
    lineHeight: 1.15
rounded:
  none: "0"
  dot: "9999px"
spacing:
  space-1: "4px"
  space-2: "8px"
  space-3: "12px"
  space-4: "16px"
  space-6: "24px"
  space-8: "32px"
  space-12: "48px"
  space-16: "64px"
  space-24: "96px"
---

# Design System: Livability Atlas

This project uses Yili Yang's visual system, version 1.0.0. The values above come from it; change them there, not here. Its manual explains each choice.

**The accent is lichen.** It marks the one focus or action in a view: the filled button, the selected tab, the focus ring, the full stop after the project's name. It is never used for data and never next to another accent.

## Principles, in order

1. **Readable by everyone.** Text at WCAG AA contrast in both themes; colour is never the only cue.
2. **The work leads.** The interface stays in the stone neutrals; maps, images and data carry the colour.
3. **Colour means something.** The accent marks focus or action; the data colours mark data.
4. **Editorial clarity.** Hierarchy from size, weight and space; text aligned left; units and sources visible.
5. **Built like an instrument.** Square corners, hairline rules, monospace numbers, matte surfaces: no glow, glass or soft shadow.


## This project

Everything above is the visual system's, copied at version 1.0.0 (skills repo, commit `1084fba`). What follows is the part that only this app decides: what its colours mean, and how the system's rules land on a map. The code is the source of each value named here.

**The Field Notebook.** The map of hex cells is the page's subject and takes nearly all of it; the panels are notes in its margin, plain and exact, and nothing in them competes with the map. This is not an estate agent's site (no photographs, no sales words) and not a dashboard (no grid of cards or headline figures).

### Colour carries three meanings, and only these

- **The score scale** (`web/src/features/map/colour.ts`): red is worse, yellow middling, blue-green better, on the cells, the legend and every bar. It is the project's own learned scale and stays: its stops are at ΔE 12 or more under simulated deuteranopia, protanopia and tritanopia, and every bar also shows its score as a length and a number. Never a second score scale, and never a factor colour beside a score.
- **The factors' own colours** (`web/src/features/factors/colours.ts`): the system's Earth 8, in its order, one per top-level factor in the catalogue's order. In a factor's box the name sits on the colour, so the box takes the colour mixed towards a ground that keeps the name at 4.5:1 or more (`index.css`): on the dark ground, the colour lifted 15% towards ink with the name in the ground colour; on the light ground, the colour at 55% on white with the name in ink. A sub-factor takes a 30% (dark) or 25% (light) tint. Every box and row also carries the factor's name, so a colour that comes round again on a ninth factor never stands alone.
- **The land under the cells** (`web/src/features/map/theme.ts`): faint tints of green, violet-grey and brown-grey for parks, industry and railways, which show in a cell with few or no homes. They stay far from every score colour at the cells' opacity.

The accent, lichen, marks the focus ring, the name's full stop, and the one filled button: "Show the reasons" in a phone's peek at a cell, the only action in that view. It is never on the map: its yellow-green lies inside the score scale, so the selected cell is outlined in ink instead.

### The map

- **Dark** (home): OpenFreeMap's Positron repainted in the stone of the dark ground (`stack.ts`): water a blue-stone, roads a step lighter than the ground at half opacity so that they cross the cells without netting them, names in the muted grey with a ground halo. A cell left out by a hard limit is a mid stone grey that recedes.
- **Light**: Positron's own pale map, with the land use tints as before, and a light grey for a cell left out.
- The cells sit over the land and under the water, roads and names (D23), at 80% until the user changes it.
- The marks over the cells (the top neighbourhoods' numbered discs, the selected cell) are drawn in ink and ground, so that they read on any cell in either theme. The numbers are in the monospace face.
- The map is made for one theme; when the reader's system setting changes, it is made again.

### Layout and components

- The map fills the window under a slim header (the name and its stop, over a hairline rule) and above a one-line "About the data".
- Panels float over the map's edges on `raised`, square, with the one `float` shadow: the preferences top left, the legend bottom left, the reasons top right, the quick look beside the pointer. On a phone (under 768 px) the legend sits at the top and the preferences lie in a sheet along the bottom with three stops: shut, half and full.
- Labels over groups ("What matters to you", "Show on the map", "Why this score") are spaced capitals in the muted grey. Body text in the panels is 14 px (the system's small), help and notes 12 px.
- Actions are underlined words, except the phone's "Show the reasons", filled in the accent with ground text. A switch ("Boxes / Rings", "Score / Rank in London", "Add up / No weak spots") fills its chosen side in ink with ground text. Sliders, check boxes and radio buttons take the ink colour, since there are many in a view and the accent marks one thing.
- Every score, share, rank and count that changes or sits in a column is in IBM Plex Mono; the words around it stay in Albert Sans.
- An error the user must act on is a line of ink text at weight 500, with words that say what went wrong; a warning is a quiet box on `surface` with an `edge` border.

### Do not

- Do not add a colour that means nothing, a second score scale, or a factor colour on a score.
- Do not put the accent on the map, or on more than one thing in a view.
- Do not put a card inside a card or a shadow inside a panel.
- Do not draw over the basemap's credits: they are a licence condition.

---
name: Livability Atlas
description: Where should I live? A map of a city scored by your own weights, with every score explained.
colors:
  score-worst: "#B2361E"
  score-poor: "#E07B39"
  score-middling: "#EDC84A"
  score-good: "#83C5A6"
  score-best: "#2A8F94"
  ink: "#171717"
  ink-strong: "#262626"
  control: "#404040"
  ink-quiet: "#525252"
  placeholder: "#737373"
  rule: "#D4D4D4"
  rule-strong: "#A3A3A3"
  paper: "#FFFFFF"
  wash: "#F5F5F5"
  wash-strong: "#E5E5E5"
  note: "#FEF3C6"
  alert: "#C10007"
  land-green: "#E1E8D6"
  land-industry: "#E6E2EC"
  land-railway: "#EAE7E2"
  water: "#D0DDE6"
  cell-excluded: "#BEBEBE"
typography:
  headline:
    fontFamily: "ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.33
  title:
    fontFamily: "ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: 1.5
  body:
    fontFamily: "ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.43
  label:
    fontFamily: "ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 400
    lineHeight: 1.33
  figure:
    fontFamily: "ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.33
    fontFeature: "tnum"
rounded:
  hairline: "2px"
  sm: "4px"
  sheet: "12px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
components:
  panel:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "12px"
    width: "320px"
  quick-look:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "12px"
    width: "208px"
  phone-sheet:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sheet}"
  switch-option:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    padding: "2px 8px"
  switch-option-on:
    backgroundColor: "{colors.ink-strong}"
    textColor: "{colors.paper}"
    typography: "{typography.label}"
    padding: "2px 8px"
  switch-option-hover:
    backgroundColor: "{colors.wash}"
  field:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "4px"
  text-action:
    textColor: "{colors.ink}"
    typography: "{typography.body}"
  note-box:
    backgroundColor: "{colors.note}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "8px"
  factor-tile:
    textColor: "{colors.paper}"
    typography: "{typography.label}"
    padding: "4px"
---

# Design System: Livability Atlas

## Overview

**Creative North Star: "The Field Notebook"**

The app is a researcher's notebook laid over a map. The map of hex cells is the page's subject and takes nearly all of it; the panels are the notes in its margin: plain, practical, written to be used, at a desk while exploring or on a phone while walking an area. A note says what a mark means and where it came from, and then gets out of the way. Every score can be traced, so the notes are full of small, exact words ("Most of London scores 50 to 80", "Few or no homes: no score") and never of slogans.

The panels are quiet and exact. Grey text, thin borders, white paper and system type: nothing in them competes with the map. Colour has two jobs only, and both carry meaning: the score scale (red is worse, yellow middling, blue-green better) on the map, the legend and every bar; and each top-level factor's own colour in the boxes, the rings and the swatches beside the sliders, never beside a score. Detail opens on demand (a quick look on hover, the reasons on click, "About the data" at the foot), so the surface stays the answer and the notebook holds the working.

This is not an estate agent's site: no photographs of houses, no big call-to-action buttons, no sales words. It is not a dashboard either: no grid of cards, headline figures and charts that fight the map for attention.

**Key Characteristics:**
- The map fills the window; the panels float over it at its edges, never beside it in a column of their own.
- One score scale everywhere, and colour used only where it means something.
- System sans-serif type in three sizes, with figures in tabular numerals.
- Actions are underlined words, not buttons; the only filled control is the chosen side of a switch.
- Flat paper, a hairline of shadow to lift a panel off the map, and nothing more.

## Colors

A neutral notebook (white paper, greys, one near-black) around two sets of meaningful colour: the score scale and the factors' own colours.

### Primary
- **Score scale** (`score-worst` Brick Red → `score-poor` Burnt Orange → `score-middling` Mustard → `score-good` Sage Mint → `score-best` Deep Teal): the colour of every score, from 0 to 1, on the hex cells, the legend's ramp and every bar. The good end leans to blue, not pure green, so the ends and the quarters stay apart in the common kinds of colour blindness (every pair of stops at ΔE 12 or more under simulated deuteranopia, protanopia and tritanopia). Scores just either side of the middle look alike to a red-green colour-blind reader, so a bar also shows its score as a length and a number. Cells are drawn at 80% so the land shows through faintly.

### Secondary
- **Factor colours**: each top-level factor takes a colour from the Salt design system's categorical palette (J.P. Morgan, Apache-2.0), step 500 for the factor (white text at 4.5:1 or more) and step 200 for its sub-factors (dark text, `#1C1C1C`). They mark which factor is which in the boxes, the rings and the swatch beside each slider; they are never used for a score, and never sit beside a score bar, where they would read as one (so the reasons show none). The palette lives in `web/src/features/factors/colours.ts`.

### Tertiary
- **Land and water under the cells** (`land-green`, `land-industry`, `land-railway`, `water`): pale, greyed tints of the basemap that show in a cell with few or no homes and on rivers drawn above the cells. Each stays at ΔE 8 or more from every score colour drawn at 80%, so none passes for a score.
- **Left out** (`cell-excluded`, a light grey): a cell that a hard limit leaves out. Light, so that streets and names stay readable through it, and no colour of the score scale.

### Neutral
- **Ink** (`ink`, Tailwind neutral-900): text in fields and the strongest text.
- **Strong ink** (`ink-strong`, neutral-800): the chosen side of a switch, the near-black of the map's outlines and rank markers.
- **Control grey** (`control`, neutral-700): the accent of every slider, check box and radio button.
- **Quiet ink** (`ink-quiet`, neutral-600): help text, notes, values beside a label, credits. The most used text colour after the default.
- **Placeholder** (`placeholder`, `#737373`): placeholders, at 4.7:1 on white (Tailwind's own was 3.9:1, under WCAG AA).
- **Rule** and **strong rule** (`rule` neutral-300, `rule-strong` neutral-400): section dividers and the edges of fields and switches.
- **Paper** (`paper`, white), **wash** (`wash` neutral-100, `wash-strong` neutral-200): panel backgrounds, a switch's hover, a quiet box of facts.
- **Note** (`note`, amber-100): a box that warns, such as a hard limit that leaves out every cell.
- **Alert** (`alert`, red-700; red-800 in small type): an error the user must act on, such as a bundle that failed to load or a postcode that is not found.

### Named Rules
**The Meaning Only Rule.** A colour in this app always means something: a score, a factor, the land, or a warning. Decoration in colour is not allowed; a new colour must name what it means.

**The One Scale Rule.** Every score, anywhere, takes the same red → yellow → blue-green scale (`web/src/features/map/colour.ts`). Never a second scale, and never a factor colour for a score.

## Typography

**Display Font:** none.
**Body Font:** the system sans-serif (`ui-sans-serif, system-ui, sans-serif`, Tailwind's default).

**Character:** the device's own type, so the app reads like a native note and loads nothing. Hierarchy comes from size and weight in small steps, never from a second family.

### Hierarchy
- **Headline** (600, 1.5rem): the app's name in the header, and a cell's score in the reasons panel (`figure`, with tabular numerals).
- **Title** (500, 0.875rem): the name of a section, such as "What matters to you", and a factor's name in a row.
- **Body** (400, 0.875rem): the text of every panel, lists and the quick look. Title and body differ by weight alone.
- **Label** (400, 0.75rem): help under a control, notes, the legend's ends, credits, the text in a factor's box. Usually in quiet ink.

### Named Rules
**The Tabular Figures Rule.** Every number that sits in a column or changes as a slider moves (shares, scores, ranks) uses tabular numerals, so it does not jump.

**The Plain Words Rule.** Labels are plain words a newcomer understands ("Worse", "Better", "Few or no homes: no score"); jargon stays in the code and the docs for contributors.

## Layout

The map takes the whole window under a slim header (the name, 16px by 8px of padding) and above a one-line footer ("About the data"). Everything else floats over the map.

- **Desktop** (768px and wider): the preferences panel at the top left (16px in, 320px wide, at most the window less 2rem, scrolling inside itself), the legend at the bottom left (288px wide), and the reasons panel at the top right (320px wide) on a click. The quick look follows the pointer (208px wide). Panels never grow down over the legend.
- **Phone** (under 768px): the legend sits at the top of the map, and the preferences lie in a sheet along the bottom with rounded top corners and three stops: shut (a 48px handle), half (42% of the map's height, 40% in landscape, scrolled to the sliders so the map stays in view while a weight moves) and full (66%, 50% in landscape), moved between with "More" and "Less". The basemap's credits stay above the sheet's handle, as their licence asks.
- **Spacing:** a 4px step. 4px between a label and its control, 8px between rows, 12px inside a panel and between sections, 16px from the window's edge. Sections inside a panel are divided by a hairline rule with 12px above and below it.

## Elevation & Depth

Flat paper. Panels are white (95% or 90% over the map) with Tailwind's small shadow, just enough to lift them off the coloured cells; the phone's sheet casts a slightly heavier shadow upwards. Nothing else has a shadow, nothing lifts on hover, and nothing inside a panel is raised.

### Shadow Vocabulary
- **Panel** (`box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)`): the preferences, legend, reasons and quick-look panels, and the loading note.
- **Sheet** (`box-shadow: 0 -2px 10px rgba(0,0,0,0.25)`): the phone's bottom sheet, which casts upwards over the map.

### Named Rules
**The Margin Note Rule.** A panel is a note on the map, not a card on a page. One level of lift only: no card inside a card, and no shadow inside a panel.

## Shapes

Small, quiet corners: 4px on panels, fields, switches and quiet boxes; 2px on the colour swatches; 12px only on the phone sheet's top corners. The hex cell is the one strong shape, and it belongs to the map; the panels do not echo it. Edges are hairlines (1px, `rule` or `rule-strong`); the boxes of the factor tree are divided by white 1px lines.

## Components

### Panels
- **Character:** a note pinned to the map's margin.
- **Corner style:** 4px. **Background:** white at 95% (90% for small notes). **Shadow:** the panel shadow. **Padding:** 12px.
- Sections inside a panel are divided by a hairline rule (`rule`), not by boxes.

### Switches
- **Character:** two or three words side by side in a thin frame, the chosen one filled.
- **Shape:** 4px frame in `rule-strong`; label-sized text; 2px by 8px of padding per option.
- **States:** chosen: `ink-strong` fill, white text; not chosen: white, `wash` on hover. Each option is a button with `aria-pressed`.
- Used for "Boxes / Rings", "Score / Rank in London" and "Add up / No weak spots".

### Text actions
- **Character:** an underlined word, as in a notebook.
- Opening a section, resetting, undoing, cancelling and opening a factor (with a "›") are all underlined text in the ink colour. There is no filled primary button; the one bordered button is the full-width "Show the reasons" on a phone, at 44px high for a finger.

### Fields
- **Style:** a white field with a 1px `rule` or `rule-strong` border, 4px corners and 4px of padding; selects keep the browser's own control.
- **Sliders, check boxes and radio buttons:** the browser's own controls, with `control` (neutral-700) as their accent colour from one base rule in `index.css`, never the browser's blue. A slider is full width with its value as a number beside its label, and 32px high on a touch screen.
- **Error:** a line of `alert` text under the field.

### Factor boxes and rings (signature)
- **Character:** the user's weights, drawn as a picture of shares.
- **Boxes:** a short strip, a treemap of 100 by 26 units, so that the sliders come first; each factor a box in its own colour with its name (500, on one line, ending in "…" where it does not fit) and share in label type, white 1px lines between boxes, 4px of padding. A box opens its factor. With one factor counted at a level there is no picture.
- **Rings:** a sunburst of the same shares, the counted sub-factors drawn outside their factor in its tint, a white centre with the level's name.
- Under either, one row per counted factor: a 12px swatch in the factor's colour, the name (underlined with "›" when it opens), the share in tabular numerals, and a slider from 0 to 5.

### Legend (signature)
- **Character:** the key to the map, read in one glance.
- The score ramp, blended through the five stops (in five equal bands when the map shows rank), with a histogram of the cells above it, "Worse" and "Better" under its ends, a one-line summary ("Most of London scores 50 to 80"), and the marks of the map: a numbered circle for a top neighbourhood and an outlined hex for a cell with few or no homes.

### Quick look and reasons
- **Quick look:** on hover, a 208px note beside the pointer with the cell's score out of 100, its rank, its strongest factors (+) and its weakest (−), and "Click for the reasons"; it never takes a click.
- **Reasons:** on click, a panel with the score as a headline figure, the strongest factors (+) and the weakest (−) under it, "The points from each factor add up to …", a bar per factor in the score scale with its length and number (a factor that opens is underlined), and the evidence behind each measure (value, dataset, date, licence) one more click away.

## Do's and Don'ts

### Do:
- **Do** let the map fill the window and float the panels over its edges.
- **Do** colour every score with the one scale in `web/src/features/map/colour.ts`, and show it as a length and a number too.
- **Do** use the factor's own colour only to say which factor a thing belongs to.
- **Do** write labels in plain words, help in label-sized quiet ink, and numbers in tabular numerals.
- **Do** keep text at WCAG AA contrast (4.5:1) or better, placeholders included, and targets on a phone at 44px or more.
- **Do** put detail one step down: hover for a quick look, click for the reasons, "About the data" for the sources.

### Don't:
- **Don't** make it look like an estate agent's site: no photographs of houses, no big call-to-action buttons, no sales words.
- **Don't** add dashboard clutter: no grid of cards, headline figures or charts that compete with the map.
- **Don't** add a colour that means nothing, a second score scale, or a factor colour on a score.
- **Don't** put a card inside a card or a shadow inside a panel.
- **Don't** add a display typeface or a second font family.
- **Don't** draw over the basemap's credits: they are a licence condition.

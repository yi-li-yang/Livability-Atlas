# Product

<!-- impeccable:product-schema 1 -->

The product record that the Impeccable design skill reads (`/impeccable`). The project's own documents stay the authority: [docs/vision.md](docs/vision.md), [docs/interface.md](docs/interface.md), [docs/glossary.md](docs/glossary.md) and [docs/decisions.md](docs/decisions.md). Where this file and those disagree, those win, and this file is corrected.

## Platform

web

## Users

A person who must choose where to live in a city they may not know well, such as someone who moves to London for work or study, a renter who looks for a cheaper area, or a family that buys a home. They want a short list of areas to visit, and they want to know why each area is on it. The repo owner is the first user, but the tool is built for anyone. They use it at a desk to explore, and on a phone to check an area while they are out.

## Product Purpose

Livability Atlas answers one question: **where should I live?** It scores every hex cell of a city (16,668 for London) by the user's own weights and hard limits, in the browser. The map shows the best areas, a ranked list names them, and every score explains itself, one layer at a time. Success: the user leaves with a few areas that fit them, and trusts the reasons.

## Positioning

The score is the user's, not ours: a weighted sum that anyone can inspect, built only from open data, with each measure's evidence (value, dataset, date, licence) one click away. The user's places and preferences never leave their device. No listing site or "best places to live" ranking does all of these.

## Operating Context

- An exploratory loop: move a weight or set a hard limit, look at how the map changes, open a cell to see why, repeat. Sliders must feel immediate.
- The map is the main surface. Panels (the factor tree, the legend, the reasons, the top neighbourhoods) sit around it on a desktop and become bottom sheets on a phone (under 768 px).
- The link carries the preference profile, so people share a profile by sharing the link.

## Capabilities and Constraints

- Progressive disclosure (D17, [docs/interface.md](docs/interface.md)): the answer at the surface, details on demand. Map → quick look on hover → reasons on click → inside a factor → evidence.
- One colour scale for every score: red is worse, yellow middling, blue-green better (`web/src/features/map/colour.ts`). Do not add a second scale for scores.
- A cell with few or no homes has no score (D22) and must show what is there (a park, an airport, industrial land).
- Factors come from the manifest: a new factor needs no change to UI code.
- Words the app shows come only from the glossary's "In the app" part: plain British English, no jargon.
- Community composition is shown as the presence of a group the user chooses, and as diversity, never as "fewer of group X" (D08).
- Static site (GitHub Pages), no server and no account. Basemap from OpenFreeMap, no key.
- Stack: Vite, React 19, TypeScript (strict), Tailwind 4, MapLibre 6 and deck.gl 9.

## Brand Commitments

No logo or brand identity yet. The name is "Livability Atlas". The voice is plain, calm and factual: short sentences, common words, British spelling. The factor tree's colours come from the categorical palette of the Salt design system.

## Evidence on Hand

Real data only: the London data bundle (70 measured indicators across 15 top-level factors) and its QA report. There are no testimonials, user numbers or press. Do not invent any.

## Product Principles

1. The answer first, the evidence one action away.
2. Every number can be traced to an open dataset.
3. The user's preferences decide; the tool never decides for them.
4. Nothing personal leaves the browser.
5. Honest about gaps: no score is better than a wrong score.

## Accessibility & Inclusion

- Colours stay apart in the common kinds of colour blindness; colour is never the only cue (bars also show length and a number, shapes have labels).
- Everything works with a keyboard.
- The ranked list is a full alternative to the map for screen-reader users.
- Works on a phone as well as a desktop.

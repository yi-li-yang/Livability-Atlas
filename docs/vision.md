# Vision

## The question

Choosing where to live is one of the largest decisions a person makes. Yet it is usually made with generic rankings, anecdotes and gut feeling. Livability Atlas treats the question seriously: it combines many kinds of evidence about places and weighs them by each user's own priorities.

The question comes at two scales, and one scoring engine serves both:

1. **Within a city.** Which neighbourhoods suit me best? The map lights up where to look for a home.
2. **Across cities and countries.** Where should I base myself for work, study, a stay abroad or retirement?

The idea as first written is in [conceptualisation.md](conceptualisation.md).

## What it is

Livability Atlas is an open-source decision tool for anyone choosing where to live. It gathers evidence about places, including cost, transport, safety, environment, community and amenities. It then scores each place by the user's own weights and hard limits. The map lights up the best areas, a ranked list names them, and every score comes with its reasons, one layer of detail at a time. It starts with London and is built to grow to more cities, more countries and many users.

## Target users

- People moving within or to a city, whether renting or buying.
- Families weighing schools, safety and green space.
- People relocating abroad for work, study or retirement.
- Remote workers choosing a base.

The project's first user is its developer. Every feature is built for any user.

## Goals

- **G1 Decide (primary).** For London, score every hex cell (a hexagon of about 0.1 km²) by a user's preference profile, rank neighbourhoods, and explain every score.
- **G2 Comprehensive and honest.** Keep a factor catalogue with each dataset's licence and date. Every number on screen traces back to a dataset.
- **G3 Clear.** High-level answers sit at the surface, and every detail is reachable on demand ([interface.md](interface.md)).
- **G4 Extensible.** Adding a factor, a dataset or a region follows a written recipe ([CONTRIBUTING.md](../CONTRIBUTING.md#recipes)) and touches no unrelated code.
- **G5 More places.** Cities and countries are added through dataset tiers and the region recipe, and the same engine compares cities.
- **G6 Path to a product.** Accounts, exact routing, mobile apps and a possible paid edition can come later without a rewrite of the core.

## Principles

- **Transparent.** The livability score is a weighted sum that anyone can inspect. No black-box model decides what is livable.
- **Honest about evidence.** Every number traces to a dataset with its date and licence, and every measured indicator carries an evidence type.
- **Personal.** Users set the weights. Where tastes differ, they also set the direction, the ideal range or the choice. Hard limits remove areas that fail a must-have.
- **Private.** A user's preferences and places stay in their browser.
- **Clear.** The answer comes first, and details open on demand.
- **Open.** The code is AGPL-3.0, and public builds use only openly licensed datasets.

## Not now

Each item is also kept in the [backlog](backlog.md#not-now).

| Item | Revisit when |
| --- | --- |
| Property listings or live market data | A listings partner or open API exists |
| User accounts | Users need their preference profiles on several devices |
| Exact door-to-door routing for a user's own places | A routing service exists (Phase 4) |
| Native mobile apps | The web app works well on phones |
| Within-city maps outside London | Phase 3, once the region recipe is proven |
| Forecasts (prices, gentrification) | Trend data is in place |

## MVP success criteria (end of Phase 1)

1. A user sets weights for about 10 top-level factors in a visual factor tree whose sizes follow the weights. They can also open any factor to adjust its sub-factors, set the direction or ideal range of subjective factors, set hard limits, and add up to 3 places of their own. The map recolours within about 100 ms of a weight change.
2. Hovering over a hex cell shows its neighbourhood, livability score and main strengths and weaknesses. Clicking shows each top-level factor's score contribution. Sub-factors, raw values, datasets, dates and evidence types open only when asked for.
3. The QA report passes all its checks: dataset checks, cross-checks and known-fact assertions ([methodology/validation.md](methodology/validation.md)).
4. `just build london` rebuilds the data bundle from raw downloads and gives the same result every time.
5. A new factor is added by following the factor recipe, with no change to UI code.
6. The London map is public as a static site. It uses only openly licensed data, and no personal data leaves the user's browser.

# Glossary

Every term the project uses, in plain words. Each term keeps one meaning in the code, the docs and the app. When you introduce a term, add it here.

## Map and places

| Term | Meaning | Example |
| --- | --- | --- |
| Within-city scale | Scoring small areas inside one city | Hex cells across London |
| Across-cities scale | Scoring whole cities across countries | London versus Lisbon |
| Hex cell | One hexagon of the map grid: about 0.1 km² and 350 m across. The smallest area the project scores | Greater London has about 15,000 |
| H3 | An open-source system of hexagon grids covering the globe, from Uber | Resolution 9 gives our hex cells |
| Neighbourhood (MSOA) | A named census area of about 8,000 residents, used for names and the ranked list | About 1,000 in London |
| Region | The whole area one build covers | Greater London |
| Buffer zone | A 2 km ring around the region, computed but not shown, so that hex cells at the edge count what lies just outside | |
| Dataset tier | How much of the world a dataset covers: one city, one country, or the globe | PTAL is city tier |
| Comparable across regions | Whether a measured indicator means the same thing in every region | Satellite PM2.5: yes. Crime counts: no |

## Factors and scoring

| Term | Meaning | Example |
| --- | --- | --- |
| Factor tree | Everything a user can weight, arranged from broad to specific | |
| Top-level factor | The first level of the factor tree, with one weight each | Environment |
| Sub-factor | A part of a factor, opened with a dropdown. It can split again | Air quality, then NO₂ |
| Measured indicator | The bottom of the factor tree: one number per hex cell, computed from a dataset | Annual mean NO₂ in µg/m³ |
| Weight | How much a factor matters to the user, from 0 (ignore) to 5 (crucial) | |
| Default weight | The starting weight, set from evidence of what people value. Users change it | |
| Scoring curve | The rule that turns a measured value into a score from 0 to 1 | PM2.5: 5 µg/m³ → 1, 25 µg/m³ → 0 |
| Preference type | Who sets a measured indicator's direction: fixed, user direction, user range or user choice | Rain: user direction |
| Ideal range | A band of values a user likes best. The score falls off on both sides | Summer temperature 20–26 °C |
| Hard limit (filter) | A must-have rule. Hex cells that fail it are greyed out and not ranked | Rent no higher than the user's cap |
| Livability score | The 0–100 result for one hex cell under a preference profile | |
| Score contribution | How many of the 100 points one factor adds for a hex cell | |
| Data coverage | The share of the user's total weight that has data for a hex cell. Below 70% the score is flagged | |
| Confidence label | How directly a measured indicator measures its factor: direct, estimate, proxy, perception or ranking | A venue count is direct |

## Interface

| Term | Meaning | Example |
| --- | --- | --- |
| Progressive disclosure | Showing the high-level answer first, and each layer of detail only when the user asks | Hover, then click, then a dropdown, then "details" |
| Quick look | What hovering over a hex cell shows: name, score, rank, main strengths and weakness | "+ Transport, − Cost" |
| Evidence layer | The deepest layer: raw value, scoring curve, dataset, date, licence, confidence label | |
| Visual factor tree | The factor tree drawn so that each factor's area is its share of the total weight | |
| Treemap, sunburst | Two ways to draw the visual factor tree: nested rectangles, or rings around a centre | |
| Factor explorer | A standalone page that prototypes the visual factor tree on the factor catalogue | `docs/factors/explorer.html` (step 0.2) |

## Users and preferences

| Term | Meaning | Example |
| --- | --- | --- |
| User | Anyone using the app. The first user is the project's developer | |
| Preference profile | Everything a user sets: weights, directions, ranges, choices, hard limits and places. Stored in their browser | |
| A user's places ("my places" in the app) | Up to 3 places a user travels to often. Travel time to them is estimated in the browser | Work, family |
| Default places | Used until a user adds their own places: London's main job centres | Bank, Oxford Circus, Canary Wharf, King's Cross |
| Preset | A ready-made preference profile to start from | Family with children |

## Data

| Term | Meaning | Example |
| --- | --- | --- |
| Dataset | A file or API the project takes data from | Police.uk crime data |
| Factor catalogue | The YAML files that list the factor tree and every dataset | `catalogue/` (step 0.2) |
| Data pipeline | The Python program that downloads datasets and computes measured indicators for every hex cell | `atlas build london` |
| Data bundle | The files the data pipeline publishes for one region. The web app reads only these | `data/published/london/…` |
| Manifest | The index file of a data bundle: factor tree, scoring curves, datasets, dates | `manifest.json` |
| Station travel-time matrix | Public-transport times between every pair of stations in a region, including average waits and changes | `station-matrix.parquet` |
| QA report | The checks run on each build, and their results | `qa.md` |
| Published ranking | An outside list or index of places, used as a supporting sub-factor and for comparison | Sunday Times Best Places to Live |
| Credibility rating | The project's high, medium or low judgement of a published ranking | |
| PTAL | TfL's Public Transport Accessibility Level, from 0 (worst) to 6b (best) | |
| Location quotient | An industry's share of local jobs divided by its share nationally or globally. Above 1, the place specialises in it | Fashion in Milan |
| Market signal | Where large companies choose to open, read as evidence of how they rate an area | Chain brands, shopping centres |
| Brand tag | A label in OpenStreetMap or Overture that links a shop to its company | `brand:wikidata` |

## Process

| Term | Meaning | Example |
| --- | --- | --- |
| Phase | A stage of the roadmap. It ends when its exit criteria are met | Phase 1: London MVP |
| MVP | Minimum viable product: the first version good enough to be useful | |
| Cycle | One goal of work. It ends when the goal's check passes | |
| Spike | A small experiment with throwaway code that answers one question | S4: travel times |
| Walking skeleton | The thinnest version that runs end to end | One factor from download to coloured map |
| Recipe | A written checklist for a repeated job | Add a factor |
| Golden test cases | Fixed examples of input and expected score that both scoring engines must reproduce | |
| Known-fact assertion | An automated test that checks the data against a fact anyone can verify | Heathrow's surroundings have the highest aircraft noise |
| Decision register | The living list of project decisions | `docs/decisions.md` |
| Backlog | The living list of features to add | `docs/backlog.md` |
| AGPL-3.0 | The code licence: open source, and anyone running a modified copy as a web service must publish their changes | |
| CLA | Contributor licence agreement: outside contributors grant rights that keep a paid edition possible | Signed through CLA Assistant |

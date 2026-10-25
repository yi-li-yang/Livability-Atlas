# Glossary

Every term the project uses, in plain words. Each term keeps one meaning and one name in the code, the docs and the app.

The glossary has two parts:

- **[In the app](#in-the-app).** Words the app shows its users, in labels, legends, tooltips and help text. Each must be clear to someone who has never seen the project, so these words carry no jargon.
- **[For contributors](#for-contributors).** Words used only in the docs and the code. Technical terms are fine here, as long as each meaning is written plainly.

When you add a term, put it in the part where it is used. A contributor term that starts to appear in the app moves to "In the app", and gets a plain name first.

## In the app

### Map and places

| Term | Meaning | Example |
| --- | --- | --- |
| Hex cell | One hexagon of the map grid, about 350 m across. The smallest area the app scores | Greater London has about 15,000 |
| Neighbourhood | A named area of about 8,000 residents, used for names on the map and in the ranked list | About 1,000 in London |
| Region | The whole area one map covers | Greater London |
| Within-city scale | Comparing small areas inside one city | Hex cells across London |
| Across-cities scale | Comparing whole cities, across countries | London versus Lisbon |
| Comparable across regions | Whether a measured indicator means the same thing everywhere, so that places in different regions can be compared on it | Satellite PM2.5: yes. Crime counts: no, because countries record crime differently |
| Fare zone | One of the numbered rings that London's public transport fares are priced by, from zone 1 in the centre outwards | Bank is in zone 1 |
| Daytime noise level | The average noise level from 7 am to 11 pm, in decibels (dB) | 55 dB (daytime) from road traffic |
| Band D | The council tax band used to compare councils' charges. A home's own band, from A to H in England, sets its real bill | Band D council tax in Wandsworth |
| Surface water flooding | Flooding when heavy rain cannot drain away, as opposed to flooding from rivers or the sea | A street that floods in a summer storm |
| Food hygiene rating | The rating from 0 to 5 that a council gives a food business for hygiene, from 0 (urgent improvement necessary) to 5 (very good) | A café rated 5 |
| Gigabit broadband | Broadband that can reach a gigabit, 1,000 megabits, per second, over full fibre or cable | 90% of homes can get gigabit broadband |
| Ofsted | The body that inspects schools in England and publishes each inspection's results | A school's latest Ofsted inspection |
| Diversity index | The chance that two residents picked at random belong to different ethnic groups, from 0 (everyone in one group) towards 1 | 0.8: most pairs of residents differ |

### Factors and scores

| Term | Meaning | Example |
| --- | --- | --- |
| Factor | Something that makes a place better or worse to live in, and that the user can weight | Transport, Safety |
| Factor tree | All the factors, from broad to specific. Each factor opens into sub-factors, down to measured indicators | |
| Sub-factor | A part of a factor, opened from it. It can split again | Air quality, inside Environment |
| Measured indicator | The bottom of the factor tree: one number per hex cell, taken from a dataset | Annual mean NO₂ in µg/m³ |
| Weight | How much a factor matters to the user, from 0 (ignore) to 5 (crucial) | |
| Default weight | The starting weight, set from evidence of what people value. Users change it | |
| Share of total weight | How much of the user's total weight one factor carries. Each factor's share splits among its sub-factors by their weights, and the factor tree draws it as area | Weights of 4, 4 and 2 give shares of 40%, 40% and 20% |
| Scoring curve | The rule that turns a measured value into a score from 0 (worst) to 1 (best) | PM2.5: 5 µg/m³ scores 1, and 25 µg/m³ scores 0 |
| Ideal range | A band of values the user likes best. The score falls away on both sides | Summer temperature 20–26 °C |
| Hard limit | A must-have rule, like a search filter. Hex cells that fail it are greyed out and not ranked | Rent no higher than the user's cap |
| Livability score | The 0–100 result for one hex cell, from the user's own weights | |
| Score contribution | How many of the livability score's points one factor adds in a hex cell. The contributions add up to the score | Transport: 32 of 59 points |
| Data coverage | How much of the user's total weight has data in a hex cell. Below 70%, the score is flagged as resting on thin data | |
| Evidence type | What kind of evidence a measured indicator is. Each measured indicator shows one of the five [evidence types](#evidence-types) below | |

### Evidence types

| Term | Meaning | Example |
| --- | --- | --- |
| Direct | It measures the thing itself | Theatres within a 15-minute walk |
| Estimate | It is worked out approximately, for example by a model where data is sparse | Travel time to a user's own places |
| Indirect | It measures something closely related, as a sign of the thing | The variety of cuisines nearby, as a sign of culture |
| Perception | How a place looks or feels to people, judged from photos or written descriptions | Street photos rated for greenery |
| Ranking | It comes from a published ranking | Time Out's neighbourhood lists |

### Preferences

| Term | Meaning | Example |
| --- | --- | --- |
| Preference profile | Everything a user sets: weights, directions, ranges, choices, hard limits and places. It stays in their browser | |
| A user's places ("my places" in the app) | Up to 3 places a user travels to often. Travel times to them are estimated in the browser | Work, family |
| Default places | Used until a user adds their own places: London's main job centres | Bank, Oxford Circus, Canary Wharf, King's Cross |
| Destination | A public place or chain a user chooses, scored by distance to the nearest one. Unlike a user's places, it is not personal | Costco, IKEA, the nearest airport |
| Preset | A ready-made preference profile to start from | Family with children |

### Data and sources

| Term | Meaning | Example |
| --- | --- | --- |
| Dataset | A file or service the project takes data from. Every number in the app names its dataset, with its date and licence | Police.uk crime data |
| Published ranking | A list or index of places published by someone else, used as a supporting factor and for comparison | Sunday Times Best Places to Live |
| Credibility rating | The project's high, medium or low judgement of how far a published ranking can be trusted | |
| Industry specialisation | How many times bigger an industry's share of local jobs is than its share nationally or worldwide. Above 1, the place specialises in that industry. Economists call it the location quotient | Fashion in Milan |
| Brand presence | Which chain brands and shopping centres are near a place. Large companies choose their sites carefully, so where they open shows how they rate an area | Gail's and Waitrose nearby; Westfield within reach |

## For contributors

### Map grid

| Term | Meaning | Example |
| --- | --- | --- |
| H3 | An open-source system of hexagon grids covering the globe, from Uber | Resolution 9 gives the hex cells |
| MSOA | Middle layer Super Output Area: the UK census area used for neighbourhoods. The House of Commons Library publishes readable names for them | About 1,000 in London |
| Output area | The smallest area for which the census publishes results. Output areas group into MSOAs | Census 2021 residents by output area |
| Buffer zone | A 2 km ring around the region, computed but not shown, so that hex cells at the edge count what lies just outside | |
| Dataset tier | How much of the world a dataset covers: one city, one country, or the globe | PTAL is city tier |

### Scoring method

| Term | Meaning | Example |
| --- | --- | --- |
| Top-level factor | The first level of the factor tree, with one weight each | Environment |
| Preference type | Who sets a measured indicator's direction: fixed, user direction, user range or user choice | Rain: user direction |
| Ramp | A scoring curve that runs in a straight line from 0 at one threshold to 1 at another, and stays flat beyond them. It falls when lower values are better | PM2.5: 1 at 5 µg/m³, falling to 0 at 25 µg/m³ |
| Evidence ladder | The kinds of evidence for a factor without a direct measure, from direct counts down to a user's own ratings, each with its evidence type | Culture: venues nearby, then variety, character, activity, perception and rankings |
| Active child | A child factor that counts in a hex cell: its weight is above 0 and it has a score there | |
| Effective share | A factor's share of total weight as it works out in one hex cell. A factor with no data there passes its share to its active siblings | Air quality's 0.1 becomes 0.2 where Noise has no data |

### Interface design

| Term | Meaning | Example |
| --- | --- | --- |
| User | Anyone using the app. The first user is the project's developer | |
| Progressive disclosure | Showing the high-level answer first, and each layer of detail only when the user asks | Hover, then click, then a dropdown, then "details" |
| Quick look | What hovering over a hex cell shows: name, score, rank, main strengths and weakness | "+ Transport, − Cost" |
| Evidence layer | The deepest layer: raw value, scoring curve, dataset, date, licence and evidence type | |
| Visual factor tree | The factor tree drawn so that each factor's area is its share of total weight | |
| Treemap, sunburst | Two ways to draw the visual factor tree: nested rectangles, or rings around a centre | |
| Factor explorer | A standalone page that prototypes the visual factor tree on the factor catalogue | `docs/factors/explorer.html` (step 0.2) |

### Data pipeline

| Term | Meaning | Example |
| --- | --- | --- |
| Factor catalogue | The YAML files that list the factor tree and every dataset | `catalogue/` (step 0.2) |
| Research status | How far a measured indicator has got: idea, researched, spiked (tried in a spike) or built. A factor with sub-factors shows how many of its measured indicators are researched | NO₂ and PM2.5 are researched |
| Public build | A data bundle built for the public site. It uses only datasets whose licences allow redistribution and commercial use (D07). A local build, for its builder's own use, may use any dataset | The London map, once it is public |
| SPDX licence id | The standard short name of a licence, from the SPDX licence list. A licence the list lacks takes an id that starts `LicenseRef-` | `OGL-UK-3.0` for the Open Government Licence v3.0 |
| Data pipeline | The Python program that downloads datasets and computes measured indicators for every hex cell | `atlas build london` |
| Data bundle | The files the data pipeline publishes for one region. The web app reads only these | `data/published/london/…` |
| Manifest | The index file of a data bundle: factor tree, scoring curves, datasets, dates | `manifest.json` |
| Station travel-time matrix | Public-transport times between every pair of stations in a region, including average waits and changes | `station-matrix.parquet` |
| QA report | The checks run on each build, and their results | `qa.md` |
| PTAL | TfL's Public Transport Accessibility Level, from 0 (worst) to 6b (best) | |
| Brand tag | A label in OpenStreetMap or Overture that links a shop to its company | `brand:wikidata` |

### Process

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

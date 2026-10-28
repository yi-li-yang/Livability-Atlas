# Hard-to-measure factors

Status: draft (Phase 0, step 0.2). How the project measures the factors that no dataset measures directly, such as culture, food quality, community life and feeling safe. Terms are defined in the [glossary](../glossary.md).

## The problem

Some of what people value most in a place has no direct measure: a lively culture, good food, a sense of community, feeling safe. Leaving these factors out would tilt the livability score towards what is easy to count. Measuring them carelessly would mislead. This page sets the rules for measuring them honestly, and applies them to each hard factor in the catalogue.

## Rules

1. **Climb the evidence ladder from the top.** Use the most direct evidence that exists. Use a lower rung only when no higher one does, or to add to it.
2. **Label every measured indicator with its evidence type**: direct, estimate, indirect, perception or ranking. The evidence layer shows it beside every number ([interface.md](../interface.md)).
3. **Machine learning may produce measured indicators, never the score.** A model that rates photos or text produces evidence of type perception, and a model that fills gaps in data produces evidence of type estimate ([scoring.md, section 11](scoring.md#11-rules-for-ml)).
4. **Check perception for bias.** A model that rates how safe, lively or attractive a street looks can learn to rate deprived areas or minority communities lower. Before use, its ratings are compared across areas of different deprivation and composition, and it is never used where it would stand in for community composition (D08).
5. **Check against known facts.** Each hard factor gets known-fact assertions, such as the West End having more theatres than an outer suburb ([validation.md](validation.md)).
6. **Watch for counting twice.** Many signals of a "good area" repeat house prices or each other, so they start at low default weights ([scoring.md, section 10](scoring.md#10-counting-twice)).
7. **Respect licences.** Ratings platforms forbid storing their data, so they wait for a licence, and published rankings keep only a listing or a rank with a citation (D07, D19, [rankings.md](../factors/rankings.md)).

## The evidence ladder

From the most direct evidence to the least. Each rung names its evidence type.

| Rung | What it measures | Culture example | Evidence type |
| --- | --- | --- | --- |
| Direct counts | The places themselves, within a walk | Cultural venues within a 15-minute walk: theatres, music venues, galleries, cinemas, libraries (GLA Cultural Infrastructure Map) | direct |
| Access | The same places, within a journey | Cultural venues within 30 minutes by public transport | direct |
| Variety | How many different kinds are near | The number of distinct cuisines nearby | indirect |
| Character | Lasting signs in the built environment | Listed buildings and conservation areas (Historic England) | indirect |
| Activity | What happens there, and how much attention it draws | Event listings; geotagged Wikipedia articles (their page views follow fame, spike S7) | indirect |
| Perception | How a place looks or reads to people, judged by a model | Street-level photos rated for liveliness and beauty; area descriptions tagged by an LLM | perception |
| Published rankings | What others have listed | Time Out's neighbourhood lists, the Sunday Times Best Places to Live | ranking |
| A user's own ratings | What the user has noted | A personal notes layer, stored in the browser | the user's own |

[Spike S7](../spikes/S7-culture-ladder.md) tested the ladder on twelve places, with a known-fact assertion for each rung that open data can test. The direct, variety and character rungs, and the count of geotagged Wikipedia articles, all separate cultural centres from suburbs, and agree with each other. Wikipedia page views do not: they follow how famous a place's landmarks are, so they are dropped. The access rung waits for the station matrix, and the perception, ranking and user's-own rungs were not testable. The test is coarse: it does not show which rung ranks two alike places correctly.

## Culture

Culture climbs the ladder above in full. The direct and access rungs carry it, and the lower rungs add what counts miss: character, activity and how a place feels. Culture is not yet researched in the catalogue; this ladder is its starting point.

## Food quality

No open dataset rates restaurants, so food quality combines open signals (D19):

| Signal | Example | Dataset and licence | Evidence type |
| --- | --- | --- | --- |
| Choice | Restaurants and cafés within a 10-minute walk | OpenStreetMap, Overture Places | direct |
| Variety | The number of distinct cuisines nearby | OpenStreetMap cuisine tags | indirect |
| Your cuisines | Restaurants serving the cuisines a user picks | OpenStreetMap cuisine tags | direct |
| Hygiene | The share of nearby food businesses rated good or very good | Food Standards Agency, open | direct for hygiene, indirect for quality |
| Guide recognition | Michelin stars and Bib Gourmand, the Good Food Guide, The World's 50 Best | Wikidata (CC0) records the Michelin stars of many restaurants, though not all. The guides themselves are proprietary, so keep only counts and a citation | ranking |
| Independents | The share of restaurants that are not chains | OpenStreetMap and Overture brand tags | indirect |
| Ratings and reviews | Average rating and review count | Google, Yelp, Tripadvisor, OpenRice (Hong Kong), Tabelog (Japan), Dianping (China). Their terms forbid storing the data or require a partnership | perception |

Choice, variety and hygiene are researched in the catalogue ([Daily amenities](../specs/2026-10-25-daily-amenities-research.md)). The open rows come first. Each country's ratings platform is a country-tier dataset that needs a licence, and until it has one, ratings stay out of public builds (D07, D19). Spike S8 tests the open signals.

## Brand presence

Where chain brands choose to open shows how large companies rate an area.

| Signal | Measured indicator | Example |
| --- | --- | --- |
| Shopping centres | The size of the shopping centres within reach | Westfield London, Westfield Stratford City |
| Brand variety | Distinct national and international chains within a 15-minute walk | |
| Brand groups | Brands grouped by what their choice of sites signals: premium, high footfall, large catchment, value | Premium: Gail's, Waitrose. High footfall: Pret, Starbucks. Large catchment: Costco, IKEA. Value: Aldi, Lidl |

Brand groups are listed per country. Each brand's group is checked against data before use, for example whether its presence tracks house prices, and brands that show no pattern are dropped. Brand presence partly mirrors house prices, so it starts at a low default weight. Spike S8 checks how complete brand tags are for London.

## Community life

Community life has no direct measure, so its leads sit on the lower rungs:

| Sub-factor | Lead | Evidence type |
| --- | --- | --- |
| Community spaces | Community centres and halls within a walk | direct |
| LGBTQ+-friendly venues | Venues tagged as such in OpenStreetMap | direct, if the tags prove complete |
| Local election turnout | Turnout at local elections, as a sign of civic life | indirect |
| How long residents stay | Census counts of residents who lived elsewhere a year before | indirect |

None is researched yet; the research notes keep the leads.

## Feeling safe

Recorded crime measures crime, which is direct for Safety but only indirect for feeling safe. Feeling safe needs its own evidence: surveys of residents' perceptions are the most direct, if one covers small enough areas under an open licence. Models that rate street photos for safety sit on the perception rung, and are the most exposed to the bias that rule 4 guards against.

## Industry strength, across cities

For the across-cities scale, an industry's strength in a city combines four signals:

- industry specialisation: the industry's share of local jobs, compared with its share worldwide
- its firms and headquarters, from Wikidata
- its flagship institutions and events
- credible rankings of the industry

## What this page does not decide

It sets no default weights, which D14 sets from evidence, and chooses no MVP factors. It sets the rules that any hard factor's research follows.

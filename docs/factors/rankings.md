# Published rankings

Status: assessed in Phase 0, step 0.2 ([roadmap](../roadmap.md)). This page rates each published ranking in the factor catalogue against the credibility rubric. Each rating and its reason also live in [datasets.yaml](../../catalogue/datasets.yaml), where the app reads them.

## The rubric

Each published ranking gets a credibility rating of high, medium or low. The rating weighs six questions:

- Is the method published?
- How much data is behind it?
- Is the publisher independent? An estate agent, for example, is not.
- Is it recent?
- Does it cover our places?
- Does its licence let us store it?

Many rankings are proprietary. For those, the catalogue stores only the rank or the listing and a citation, and keeps them out of public builds unless the licence allows more (D07).

## The assessment

| Ranking | Scale | Method published | Data behind it | Independent | Recent | Covers London | Licence | Credibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| The Sunday Times Best Places to Live | within a city | Criteria, no scoring | Judges' visits, with data on schools, transport and broadband | Yes, but the 2026 edition is sponsored by a mortgage lender | Annual, 2026 | Seven neighbourhoods in 2026 | Proprietary | medium |
| Time Out's Coolest Neighbourhoods in the World | within a city | Broad criteria, no scoring | Editors' judgement | Yes | Annual, 2025 | One or two neighbourhoods a year | Proprietary | low |
| EIU Global Liveability Index | across cities | 30 indicators in five categories | Analysts' ratings and data | Yes | Annual, 2026 | Yes, among 173 cities | Proprietary: sold, with a free summary | high |
| Mercer Quality of Living City Ranking | across cities | In outline | Mercer's surveys | Built to set employers' pay for staff posted abroad | 2024 | Yes, among 241 cities | Proprietary | low |
| Monocle's Quality of Life Survey | across cities | Questionnaire and metrics, no scoring | Correspondents' answers | Yes | Annual, 2026 | Not in the 2026 top 20 | Proprietary | low |
| OECD Better Life Index | across cities | In full | Rich and official | Yes, intergovernmental | Editions since 2011 | As a large region, Greater London | Not confirmed | high |

**Why each rating.**

- **The Sunday Times, medium.** It publishes its criteria, such as schools, transport, broadband, green space and the high street, and its judges visit every place. But it publishes no scoring, and Lloyds Banking Group sponsors the 2026 edition.
- **Time Out, low.** Its writers and editors nominate and rank the places on culture, nightlife and a sense of newness, with no data behind the order. Its criteria favour going out over everyday living.
- **The EIU, high.** It publishes its 30 indicators and five categories, is independent of property interests, and covers London every year.
- **Mercer, low.** It describes its method only in outline, and builds the ranking to help employers set pay and hardship allowances for staff posted abroad. The cities it covers follow its clients' demand.
- **Monocle, low.** Its editors choose the top 20 from correspondents' answers, with no published scoring.
- **The OECD, high.** It publishes its method and data on 11 topics, and leaves their weighting to the user. It covers countries and large regions, not cities or neighbourhoods.

## How the catalogue uses them

- **A supporting factor.** Published rankings partly repeat the other factors, so the factor starts at a default weight of 1 (D14).
- **Within a city, a listing.** The Sunday Times and Time Out are measured indicators of evidence type ranking. A hex cell inside a neighbourhood that the latest edition names scores 1, and any other 0. The catalogue's checks require a credibility rating on every dataset that a ranking indicator uses.
- **Across cities, ranks.** The EIU, Mercer, Monocle and the OECD stay as ideas until Phase 3, with their datasets already recorded.
- **Storage.** Only names or ranks and a citation are stored, and every ranking stays out of public builds. The OECD's could join once its data terms are confirmed: its open-by-default policy puts content published since 1 July 2024 under CC BY 4.0, but its site refused automated access when this was checked.

## What the assessment found

- Only the EIU and the OECD rate high, and both work across cities, not within London.
- Within London, the rankings say little: the Sunday Times names seven neighbourhoods in 2026, and Time Out one or two. A listing is a small signal, which the factor's low weight reflects.

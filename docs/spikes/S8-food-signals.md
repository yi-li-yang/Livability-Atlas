# S8: the open food signals, and brand groups

Status: done for the signals that open data can test. A spike of step 0.4 ([roadmap](../roadmap.md#spikes)). Its code is [pipeline/notebooks/s8_food_signals.py](../../pipeline/notebooks/s8_food_signals.py), throwaway and never imported by `atlas`.

## Question

Do the food signals (hygiene ratings, Michelin in Wikidata, cuisine variety, the independents' share) work for London? Do the brand groups track house prices?

## Answer

| Signal | Works for London? |
| --- | --- |
| Hygiene ratings | **Yes.** Almost every homes cell has enough rated businesses, and the share varies. |
| Cuisine variety | **Yes,** from Overture's categories first, then OpenStreetMap's tags. |
| Independents' share | **Partly.** A noisy but usable indirect signal. |
| Michelin in Wikidata | **No.** It misses known starred restaurants, so counts would understate. |
| Brand groups against prices | **Premium and value brands show a pattern; high-footfall brands weakly; large-catchment brands none.** |

## What was done

1. **Hygiene.** Took the 60,726 food businesses on the FSA's register that hold a rating from 0 to 5 (3,909 more await inspection), and for each of 11,182 homes cells, the share within 800 m rated 4 or 5, in cells with 10 or more rated businesses.
2. **Cuisine variety.** Counted the distinct cuisines among the restaurants within 800 m of each homes cell, twice: from OpenStreetMap's `cuisine` tags and from Overture's categories (such as `indian_restaurant`). Checked five known places.
3. **Michelin.** Ran a query on Wikidata for London items with an award whose label contains "Michelin", and looked for four restaurants known to hold stars.
4. **Independents.** Took the 59 names that 20 or more FSA eating places share as chains, and computed each cell's chain share from the FSA's names, and again from the brand tags on OpenStreetMap's and Overture's eating places. The signal is one minus the second, so the comparison asks whether tags rank cells as the names do.
5. **Brand groups.** For the brands of each group the research notes name, found the places that carry the brand in their name or brand tag (as whole words), recorded whether each homes cell has one within 1.2 km, and compared presence with the median sale price among the sales of the cell and its neighbours within two steps over 24 months, from [S3](S3-sales-and-rents.md).

## Findings

**Hygiene.** 85% of rated businesses are rated 4 or 5, and 67% are rated 5, so the signal lives in the lower tail. 98% of homes cells have 10 or more rated businesses within 800 m. The share within 800 m has a median of 87% and runs from 69% (5th percentile) to 97% (95th), and 6% of cells are under 70%.

**Cuisine variety.**

| | OpenStreetMap | Overture |
| --- | --- | --- |
| Restaurants in London | 9,140 | 32,922 |
| With a cuisine | 73% (a tag) | 77% (a specific category) |
| Distinct cuisines | 264 (raw tag values) | 148 (categories) |
| Cuisines within 800 m of a home, 5th, 50th, 95th percentile | 0, 4, 27 | 2, 12, 41 |
| Homes cells with no cuisine found | 18% | 1.3% |

The two rank homes cells alike (rank correlation 0.84). Cuisines within 800 m at known places, OpenStreetMap and Overture: Soho 88 and 89, Brick Lane 54 and 74, Orpington 22 and 18, Edgware 12 and 24, Chigwell 0 and 4. Both put the two centres first and Chigwell last. Overture has three and a half times the restaurants, so its variety is higher, and OpenStreetMap's tags need tidying: 264 raw values include variant spellings and regional descriptions.

**Michelin in Wikidata.** The query found 27 London items with a Michelin star. Of four restaurants looked for, Gordon Ramsay, Core by Clare Smyth and Dinner by Heston are there, and The Clove Club is not found. So the records are incomplete, and a count of starred restaurants near a cell would understate. The guides themselves are proprietary, as the methodology says.

**Independents.** 8.6% of the FSA's eating places have a chain name, and 13% of OpenStreetMap's and Overture's eating places carry a brand tag (the tags may cover more chains than the 59 names). The median cell's chain share is 7% by the FSA's names and 10% by tags. The two rank homes cells alike with a rank correlation of 0.71: fair, and noisy.

**Brand groups against sale prices** (rank correlation of presence within 1.2 km with the median price nearby; the share of homes cells that have one):

| Group | Brand | Places | Cells with one | Correlation with price |
| --- | --- | --- | --- | --- |
| Premium | Waitrose | 292 | 29% | +0.39 |
| | Gail's | 242 | 27% | +0.43 |
| | **Either** | | 39% | **+0.44** |
| High footfall | Pret A Manger | 630 | 31% | +0.21 |
| | Starbucks | 586 | 47% | +0.19 |
| | Either | | 52% | +0.19 |
| Value | Aldi | 147 | 24% | −0.02 |
| | Lidl | 283 | 41% | −0.22 |
| | **Either** | | 55% | **−0.19** |
| Large catchment | Costco | 16 | 2% | −0.05 |
| | IKEA | 27 | 5% | +0.06 |
| | Either | | 7% | +0.03 |

Premium brands track prices moderately, as the methodology expected ("brand presence partly mirrors house prices"). Lidl runs against prices, and Aldi does not follow it. Large-catchment stores are too few to tell: they are within reach of 7% of homes. A first pass that matched brand names as any part of a word counted 222 Aldi places, many of them false matches (a name like Rinaldi), where whole words give 147.

## Decisions

1. **Hygiene:** the measured indicator works as researched, and moves to `spiked`.
2. **Cuisine variety:** Overture's categories first and OpenStreetMap's tags to fill gaps. A percentile curve, because no standard says how many cuisines are enough. It moves to `spiked`. Your cuisines follows the same sources.
3. **Guide recognition stays an idea.** Wikidata is too incomplete to count from.
4. **Independents stay an idea,** a candidate for Phase 2, as an indirect signal with a low default weight. A chain list per country is the work it needs.
5. **Brand groups:** the premium and value groups show a pattern, so they can go on, at a low default weight. Drop Aldi, Costco and IKEA, whose presence shows none, as the methodology's rule says. A premium brand in reach also means a dearer area, so the group must not double count with housing cost.

## What was not tested

- **How good the food is.** Hygiene is not quality, and no open signal here measures quality.
- **Ratings platforms** (Google, Yelp, Tripadvisor and country platforms): licences forbid storing them.
- **Whether the four brands per group are representative,** and brands outside London.
- **Michelin completeness beyond four restaurants,** and the Bib Gourmand or other guides.
- **Cuisine labels' accuracy,** only their presence.

## Reproduce

From `pipeline/`, with the data that S1 to S3 and S6 need (S6's fetch adds the FSA ratings):

```sh
uv run python notebooks/s8_food_signals.py
```

It queries Wikidata once, and takes a few minutes.

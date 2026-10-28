# S3: sales, prices per m² and rents

Status: **partly done.** A spike of step 0.4 ([roadmap](../roadmap.md#spikes)). Its code is [pipeline/notebooks/s3_sales_and_rents.py](../../pipeline/notebooks/s3_sales_and_rents.py), throwaway and never imported by `atlas`. The sales and rent questions are answered. The price per m² is not: it needs data that only the owner can fetch.

## Question

How many hex cells have enough sales for a price per m² (Land Registry with EPC floor areas)? What is the finest open rent data for London, and is a model of rent from sale prices credible?

## Answer

- **Enough sales: yes, if each cell pools its neighbours and two years.** With a cell and its neighbours within two steps over 24 months, 99% of London's homes cells have 20 or more sales and 95% have 40 or more. A cell alone has 5 or more sales in a year in only 37% of cases.
- **Price per m²: open.** It needs the energy certificates' floor areas. They need a GOV.UK One Login to download in bulk, and matching them to sales by address waits on Royal Mail's answer, which is already one of the owner's checks in [progress.md](../progress.md).
- **Finest open rent data: postcode districts,** from the ONS's ad hoc releases of the private rental market in London, with counts and quartiles by number of bedrooms. The catalogue had said that nothing finer than the borough was open.
- **A model of rent from sale prices: not worth it.** It predicts a district's rent to within 7%, against 8% for using its borough's average.

## What was done

1. Read 150,243 London residential sales from October 2024 to September 2026 (HM Land Registry's Price Paid Data, standard sales only), and placed each by its postcode's coordinates from OS Code-Point Open, in H3 resolution 9 cells.
2. Counted sales per cell for 12 and 24 months, alone and pooled over one and two steps, among the 13,699 cells with 50 or more residents (residents from spike S2's allocation).
3. Measured how spread out prices are inside a cell, and from that how many sales a median needs.
4. Downloaded the ONS's London rents by postcode district (April 2025 to March 2026). For 168 districts with one-bedroom rents and 186 with two-bedroom rents, backed by 30 or more rents each, compared three ways of estimating a district's median rent against the ONS's figure, leaving each district out in turn.

## Findings

**Sales per homes cell.**

| Pooled over | 12 months, 5+ sales | 12 months, 20+ | 24 months, 20+ | 24 months, 40+ |
| --- | --- | --- | --- | --- |
| The cell alone | 37% | 1.5% | 17% | 3% |
| One step (7 cells) | 93% | 63% | 88% | 71% |
| Two steps (19 cells) | 99% | 94% | 99% | 95% |

**How many sales a median needs.** The prices of homes sold in one cell vary by about 37% (the spread of the logarithm of price, in cells with at least 10 sales), because houses and flats mix. For a median within 10%, 15% or 20% with 95% confidence, a cell needs about 82, 37 or 21 sales. A price per m² separates flats from houses, so it should need fewer sales. That is untested.

**Rents.** The ONS's release covers 247 postcode districts with the count, mean, lower quartile, median and upper quartile of rents, by bedroom count, under the Open Government Licence v3.0. Its notes limit its use: counts are rounded to 10 and small cells suppressed, Housing Benefit claimants are not in the sample, and the sample is purposive, so the ONS says the statistics "should not be compared across time periods or between areas".

**Models of a district's median rent, mean error against the ONS's figure.**

| Model | One bedroom | Two bedrooms |
| --- | --- | --- |
| A constant yield (rent as a fixed share of the median flat price) | 17% | 14% |
| The average of the district's borough | 8% | 8% |
| Log rent on log median flat price, across London | 8% | 8% |
| The borough's average, plus price differences within the borough | 7% | 7% |

Sale prices explain 82% of the variation in rents across districts, but only because both rise towards the centre. Inside a borough they add one point of accuracy. A constant yield is poor: the gross yields of the middle 80% of districts run from 3.7% to 5.9% for one bedroom, and from 4.8% to 7.4% for two. There is no rent data below the district to check a per-cell model against.

**Code-Point Open.** The pack's own licence file says "Your use of data is subject to terms at www.ordnancesurvey.co.uk/opendata/licence", and asks for three acknowledgements: Ordnance Survey data, Royal Mail data and National Statistics data, each "© Crown copyright and database right" with the year. The licence page answered 503 when it was read, so whether public builds may use it is still open. It is the second candidate, after the ONS Postcode Directory, for placing NHS practices from their postcodes in the [Health care research](../specs/2026-10-28-health-care-research.md).

## Decisions

1. **Pool two steps and 24 months for any price.** That gives 20 or more sales almost everywhere, and 40 or more in 95% of homes cells. The catalogue's buying cost method now says so.
2. **Keep renting cost at the borough,** from the ONS's price statistics. The postcode-district rents join the catalogue as a dataset (`ons-london-rents-by-district`), listed second, and stay out of the score because of the ONS's own caution.
3. **Do not model rents per cell from sale prices.** It adds about one point of accuracy over the borough's average, and cannot be checked below the district.
4. **Leave the price per m² open until the certificates are in hand,** and buying cost stays out of public builds until Royal Mail answers (D07).

## What the owner can do

- Sign in with a GOV.UK One Login, and download the domestic energy performance certificates from the [energy performance data service](https://get-energy-performance-data.communities.gov.uk/), which offers them as CSV for England and Wales. The spike can then measure floor areas and match them to sales in a private build, to see how many cells keep a price per m² and how much it narrows the spread.
- Ask Royal Mail the existing question about matching Price Paid Data to energy certificates by address.

## What it means for other spikes

- **S5 and S6** can reuse the postcode-to-cell lookup and the pooling code. The whole script runs in about 15 seconds on 3 years of sales.
- **Downloads in `data/raw/`:** Price Paid (415 MB for 2024 to 2026), Code-Point Open (14 MB), and the ONS rents (130 kB). All are free, with no key.

## Reproduce

From `pipeline/`, with the three downloads in `data/raw/` and spike S2's data:

```sh
uv run python notebooks/s3_sales_and_rents.py
```

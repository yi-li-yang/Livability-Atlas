# Housing and cost research

Status: built. The fourth MVP factor researched in Phase 0, step 0.2 ([roadmap](../roadmap.md)), with the `/research-factor` recipe.

## Scope

- **Researched:** buying cost, renting cost and council tax, the Housing and cost row of the MVP candidates in the [research notes](../factors/research-notes.md).
- **Left as an idea:** home energy efficiency, outside the MVP row, with a lead in the research notes. Rent and price levels, purchasing power and tax burden apply across cities, which waits for Phase 3.

## Measured indicators

| Measured indicator | Unit | Resolution | Datasets |
| --- | --- | --- | --- |
| Buying cost | £ per m² | sales in and around the hex cell | Price Paid Data, energy performance certificates |
| Renting cost | £ a month | borough | ONS Price Index of Private Rents |
| Council tax | £ a year (Band D) | borough | MHCLG council tax levels |

All three share one design:

- **Scoring curve:** the percentile fallback, lower is better. No standard sets a fair price, and prices differ between regions and currencies, so a hex cell scores by its rank within the region. A user's budget belongs in a hard limit, not in the curve. A YAML anchor shares this reason between the three.
- **Evidence type:** direct, and not comparable across regions.

Renting cost and council tax have one value per borough, so every hex cell in a borough shares it. No finer open rent data covers London: the Mayor's London Rents Map uses the same ONS series, at borough level.

## Datasets

| Dataset | Tier | Licence | Public builds |
| --- | --- | --- | --- |
| Price Paid Data, from HM Land Registry | country | Open Government Licence v3.0, but not for the addresses | no |
| Energy performance certificates for homes, from MHCLG | country | Open Government Licence v3.0, except the address fields | yes, located by UPRN |
| Price Index of Private Rents, from the ONS | country | Open Government Licence v3.0 | yes |
| Council Tax levels set by local authorities in England, from MHCLG | country | Open Government Licence | yes |

**The address data.** Both Price Paid Data and the energy certificates carry addresses processed against Ordnance Survey's AddressBase Premium, which includes Royal Mail's PAF. The Open Government Licence does not cover them:

- Price Paid Data's addresses, postcodes included, may be used only for personal or non-commercial use, or to display residential property price information. Other uses need Royal Mail's permission.
- The certificates' addresses may be used only for purposes tied to the energy performance of buildings. Every other field, UPRNs included, is open.

Buying cost needs each sale's floor area, which means matching sales to certificates, and Price Paid Data has no UPRN. Until Royal Mail confirms that the match is allowed, or Land Registry's UPRN look-up table proves usable under its own licence, Price Paid Data stays out of public builds. The certificates can go in, located by UPRN rather than by address.

## Decisions to review

1. **Percentile scores for all three**, with budgets as hard limits.
2. **Borough values for rent and council tax**, the finest open data.
3. **Rent for all homes**, before the user's home size is taken into account.
4. **Price Paid Data kept out of public builds** until the address question is answered.

## Findings for the spikes

- **S3.** How to match sales to certificates within the licences' terms, through Land Registry's UPRN look-up or with Royal Mail's permission; how many years and how wide an area to pool for a price per m²; and whether a model of rent from sale prices is credible at hex level.

## Testing

- Both catalogue files pass every check, and the explorer's 44 tests pass.
- The browser check passes.

## Done when

- The checks pass, the Artifact is published again, and the pull request is merged.

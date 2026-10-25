# Digital connectivity research

Status: built. The seventh MVP factor researched in Phase 0, step 0.2 ([roadmap](../roadmap.md)), with the `/research-factor` recipe.

## Scope

- **Researched:** broadband and 5G coverage, the Digital connectivity row of the MVP candidates in the [research notes](../factors/research-notes.md), which asked for the resolution of Ofcom's data to be checked.
- **Left as ideas:** broadband speed and internet freedom, which apply across cities and wait for Phase 3.

## What the resolution check found

Ofcom's Connected Nations 2025 data, a snapshot from July 2025, is open under the Open Government Licence. Its resolution differs by kind:

- **Fixed broadband** comes down to census output areas and postcodes, but only for gigabit-capable coverage and slower speed bands. Ofcom does not publish full-fibre coverage below local authorities, because providers keep it confidential.
- **Mobile coverage** comes only by local authority and constituency, built from 100 m pixels that are not themselves published.

## Changes to the factor tree

**Full-fibre availability** becomes **Gigabit broadband**, which Ofcom reports for small areas. Gigabit-capable coverage includes full fibre and cable, and it is the capability users care about.

## Measured indicators

| Measured indicator | Unit | Resolution | Scoring curve | Evidence type | Dataset |
| --- | --- | --- | --- | --- | --- |
| Gigabit broadband | % of homes | output area | Ramp: the share of homes | direct | Ofcom fixed coverage, with ONS output area boundaries |
| 5G coverage | % of premises | borough | Ramp: the share of premises | estimate | Ofcom mobile coverage |

**5G from every network.** In every London borough, Ofcom's data puts outdoor 5G from at least one network at about 100% of premises, which separates no places. Coverage from all four networks ranges from 61% of premises in Kingston upon Thames to 100% in several central boroughs. The measured indicator is therefore coverage from all four networks: whichever network a user is on, it works. The coverage is modelled by the networks, so the evidence type is estimate, and Ofcom's signal thresholds are its own, so it does not compare across regions.

## Datasets

| Dataset | Tier | Licence | Public builds |
| --- | --- | --- | --- |
| Connected Nations 2025: fixed broadband coverage, from Ofcom | country | Open Government Licence | yes |
| Connected Nations 2025: mobile coverage, from Ofcom | country | Open Government Licence | yes |
| Output Areas (December 2021) Boundaries, from the ONS | country | Open Government Licence v3.0 | yes |

The output area boundaries turn values for output areas into values for hex cells. Their data.gov.uk record leaves the licence unset, but the ONS supplies its digital boundary products under the Open Government Licence v3.0, with credits to the ONS and Ordnance Survey. The five crime measured indicators, which use residents by output area, now list the boundaries too.

## Decisions to review

1. **Gigabit broadband instead of full fibre**, since full fibre is not public for small areas.
2. **5G from all four networks**, the only measure that separates London's boroughs.
3. **One 5G value per borough**, the finest open data.

## Testing

- Both catalogue files pass every check, and the explorer's 45 tests pass.
- The browser check passes.

## Done when

- The checks pass, the Artifact is published again, and the pull request is merged.

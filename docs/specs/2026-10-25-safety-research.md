# Safety research

Status: built. The third MVP factor researched in Phase 0, step 0.2 ([roadmap](../roadmap.md)), with the `/research-factor` recipe.

## Scope

- **Researched:** crime, as five measured indicators, one for each kind of crime that bears on residents. That is the Safety row of the MVP candidates in the [research notes](../factors/research-notes.md).
- **Left as an idea:** road collisions, outside the MVP row, with a lead in the research notes. Homicide rate and political stability apply across cities, which waits for Phase 3.

## Changes to the factor tree

**Crime by category** becomes **Crime**, a factor with five measured indicators, so that users can weight the kinds of crime they care about. Police.uk sorts crime into 14 categories, of which these five bear most directly on where people live:

| Measured indicator | Police.uk categories |
| --- | --- |
| Burglary | Burglary |
| Violence and sexual offences | Violence and sexual offences |
| Robbery and theft from the person | Robbery; theft from the person, such as pickpocketing |
| Vehicle crime | Vehicle crime |
| Anti-social behaviour | Anti-social behaviour |

The other categories are left out. Shoplifting falls on shops rather than residents. Drug and weapons offences reflect police activity as much as crime. Bicycle theft, criminal damage, public order, other theft and other crime can join later if users ask.

## Measured indicators

All five share one design:

- **Unit:** crimes, or incidents for anti-social behaviour, a year per 1,000 residents. D08 asks for crime as rates, with notes on reporting.
- **Scoring curve:** the percentile fallback, lower is better. No standard sets a safe level of crime, and countries record crime differently, so a hex cell scores by its rank within the region. For the same reason they are not comparable across regions.
- **Evidence type:** direct. They are recorded crimes, with the caveat in each method that not every crime is reported.
- **Method:** the last 12 months of Police.uk's records, counted at their anonymised map points, per 1,000 residents from Census 2021, smoothed over neighbouring hex cells.

Two YAML anchors share the curve's reason and the method between the measured indicators, so each text exists once. Anti-social behaviour has its own method, because its records are incidents, not crimes.

## Datasets

| Dataset | Tier | Licence | Public builds |
| --- | --- | --- | --- |
| Police recorded crime and anti-social behaviour, from data.police.uk | country | Open Government Licence v3.0 | yes |
| Census 2021, usual residents by output area (TS001), from the ONS through Nomis | country | Open Government Licence | yes |

Police.uk covers England, Wales and Northern Ireland, monthly, for the latest three years. It moves each crime to the nearest of a list of anonymous map points, each over a street, a public place or commercial premises. Nomis publishes census data under the Open Government Licence without naming a version, and asks for the credit "Source: Office for National Statistics".

## Decisions to review

1. **Five kinds of crime**, and the categories left out.
2. **Rates per resident**, as D08 asks, which overstate crime where few people live but many visit, such as central London. Spike S2 compares them with rates per area.
3. **Percentile scores**, the fallback in the scoring method, because no threshold exists.

## Findings for the spikes

- **S2.** The smoothing of rates over neighbouring hex cells; rates per resident against rates per area; and Police.uk's caveats: forces' geocoding accuracy ranges from 60% to 97%, and six forces may count some anti-social behaviour twice.

## Testing

- Both catalogue files pass every check, and the explorer's 44 tests pass.
- The browser check passes, which confirms that the page reads the YAML anchors.

## Done when

- The checks pass, the Artifact is published again, and the pull request is merged.

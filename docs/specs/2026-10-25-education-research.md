# Education research

Status: built. The eighth MVP factor researched in Phase 0, step 0.2 ([roadmap](../roadmap.md)), with the `/research-factor` recipe.

## Scope

- **Researched:** nearby schools by phase, and their inspection results, the Education row of the MVP candidates in the [research notes](../factors/research-notes.md).
- **Left as ideas:** nurseries and school league tables, outside the MVP row, with leads in the research notes. School quality, international schools and universities apply across cities, which waits for Phase 3.

## Changes to the factor tree

**Schools by phase and inspection outcome** becomes **Schools**, a factor with three measured indicators: primary schools, secondary schools and school inspection results. Families weight the phase their children need, and the inspections apart from the walk.

## Measured indicators

| Measured indicator | Unit | Scoring curve | Evidence type | Datasets |
| --- | --- | --- | --- | --- |
| Primary schools | minutes on foot | Ramp: 1 within 6 minutes, 0 at 25 minutes | direct | DfE's register of schools, OpenStreetMap |
| Secondary schools | minutes on foot | Ramp: 1 within 6 minutes, 0 at 25 minutes | direct | DfE's register of schools, OpenStreetMap |
| School inspection results | % of nearby schools | Waits for a definition | direct | Ofsted's inspection records, DfE's register of schools |

**The walk.** CIHT's guidelines (2000, Table 3.2) group school trips with commuting: 500 m desirable and 2,000 m the preferred maximum, about 6 and 25 minutes at 4.8 km/h. Each method notes that admission follows each school's own criteria, so the nearest school is not always one a child can attend.

**Inspection results.** This is the "new definition of rating" that the research notes asked for. Ofsted's renewed framework, in force since 10 November 2025, gives each school a report card: up to eight evaluation areas graded on a five-point scale, from urgent improvement through needs attention, expected standard and strong standard to exceptional, with safeguarding met or not met. Ofsted says these grades do not compare directly with the earlier ones, and most schools' latest inspection still predates the report cards. The measured indicator is the share of state schools within a 2,000 m walk that meet the standard, and its curve waits for the definition of meeting it. One candidate is the expected standard or better in every graded area, matched with good or better under the earlier framework, decided once report cards cover more schools.

## Datasets

| Dataset | Tier | Licence | Public builds |
| --- | --- | --- | --- |
| Get Information About Schools, from the Department for Education | country | Open Government Licence v3.0 | yes |
| State-funded school inspections and outcomes: management information, from Ofsted | country | Open Government Licence v3.0 | yes |

The register is updated daily, and Ofsted's records monthly, with one row for each school's latest inspection; the latest is as at 30 September 2026.

## Decisions to review

1. **Primary and secondary apart**, so that families can weight each.
2. **CIHT's school walking distances.**
3. **Inspection results wait for a definition** that spans Ofsted's frameworks.

## Testing

- Both catalogue files pass every check, and the explorer's 45 tests pass.
- The browser check passes.

## Done when

- The checks pass, the Artifact is published again, and the pull request is merged.

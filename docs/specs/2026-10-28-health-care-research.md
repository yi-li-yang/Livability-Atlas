# Health care research

Status: built. The tenth MVP factor researched in Phase 0, step 0.2 ([roadmap](../roadmap.md)), with the `/research-factor` recipe. [D21](../decisions.md#d21-mvp-factor-set) added it to the MVP.

## Scope

- **Researched:** access to GP practices (how near one is, and how many patients each GP serves) and the distance to the nearest A&E.
- **Left as ideas:** dentists and health-care quality and cost. The [research notes](../factors/research-notes.md) keep their leads, and the reasons are below. Health-care quality and cost applies across cities, which waits for Phase 3.

## Changes to the factor tree

**GP access and list size** becomes **GP access**, a factor with two measured indicators: the walk to a GP practice, and patients per GP. They measure different things, in different units: how near a practice is, and how stretched it is. **A&E travel time** becomes **Distance to A&E**, because the only evidence found is in straight-line kilometres. A travel time would need routing, and the evidence would not support it.

## Measured indicators

| Measured indicator | Unit | Scoring curve | Evidence type | Datasets |
| --- | --- | --- | --- | --- |
| Walk to a GP practice | minutes on foot | Ramp: 1 within 5 minutes, 0 at 15 minutes | direct | NHS England's ODS with the ONS postcode directory, or OpenStreetMap |
| Patients per GP | patients per full-time GP | Waits for the zero end | indirect | NHS England's registered patients, GP workforce and ODS |
| Distance to A&E | km in a straight line | Waits for the spread of distances | direct | OpenStreetMap, cross-checked with ODS |

**The walk.** The same curve as pharmacies and groceries: CIHT's guidelines (2000, Table 3.2) give 400 m desirable and 1,200 m preferred maximum for trips other than commuting, about 5 and 15 minutes at 4.8 km/h. No NHS source sets a walking standard for GP practices. The searches found research (about 85% of people in England live within a 20-minute walk of a practice, from a Durham University study) and local planning documents, but no standard.

**Patients per GP.** For each cell, the registered patients of the GP practices within a 15-minute walk, divided by their full-time, fully qualified GPs, trainees excluded. The Healthy Urban Development Unit's planning model plans for one GP per 1,800 patients, so 1,800 is where the score would start to fall. The searches reached that figure through Camden Council's health assessments, which quote it, and not through the model itself, which is on the London Datastore. No source says where access becomes poor, so the zero end waits for how the measure spreads across London's cells. The Oxford study *Counting general practitioners* (data from 2015 to 2024) gives the national spread: the 5th to 95th percentile ran from 1,357 to 5,559 patients per fully qualified full-time GP. The measure is **indirect**: a high ratio shows that an appointment is likely to be harder to get, and does not count appointments.

**Distance to A&E.** Nicholl and colleagues (*Emergency Medicine Journal*, 2007, volume 24, pages 665 to 668) followed 10,315 emergency patients taken to hospital by four English ambulance services, and found that each extra 10 km of straight-line distance went with about a 1% higher absolute risk of death, with no threshold. Its data are from 1997 to 2001, and the Patients Association has criticised the design. A ramp needs a distance at which the score is 0, and none has a source, so the curve waits for the distances in the built data. The departments counted are type 1: consultant-led, open 24 hours, with full resuscitation facilities, as NHS England's A&E definitions describe them.

**Comparing regions.** Only the A&E distance compares across regions. The two GP measures use NHS England's registers, which cover England only, where Scotland, Wales and Northern Ireland keep their own. The A&E distance uses OpenStreetMap, which is global.

## Datasets

| Dataset | Tier | Licence | Public builds |
| --- | --- | --- | --- |
| NHS England Organisation Data Service (ODS): GP practices, trust sites, dental practices | country | Open Government Licence v3.0 | yes |
| Patients Registered at a GP Practice, from NHS England | country | Open Government Licence v3.0 | yes |
| General Practice Workforce, from NHS England | country | Open Government Licence v3.0 | yes |
| ONS Postcode Directory | country | not confirmed | **no** |
| OpenStreetMap, already in the catalogue | global | ODbL 1.0 | yes |

**NHS England's licence.** The three NHS England datasets carry no licence on their own pages. NHS England's terms and conditions release its content under the Open Government Licence, except third-party information marked as such and a list of exclusions (logos, information standards, software). Nothing on the three pages is marked otherwise. The attribution those terms ask for is "Contains information from NHS England, licenced under the current version of the Open Government Licence."

**The postcode directory.** The ODS gives each practice's postcode and no coordinates. The ONS's page on licences says its postcode products are under the Open Government Licence and may be re-used commercially, with attribution lines for the Ordnance Survey and for Royal Mail. It does not name the directory, and it does not give Royal Mail's own terms. The Ordnance Survey's pages for Code-Point Open, the product the ONS says its postcode products derive from, state no licence either. So the directory stays out of public builds until its own page on the Open Geography Portal states a licence. Until then a public build measures the walk to a GP practice from OpenStreetMap's mapped doctors' surgeries, and cannot measure patients per GP, which needs the practices' postcodes. Northern Ireland postcodes carry separate terms, which a London build does not need.

**What the sources lack.** NHS England publishes no list of emergency departments by site. Its A&E statistics are by trust, and site-level data is only promised in a supplementary data set. OpenStreetMap's `emergency=yes` tag on hospitals fills the gap, with the ODS's trust sites as a cross-check.

## Decisions to review

1. **GP access as two measured indicators**, the walk and patients per GP, so that users can weight them apart.
2. **The pharmacies curve for the GP walk**, from CIHT, since no NHS standard exists.
3. **Patients per GP and Distance to A&E wait for their curves.** Each has one source and no threshold, and the spread of London's data is the honest basis for a percentile or a ramp.
4. **Distance to A&E in straight-line kilometres**, renamed from a travel time, because that is what the evidence measures.
5. **The ONS Postcode Directory stays out of public builds** until its own page states a licence. Update, 2026-10-28: OS Code-Point Open, which the directory derives from, is confirmed under the Open Government Licence, and places the practices instead; patients per GP now waits only for its curve.
6. **Dentists stay an idea.** The ODS lists dental practices and where they are, but no open source says which take new NHS patients, and the NHS Business Services Authority says it does not record it. A map of practices alone would score places on dentists that people cannot register with.

## Findings for the spikes

- **S6.** How complete OpenStreetMap's mapped GP surgeries and its hospitals with `emergency=yes` are, against the ODS's GP practices and trust sites. The same spike checks how far walking distances differ from straight lines.

## Testing

- Both catalogue files pass every check: `just check` runs `atlas validate` and the factor explorer's 45 tests.
- The factor explorer's copy of the catalogue is refreshed with `just docs`.

## Done when

- The checks pass, and the pull request is merged.

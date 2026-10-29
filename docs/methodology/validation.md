# Validation

Status: draft. This document describes how the project checks its inputs and its method. It does not check whether results match anyone's opinion or any published ranking. A difference is not an error: a ranking weighs different things, often for a different reader.

## Principles

- Check every input against its dataset.
- Check independent datasets that measure related things against each other.
- Check facts anyone can verify.
- Check that the method does what it says.
- Use outside comparisons to explain differences, never as a pass or fail.
- Rely on no one's personal knowledge of an area.

## Checks

| Kind | What it checks | Example |
| --- | --- | --- |
| Dataset checks | Each measured indicator reproduces its dataset | Crime counts per borough match Police.uk's published totals |
| Cross-checks | Independent datasets that measure related things agree | Aircraft noise is highest under the Heathrow flight paths; station proximity agrees with PTAL |
| Known-fact assertions | Automated tests on facts anyone can verify | A hex cell containing a Tube station has a walk time under 5 min; hex cells inside the Thames flood zone carry flood risk |
| Method tests | Golden test cases and property tests | A better measured value never lowers a score; contributions add up to the livability score |
| Outside comparisons | Where and why the scores differ from published rankings and resident wellbeing | A "why we differ" view (Phase 2) |

## The QA report

Every build writes `qa.md` into its data bundle. For each measured indicator it reports coverage, value ranges, nulls, the result of every check, and changes since the previous build. A build with a failing check is not published.

It is built ([the spec](../specs/2026-10-29-qa-report.md)). `atlas build` runs it on the bundle it has just written and moves `latest.json`, which publishes the bundle, only if no check failed. `atlas qa <region>` checks any built version again, in seconds, because it reads only the bundle. What it checks:

- **The bundle's structure:** the rows, the cells, the columns and the neighbourhoods agree with the manifest.
- **Datasets:** every dataset an indicator cites is listed, credited, and licensed (an unknown licence is a warning).
- **Values:** none is infinite or negative, a percentage is within 0 to 100, an index within 0 to 1, a text value is one that its curve can score, and no indicator is empty, mostly empty or constant.
- **Relations** (cross-checks): pairs of columns from independent datasets whose rank correlation must have the expected sign and strength, such as the walk to a station against the PTAL band.
- **Known facts:** a region's own list, in `datasets/cities/<region>/facts.py`.
- **Method tests** stay in the test suite, with the golden cases. **Dataset reproduction checks** (crime counts per borough against Police.uk's totals) need the raw files, so they belong to each indicator's own tests.

## Known traps

- **Edge effects.** The buffer zone handles them ([scoring.md](scoring.md#1-spatial-framework)).
- **Area averages.** An area average does not describe every street.
- **Anonymised crime locations.** Police.uk moves each crime to a nearby anonymised point, so counts are smoothed over neighbouring hex cells.
- **Dataset dates.** The widely used PTAL grid, for example, may predate the Elizabeth line, which opened in 2022. Spike S1 checks for a newer release, and the evidence layer shows every dataset's date.
- **Time.** Day differs from night (night transport, nightlife noise), and weekdays differ from weekends. Trends such as prices and regeneration move.
- **Counting twice.** See [scoring.md](scoring.md#10-counting-twice).

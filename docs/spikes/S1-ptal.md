# S1: PTAL to hex cells

Status: done. A spike of step 0.4 ([roadmap](../roadmap.md#spikes)). Its code is [pipeline/notebooks/s1_ptal_to_hex.py](../../pipeline/notebooks/s1_ptal_to_hex.py), throwaway and never imported by `atlas`.

## Question

Can the PTAL grid be mapped to hex cells, and is there a PTAL release newer than the Elizabeth line (2022)?

## Answer

- **Yes, to hex cells.** TfL's 100 m grid maps cleanly to H3 resolution 9. The measured indicator takes the PTAL band that covers most of each cell, which is what the catalogue already says.
- **No newer release.** The London Datastore offers only the 2015 files. The only newer source found is a "TfL PTAL 2021" layer on a GLA map server, which is not a release, states no licence, and no longer answers. TfL's own WebCAT shows current values on a map, and its team supplies the latest data on request, which is still the owner's check in [progress.md](../progress.md).

## What was done

1. Downloaded the 2015 PTAL grid values and contours from the [London Datastore](https://data.london.gov.uk/dataset/public-transport-accessibility-levels) (Open Government Licence v2) into `data/raw/ptal/`.
2. Converted each grid point from British National Grid to longitude and latitude, and gave it the H3 resolution 9 cell that holds it.
3. For each cell, compared three ways of choosing one band, and measured how much the points inside a cell disagree.
4. Counted the cells under the contours, which cover Greater London, to see whether any has no grid point.

## Findings

| What | Result |
| --- | --- |
| Grid | 159,451 points, 100 m apart, each with an access index (AI) and a band |
| Cells under the contours | 16,883 (so "about 17,000" for Greater London, not 15,000) |
| Cells with no grid point under the contours | 0 |
| Grid-point cells just outside the contours | 354, at the edge |
| Grid points per cell | 9 for the median cell, from 1 (at the edge) to 12; 95% of cells have 8 or more |
| Cells whose points all share one band | 22% |
| Share of a cell's points in its most common band | 73% on average; over half the points in 82% of cells |
| Cells where two bands tie for most common | 6% |
| Most common band equals the band at the cell's centre | 82% |
| Band of the mean AI equals the band at the cell's centre | 69%, and within one band in 97% |

**Why the most common band.** The AI is very skewed, up to 188, so one point near a station pulls a cell's mean up. The band that covers most of the cell stays closer to what a person at the cell's centre sees (82% against 69%). It is also easy to explain in the evidence layer. The scoring curve is a lookup on bands, so a band is what the measured indicator needs.

**What the band codes mean.** The access index runs 0 for band 0; up to 2.5 for 1a; up to 5 for 1b; then 10 for 2, 15 for 3, 20 for 4, 25 for 5, 40 for 6a, and above 40 for 6b. The data's ranges match TfL's thresholds, so the mapping can compute a band from an index.

**Cells at the edge.** The PTAL grid stops at Greater London's boundary. The 2 km buffer zone that D04 asks for gets no PTAL, and PTAL is a Greater London measure anyway. The data bundle must carry "no value" there, and must not score it as band 0.

## Decisions

1. **Map by the band that covers most of the cell.** The catalogue's method for the service level measured indicator stands. Ties, in 6% of cells, are broken by a fixed rule at build time (the lower band is the cautious one).
2. **Use the 2015 release, labelled with its date,** until TfL supplies newer data. The 2015 grid predates the Elizabeth line, so places it serves, such as Whitechapel, Woolwich and Abbey Wood, are understated.
3. **Correct the cell count** to about 17,000 in the docs. It does not change D04's choice.

## What it means for other spikes

- **S3, S5 and S6 start from a working pattern.** Points to cells by `h3.latlng_to_cell` is quick: the whole run takes about 5 seconds for 159,000 points.
- **Windows wheels.** GeoPandas, Shapely, pyogrio, h3, pyarrow and pyproj all installed from Windows wheels with uv and ran, so the geospatial stack works on this machine. They sit in the `spikes` dependency group of `pipeline/pyproject.toml`, until a task imports them from `atlas`.
- **Contours need no GDAL install.** pyogrio reads TfL's MapInfo contour file directly.

## Reproduce

From `pipeline/`, with the unzipped 2015 PTAL files in `data/raw/ptal/`:

```sh
uv run python notebooks/s1_ptal_to_hex.py
```

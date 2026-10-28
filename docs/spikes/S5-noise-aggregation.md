# S5: averaging a noise grid over a hex cell

Status: **partly done.** A spike of step 0.4 ([roadmap](../roadmap.md#spikes)). Its code is [pipeline/notebooks/s5_noise_aggregation.py](../../pipeline/notebooks/s5_noise_aggregation.py), throwaway and never imported by `atlas`. Road noise is tested. Air quality and flooding are not, for the reasons below.

## Question

How should raster data (air quality, noise) be aggregated to hex cells?

## Answer

**For noise, average the levels at the cell's addresses,** not over its area. The arithmetic mean, in decibels, of the level at each address matches the average of the addresses' own scores almost exactly. Every way of averaging over the cell's area is much further off. A cell with no address, such as a park, takes the arithmetic mean over its area.

## What was done

1. Fetched Defra's modelled daytime road noise (LAeq,16h, England Round 4, all roads) for Greater London from its WCS service: 30 tiles of 10 km, 30 million 10 m pixels, cached in `data/raw/noise/`. The service states no fees and no access constraints, and its coverage identifiers carry the same dataset identifier as the catalogue's entry.
2. Put each pixel in the H3 resolution 9 cell that holds it, by rasterising the cells onto the same grid. The median cell holds 945 pixels. Pixels below the maps' 40 dB cut-off, or empty, count as 40 dB: 8% of them.
3. Computed five ways of turning a cell's pixels into one level: the arithmetic mean in dB, the sound energy mean (the mean of the sound energy, converted back to dB), the highest pixel, and the mean of the levels sampled at the cell's postcode points, arithmetic and energy. Postcode points from OS Code-Point Open stand in for addresses, about 10 a cell, in 13,583 of the 16,883 cells.
4. Scored each with the road noise curve (1 at 50 dB, 0 at 70 dB), and compared with a benchmark: score every address's own level, then average the scores in the cell. That is what an average resident would score.

## Findings

**The choice matters a great deal.** Over the cell's area, the sound energy mean is a median 4.7 dB above the arithmetic mean (9 dB at the 95th percentile), because a loud road dominates the energy. Two thirds of cells score differently by more than 0.1 between the two, and the average score is 0.85 by the arithmetic mean, 0.65 by the energy mean, and 0.27 by the highest pixel. The ranking of cells hardly changes (rank correlation 0.94 between the first two), so the choice moves the scale more than the order.

**Against the benchmark of the addresses' own scores** (cells with addresses):

| Way of averaging | Mean score minus the benchmark | Mean absolute difference | Rank correlation |
| --- | --- | --- | --- |
| Arithmetic mean at addresses | +0.03 | 0.04 | 0.97 |
| Energy mean at addresses | −0.10 | 0.10 | 0.97 |
| Arithmetic mean over the area | +0.08 | 0.12 | 0.76 |
| Energy mean over the area | −0.15 | 0.18 | 0.82 |
| Highest pixel | −0.57 | 0.57 | 0.75 |

Over the area, the arithmetic mean has the smaller error in the score, and the energy mean the better ranking, and neither is close. People live at addresses, which sit nearer roads than the average pixel does (the arithmetic mean over the area is a median 1.2 dB below the mean at addresses), and a cell's streets and its back gardens, parks and rooftops are not alike. Averaging at addresses keeps both the scale and the order.

## Decisions

1. **Road noise: the arithmetic mean of the levels at the cell's addresses,** with the area's arithmetic mean for a cell with no address. The catalogue's road noise method says so, and the measured indicator moves to `spiked`.
2. **Rail and aircraft noise use the same method,** untested on their own data. Their methods say so.
3. **Air quality keeps the area-weighted mean for now.** The finding probably carries over, since pollution is also higher beside roads, but the spike could not test it: the LAEI's licence is unconfirmed, and Defra's background maps are a coarse 1 km grid, where the choice matters little.
4. **Address points:** OS Code-Point Open stood in, and its licence for public builds is still open (see [S3](S3-sales-and-rents.md)). OS Open UPRN, an Ordnance Survey product that locates every address, may be a better source. The spike did not check it or its licence. Neither is confirmed.

## What was not tested

- **Flooding.** The share of a cell's area at risk is a different quantity, where the area is the right weight. Whether to weight it by homes instead is open, and the same address points would answer it.
- **Rail and aircraft noise,** and other metrics (night, evening).
- **Postcodes as addresses.** They include businesses, and one postcode holds many homes. A set of dwellings would sharpen the answer, and would not change its direction: the gap between the two groups of methods is large.

## Reproduce

From `pipeline/`, with S1's contours, S3's Code-Point Open data and S2's data in `data/raw/`:

```sh
uv run python notebooks/s5_noise_aggregation.py
```

The first run downloads the tiles from Defra (about 120 MB).

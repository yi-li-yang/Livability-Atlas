import { describe, expect, it } from "vitest";
import type { Bundle } from "../../data/bundle";
import type { Manifest } from "../../generated/manifest.schema";
import { withPlaces } from "./withPlaces";

const manifest = (travel: boolean): Manifest => ({
  format_version: 1,
  version: "t",
  region: { id: "t", name: "T" },
  grid: { system: "h3", resolution: 9 },
  cell_count: 3,
  factors: [],
  indicators: [
    {
      id: "travel-time-to-places",
      name: "Travel time",
      column: "travel_time_to_places",
      unit: "minutes",
      evidence_type: "estimate",
      preference_type: "fixed",
      curve: { shape: "ramp", t0: 90, t1: 15 },
      datasets: [],
    },
  ],
  datasets: [],
  ...(travel
    ? {
        travel: {
          indicator: "travel-time-to-places",
          stations: "s",
          cell_stations: "c",
          matrix: "m",
          station_count: 0,
          unreachable: 65535,
          reach_minutes: 40,
          walk_metres_a_minute: 80,
          street_factor: 1.33,
        },
      }
    : {}),
});

const bundle = (travel = true): Bundle => ({
  manifest: manifest(travel),
  cells: ["a", "b", "c"],
  columns: { travel_time_to_places: [60, 70, 80] },
});

describe("the bundle with the user's places", () => {
  it("holds the mean minutes to the places in the travel indicator, to a tenth", () => {
    const out = withPlaces(bundle(), [
      Float64Array.from([10, 20.04, Number.NaN]),
      Float64Array.from([30, 40, 5]),
    ]);
    expect(out.columns.travel_time_to_places).toEqual([20, 30, null]);
  });

  it("is the bundle as it was without places, or without travel files", () => {
    const b = bundle();
    expect(withPlaces(b, [])).toBe(b);
    const none = bundle(false);
    expect(withPlaces(none, [Float64Array.from([1, 2, 3])])).toBe(none);
  });

  it("leaves the bundle it was given alone", () => {
    const b = bundle();
    withPlaces(b, [Float64Array.from([1, 2, 3])]);
    expect(b.columns.travel_time_to_places).toEqual([60, 70, 80]);
  });
});

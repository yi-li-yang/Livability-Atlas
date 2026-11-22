import { describe, expect, it } from "vitest";
import type { ManifestIndicator } from "../../generated/manifest.schema";
import {
  bandOf,
  higherIsBetter,
  startsHigherIsBetter,
  withDirection,
  withRange,
} from "./preferences";

const indicator = (
  id: string,
  curve: ManifestIndicator["curve"],
  preference_type: ManifestIndicator["preference_type"] = "user-direction",
): ManifestIndicator => ({
  id,
  name: id,
  column: id,
  unit: "",
  evidence_type: "direct",
  preference_type,
  curve,
  datasets: [],
});

const nightlife = indicator("nightlife", {
  shape: "percentile",
  better: "higher",
});
const density = indicator("density", { shape: "percentile", better: "lower" });
const age = indicator(
  "building-age",
  { shape: "ideal-range", l0: 1800, l1: 1850, u1: 2020, u0: 2030 },
  "user-range",
);

describe("the direction of a user-direction indicator", () => {
  it("starts as the catalogue's curve says", () => {
    expect(startsHigherIsBetter(nightlife)).toBe(true);
    expect(startsHigherIsBetter(density)).toBe(false);
    expect(
      startsHigherIsBetter(indicator("walk", { shape: "ramp", t0: 20, t1: 5 })),
    ).toBe(false);
    expect(
      startsHigherIsBetter(indicator("x", { shape: "lookup", scores: {} })),
    ).toBeNull();
  });

  it("is the other way once flipped", () => {
    expect(higherIsBetter({ weights: {} }, nightlife)).toBe(true);
    expect(
      higherIsBetter({ weights: {}, flipped: ["nightlife"] }, nightlife),
    ).toBe(false);
  });

  it("is set by flipping the indicator, or by taking the flip away", () => {
    const fewer = withDirection({ weights: {} }, nightlife, false);
    expect(fewer.flipped).toEqual(["nightlife"]);
    expect(withDirection(fewer, nightlife, false)).toEqual(fewer);
    expect(withDirection(fewer, nightlife, true)).toEqual({ weights: {} });
    expect(
      withDirection({ weights: {}, flipped: ["a"] }, density, true).flipped,
    ).toEqual(["a", "density"]);
  });
});

describe("the band of a user-range indicator", () => {
  it("starts as the catalogue's full-marks band", () => {
    expect(bandOf({ weights: {} }, age)).toEqual([1850, 2020]);
  });

  it("is the user's once set, and the catalogue's again once cleared", () => {
    const set = withRange({ weights: {} }, age, [1890, 1930]);
    expect(set.ranges).toEqual({ "building-age": [1890, 1930] });
    expect(bandOf(set, age)).toEqual([1890, 1930]);
    expect(withRange(set, age, null)).toEqual({ weights: {} });
  });

  it("puts the two ends in order", () => {
    expect(withRange({ weights: {} }, age, [1930, 1890]).ranges).toEqual({
      "building-age": [1890, 1930],
    });
  });

  it("is the catalogue's when the user sets it back to that", () => {
    expect(withRange({ weights: {} }, age, [1850, 2020])).toEqual({
      weights: {},
    });
  });
});

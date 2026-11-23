import { describe, expect, it } from "vitest";
import { curveScore } from "./curves";

// These are the numbers of the golden test cases in shared/fixtures/scoring/, which the Python
// reference scorer reproduces: the web app's engine must give the same.
describe("curveScore", () => {
  const fall = { shape: "ramp", t0: 25, t1: 5 } as const;

  it("scores a falling ramp, flat beyond both thresholds", () => {
    expect(curveScore(fall, 9)).toBeCloseTo(0.8, 12);
    expect(curveScore(fall, 30)).toBe(0);
    expect(curveScore(fall, 3)).toBe(1);
    expect(curveScore(fall, 25)).toBe(0);
    expect(curveScore({ shape: "ramp", t0: 0, t1: 100 }, 25)).toBeCloseTo(
      0.25,
      12,
    );
  });

  it("scores an ideal range inside the band, on each slope and at its edges", () => {
    const band = {
      shape: "ideal-range",
      l0: 14,
      l1: 20,
      u1: 26,
      u0: 32,
    } as const;
    expect(curveScore(band, 23)).toBe(1);
    expect(curveScore(band, 29)).toBeCloseTo(0.5, 12);
    expect(curveScore(band, 17)).toBeCloseTo(0.5, 12);
    expect(curveScore(band, 14)).toBe(0);
    expect(curveScore(band, 26)).toBe(1);
    expect(curveScore(band, 40)).toBe(0);
  });

  it("scores a lookup, and returns null for a category it does not list", () => {
    const flood = {
      shape: "lookup",
      scores: { "very low": 1, low: 0.75, medium: 0.4, high: 0 },
    } as const;
    expect(curveScore(flood, "low")).toBe(0.75);
    expect(curveScore(flood, "high")).toBe(0);
    expect(curveScore(flood, "extreme")).toBeNull();
  });

  it("scores the lowest PTAL band as data: 0 is a score, and an absent value is not", () => {
    const ptal = {
      shape: "lookup",
      scores: { "0": 0, "1a": 0.125, "6b": 1 },
    } as const;
    expect(curveScore(ptal, "0")).toBe(0);
    expect(curveScore(ptal, "6b")).toBe(1);
  });

  it("scores a log ramp by the ratio of the values: half of 4000 is halfway to 1000", () => {
    const rent = { shape: "ramp", t0: 4000, t1: 1000, log: true } as const;
    expect(curveScore(rent, 2000)).toBeCloseTo(0.5, 12);
    expect(curveScore(rent, 500)).toBe(1);
    expect(curveScore(rent, 8000)).toBe(0);
  });

  it("scores a count on the log of the value plus its offset", () => {
    const cafes = {
      shape: "ramp",
      t0: 0,
      t1: 15,
      log: true,
      offset: 1,
    } as const;
    expect(curveScore(cafes, 0)).toBe(0);
    expect(curveScore(cafes, 3)).toBeCloseTo(0.5, 12);
    expect(curveScore(cafes, 1)).toBeCloseTo(0.25, 12);
  });

  it("scores a value with no logarithm as the low end of the values", () => {
    expect(curveScore({ shape: "ramp", t0: 1, t1: 4, log: true }, 0)).toBe(0);
    expect(curveScore({ shape: "ramp", t0: 4, t1: 1, log: true }, -2)).toBe(1);
  });
});

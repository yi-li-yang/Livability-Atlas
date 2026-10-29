import { describe, expect, it } from "vitest";
import type { Bundle, Value } from "../../data/bundle";
import type {
  Manifest,
  ManifestIndicator,
} from "../../generated/manifest.schema";
import {
  describeLimit,
  limitableIndicators,
  rangeOf,
  withLimit,
  withoutLimit,
} from "./limits";

const indicator = (
  id: string,
  unit: string,
  extra: Partial<ManifestIndicator> = {},
): ManifestIndicator => ({
  id,
  name: `Name of ${id}`,
  column: id.replace(/-/g, "_"),
  unit,
  evidence_type: "direct",
  preference_type: "fixed",
  datasets: [],
  ...extra,
});

const manifest = (indicators: ManifestIndicator[]): Manifest => ({
  format_version: 1,
  version: "t",
  region: { id: "t", name: "T" },
  grid: { system: "h3", resolution: 9 },
  cell_count: 5,
  factors: [],
  indicators,
  datasets: [],
});

function bundle(
  columns: Record<string, Value[]>,
  indicators: ManifestIndicator[],
): Bundle {
  return {
    manifest: manifest(indicators),
    cells: ["a", "b", "c", "d", "e"],
    columns,
  };
}

describe("describeLimit", () => {
  const rent = indicator("renting-cost", "£ a month");
  it("says a maximum and a minimum in words with the unit", () => {
    expect(describeLimit({ indicator: "renting-cost", max: 2000 }, rent)).toBe(
      "Name of renting-cost: at most £2,000 a month",
    );
    expect(describeLimit({ indicator: "renting-cost", min: 1500 }, rent)).toBe(
      "Name of renting-cost: at least £1,500 a month",
    );
  });

  it("lists the categories allowed", () => {
    const band = indicator("service-level", "PTAL band");
    expect(
      describeLimit({ indicator: "service-level", in: ["4", "5", "6a"] }, band),
    ).toBe("Name of service-level: only PTAL band 4, 5 or 6a");
  });

  it("names the indicator by its id when the bundle no longer has it", () => {
    expect(describeLimit({ indicator: "gone", max: 3 }, undefined)).toBe(
      "gone: at most 3",
    );
  });
});

describe("limitableIndicators", () => {
  it("offers the indicators with a column of their own, numeric or in categories", () => {
    const indicators = [
      indicator("walk", "minutes"),
      indicator("band", "PTAL band"),
      indicator("faith", "minutes", {
        options: [{ id: "x", name: "X", column: "faith__x" }],
      }),
    ];
    const b = bundle(
      {
        walk: [1, 2, null, 4, 5],
        band: ["1a", "2", "6b", null, "3"],
        faith__x: [1, 2, 3, 4, 5],
      },
      indicators,
    );
    const found = limitableIndicators(b);
    expect(found.map((f) => [f.indicator.id, f.kind])).toEqual([
      ["band", "category"],
      ["walk", "number"],
    ]);
    expect(found[0].values).toEqual(["1a", "2", "3", "6b"]);
  });

  it("treats a column of numbers written as text, like fare zones, as numbers", () => {
    const b = bundle({ zone: ["1", "3", "2", null, "5"] }, [
      indicator("zone", "fare zone"),
    ]);
    const [zone] = limitableIndicators(b);
    expect(zone.kind).toBe("number");
  });
});

describe("rangeOf", () => {
  it("gives the lowest, the middle and the highest of the numbers that exist", () => {
    const values: Value[] = [10, 20, 30, 40, 50, 60, 70, 80, 90, null, 100];
    expect(rangeOf(values)).toEqual({ min: 10, median: 55, max: 100 });
  });

  it("has nothing to give where no value exists", () => {
    expect(rangeOf([null, null])).toBeNull();
  });
});

describe("withLimit and withoutLimit", () => {
  it("a new limit on an indicator replaces the old one on it", () => {
    const first = withLimit({ weights: {} }, { indicator: "walk", max: 5 });
    const second = withLimit(first, { indicator: "walk", min: 2 });
    expect(second.limits).toEqual([{ indicator: "walk", min: 2 }]);
  });

  it("keeps limits on other indicators, and removes one by its indicator", () => {
    const profile = withLimit(
      withLimit({ weights: { a: 1 } }, { indicator: "walk", max: 5 }),
      { indicator: "rent", max: 9 },
    );
    expect(profile.limits).toHaveLength(2);
    const less = withoutLimit(profile, "walk");
    expect(less.limits).toEqual([{ indicator: "rent", max: 9 }]);
    expect(less.weights).toEqual({ a: 1 });
    expect(withoutLimit(less, "rent").limits).toBeUndefined();
  });
});

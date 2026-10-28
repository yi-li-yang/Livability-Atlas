import { describe, expect, it } from "vitest";
import type { ManifestFactor } from "../../generated/manifest.schema";
import { countAgain, levelAt, withWeight } from "./level";

const leaf = (id: string, weight: number): ManifestFactor => ({
  id,
  name: id,
  default_weight: weight,
  indicator: id,
});

const FACTORS: ManifestFactor[] = [
  {
    id: "safety",
    name: "Safety",
    default_weight: 4,
    children: [leaf("crime", 3), leaf("lighting", 1)],
  },
  {
    id: "transport",
    name: "Transport",
    default_weight: 3,
    children: [
      {
        id: "getting-around",
        name: "Getting around",
        default_weight: 2,
        children: [leaf("service-level", 3)],
      },
    ],
  },
  leaf("comfort", 1),
];

const NONE = { weights: {} };

describe("levelAt", () => {
  it("shows the top-level factors with their shares of the weight", () => {
    const level = levelAt(FACTORS, NONE, []);
    expect(level.trail).toEqual([]);
    expect(level.counted.map((f) => [f.id, f.share])).toEqual([
      ["safety", 0.5],
      ["transport", 0.375],
      ["comfort", 0.125],
    ]);
    expect(level.notCounted).toEqual([]);
  });

  it("opens a factor to show its sub-factors, whose shares add to 1 among themselves", () => {
    const level = levelAt(FACTORS, NONE, ["safety"]);
    expect(level.trail).toEqual([{ id: "safety", name: "Safety" }]);
    expect(level.counted.map((f) => [f.id, f.share])).toEqual([
      ["crime", 0.75],
      ["lighting", 0.25],
    ]);
  });

  it("uses the weights the user has set, over the defaults", () => {
    const level = levelAt(FACTORS, withWeight(NONE, "safety", 1), []);
    expect(level.counted.find((f) => f.id === "safety")?.weight).toBe(1);
    expect(level.counted.find((f) => f.id === "safety")?.share).toBeCloseTo(
      1 / 5,
    );
  });

  it("moves a factor at weight 0 to the list of those not counted", () => {
    const level = levelAt(FACTORS, withWeight(NONE, "comfort", 0), []);
    expect(level.counted.map((f) => f.id)).toEqual(["safety", "transport"]);
    expect(level.notCounted.map((f) => f.id)).toEqual(["comfort"]);
  });

  it("does not count a factor whose sub-factors are all at weight 0", () => {
    const profile = withWeight(withWeight(NONE, "crime", 0), "lighting", 0);
    const level = levelAt(FACTORS, profile, []);
    expect(level.notCounted.map((f) => f.id)).toEqual(["safety"]);
    expect(level.notCounted[0].weight).toBe(4);
  });

  it("marks the factors that open, and gives sub-factors the tint of their top-level factor", () => {
    const top = levelAt(FACTORS, NONE, []);
    expect(top.counted.map((f) => f.opens)).toEqual([true, true, false]);
    const inside = levelAt(FACTORS, NONE, ["transport", "getting-around"]);
    const safety = levelAt(FACTORS, NONE, ["safety"]);
    expect(inside.trail.map((t) => t.id)).toEqual([
      "transport",
      "getting-around",
    ]);
    expect(inside.counted[0].colour).not.toBe(safety.counted[0].colour);
    expect(safety.counted[0].colour).toBe(safety.counted[1].colour);
    expect(safety.counted[0].colour).not.toBe(top.counted[0].colour);
  });

  it("stops where a path leaves the tree or reaches a measured indicator", () => {
    expect(levelAt(FACTORS, NONE, ["nope"]).trail).toEqual([]);
    expect(levelAt(FACTORS, NONE, ["safety", "crime"]).trail).toEqual([
      { id: "safety", name: "Safety" },
    ]);
  });

  it("gives every factor of a level a different colour at the top", () => {
    const colours = levelAt(FACTORS, NONE, []).counted.map((f) => f.colour);
    expect(new Set(colours).size).toBe(colours.length);
  });
});

describe("countAgain", () => {
  it("returns a factor and what is inside it to their default weights", () => {
    const profile = withWeight(
      withWeight(withWeight(NONE, "safety", 0), "crime", 0),
      "lighting",
      0,
    );
    const back = countAgain(profile, FACTORS[0]);
    expect(back.weights).toEqual({});
    expect(levelAt(FACTORS, back, []).counted.map((f) => f.id)).toContain(
      "safety",
    );
  });

  it("leaves the weights set elsewhere alone", () => {
    const profile = withWeight(withWeight(NONE, "safety", 0), "comfort", 5);
    expect(countAgain(profile, FACTORS[0]).weights).toEqual({ comfort: 5 });
  });

  it("gives a factor whose default weight is 0 a weight of 1", () => {
    const factor = leaf("choice", 0);
    expect(countAgain(NONE, factor).weights).toEqual({ choice: 1 });
  });
});

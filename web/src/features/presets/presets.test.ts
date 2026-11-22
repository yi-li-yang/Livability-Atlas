import { describe, expect, it } from "vitest";
import type {
  ManifestFactor,
  ManifestPreset,
} from "../../generated/manifest.schema";
import { fromPreset, matchingPreset, undoPreset } from "./presets";

const leaf = (id: string, weight = 3): ManifestFactor => ({
  id,
  name: id,
  default_weight: weight,
  indicator: id,
});

const factors: ManifestFactor[] = [
  leaf("health-care"),
  leaf("education"),
  leaf("transport"),
  {
    id: "community-and-people",
    name: "Community and people",
    default_weight: 0,
    children: [leaf("faith", 0), leaf("diversity")],
  },
];

const retiree: ManifestPreset = {
  id: "retiree",
  name: "Retired",
  description: "Health care close by.",
  weights: { "health-care": 5, education: 0 },
  flipped: ["nightlife", "density"],
  limits: [
    { indicator: "council-tax", max: 2000, min: null, in: null },
    { indicator: "service-level", in: ["6a", "6b"] },
  ],
};

describe("starting from a preset", () => {
  it("replaces the weights, directions and limits with the preset's", () => {
    const profile = fromPreset(
      {
        weights: { transport: 1 },
        flipped: ["x"],
        limits: [{ indicator: "rent", max: 1 }],
      },
      retiree,
      factors,
    );
    expect(profile).toEqual({
      weights: { "health-care": 5, education: 0 },
      flipped: ["nightlife", "density"],
      limits: [
        { indicator: "council-tax", max: 2000 },
        { indicator: "service-level", in: ["6a", "6b"] },
      ],
    });
  });

  it("keeps what is the user's own: choices, bands and the scoring mode", () => {
    const profile = fromPreset(
      {
        weights: {},
        ranges: { "building-age": [1890, 1930] },
        mode: "balanced",
      },
      { id: "p", name: "P", description: "" },
      factors,
    );
    expect(profile).toEqual({
      weights: {},
      ranges: { "building-age": [1890, 1930] },
      mode: "balanced",
    });
  });

  it("keeps a picked choice counting, with the factors that hold it", () => {
    const profile = fromPreset(
      {
        weights: { faith: 4, "community-and-people": 3 },
        choices: { faith: ["hindu"] },
      },
      retiree,
      factors,
    );
    expect(profile.choices).toEqual({ faith: ["hindu"] });
    expect(profile.weights.faith).toBe(4);
    expect(profile.weights["community-and-people"]).toBe(3);
  });
});

describe("the preset the profile is at", () => {
  const presets = [retiree];

  it("is recognised while the profile still matches it, and not once it differs", () => {
    const start = fromPreset({ weights: {} }, retiree, factors);
    expect(matchingPreset(start, presets, factors)?.id).toBe("retiree");
    expect(
      matchingPreset(
        { ...start, weights: { ...start.weights, transport: 4 } },
        presets,
        factors,
      ),
    ).toBeNull();
    expect(matchingPreset({ weights: {} }, presets, factors)).toBeNull();
  });

  it("does not depend on the order of directions, or on a weight set to its default", () => {
    const start = fromPreset({ weights: {} }, retiree, factors);
    const same = {
      ...start,
      weights: { ...start.weights, transport: 3 },
      flipped: ["density", "nightlife"],
      limits: [...(start.limits ?? [])].reverse(),
    };
    expect(matchingPreset(same, presets, factors)?.id).toBe("retiree");
  });

  it("is still recognised with a choice picked, a band set or the mode changed", () => {
    const start = fromPreset(
      { weights: {}, choices: { faith: ["sikh"] }, mode: "balanced" },
      retiree,
      factors,
    );
    expect(matchingPreset(start, presets, factors)?.id).toBe("retiree");
  });
});

describe("undoing a preset", () => {
  it("brings back the weights, directions and limits, and keeps what changed since", () => {
    const before = { weights: { transport: 1 }, flipped: ["x"] };
    const now = {
      ...fromPreset(before, retiree, factors),
      mode: "balanced" as const,
      choices: { faith: ["sikh"] },
    };
    const undone = undoPreset(now, before, factors);
    expect(undone.weights.transport).toBe(1);
    expect(undone.flipped).toEqual(["x"]);
    expect(undone.limits).toBeUndefined();
    expect(undone.mode).toBe("balanced");
    expect(undone.choices).toEqual({ faith: ["sikh"] });
    // the choice picked after the preset still counts
    expect(undone.weights.faith).toBeGreaterThan(0);
    expect(undone.weights["community-and-people"]).toBeGreaterThan(0);
  });
});

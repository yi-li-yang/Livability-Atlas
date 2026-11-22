import { describe, expect, it } from "vitest";
import type { ManifestPreset } from "../../generated/manifest.schema";
import { fromPreset, matchingPreset } from "./presets";

const retiree: ManifestPreset = {
  id: "retiree",
  name: "Retired",
  description: "Health care close by.",
  weights: { "health-care": 5, education: 0 },
  flipped: ["nightlife"],
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
        flipped: ["density"],
        limits: [{ indicator: "rent", max: 1 }],
      },
      retiree,
    );
    expect(profile).toEqual({
      weights: { "health-care": 5, education: 0 },
      flipped: ["nightlife"],
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
        choices: { faith: ["hindu"] },
        ranges: { "building-age": [1890, 1930] },
        mode: "balanced",
      },
      { id: "p", name: "P", description: "" },
    );
    expect(profile).toEqual({
      weights: {},
      choices: { faith: ["hindu"] },
      ranges: { "building-age": [1890, 1930] },
      mode: "balanced",
    });
  });

  it("is recognised while the profile still matches it, and not once it differs", () => {
    const presets = [retiree];
    const start = fromPreset({ weights: {} }, retiree);
    expect(matchingPreset(start, presets)?.id).toBe("retiree");
    expect(
      matchingPreset(
        { ...start, weights: { ...start.weights, transport: 4 } },
        presets,
      ),
    ).toBeNull();
    expect(matchingPreset({ weights: {} }, presets)).toBeNull();
  });
});

import { describe, expect, it } from "vitest";
import type {
  Manifest,
  ManifestFactor,
  ManifestIndicator,
} from "../../generated/manifest.schema";
import type { Profile } from "../../scoring/region";
import { legendEnds, noDataNote, viewedIndicator, viewOptions } from "./views";

const leaf = (id: string, name = id): ManifestFactor => ({
  id,
  name,
  default_weight: 3,
  indicator: id,
});

const indicator = (
  id: string,
  type: ManifestIndicator["preference_type"] = "fixed",
): ManifestIndicator => ({
  id,
  name: id,
  column: id,
  unit: "",
  evidence_type: "direct",
  preference_type: type,
  datasets: [],
});

function manifestOf(
  factors: ManifestFactor[],
  indicators: ManifestIndicator[],
): Manifest {
  return {
    format_version: 2,
    version: "test",
    region: { id: "test", name: "Test" },
    grid: { system: "h3", resolution: 9 },
    cell_count: 1,
    factors,
    indicators,
    datasets: [],
  };
}

const FACTORS: ManifestFactor[] = [
  {
    id: "safety",
    name: "Safety",
    default_weight: 4,
    children: [
      {
        id: "crime",
        name: "Crime",
        default_weight: 3,
        children: [leaf("burglary", "Burglary"), leaf("theft", "Theft")],
      },
      leaf("lighting", "Street lighting"),
    ],
  },
  leaf("comfort", "Comfort"),
];
const INDICATORS = ["burglary", "theft", "lighting", "comfort"].map((id) =>
  indicator(id),
);

describe("viewOptions", () => {
  it("lists each factor and measured indicator, in the order of the tree", () => {
    const options = viewOptions(manifestOf(FACTORS, INDICATORS));
    expect(options.map((o) => o.id)).toEqual([
      "safety",
      "crime",
      "burglary",
      "theft",
      "lighting",
      "comfort",
    ]);
  });

  it("says how deep each is and which top-level factor it is in", () => {
    const options = viewOptions(manifestOf(FACTORS, INDICATORS));
    expect(options.map((o) => [o.depth, o.group, o.groupId])).toEqual([
      [0, "Safety", "safety"],
      [1, "Safety", "safety"],
      [2, "Safety", "safety"],
      [2, "Safety", "safety"],
      [1, "Safety", "safety"],
      [0, "Comfort", "comfort"],
    ]);
    expect(options[0].name).toBe("Safety");
    expect(options[4].name).toBe("Street lighting");
  });

  it("leaves out a choice indicator, which has no score until the user picks", () => {
    const options = viewOptions(
      manifestOf(FACTORS, [
        ...INDICATORS.filter((i) => i.id !== "theft"),
        indicator("theft", "user-choice"),
      ]),
    );
    expect(options.map((o) => o.id)).not.toContain("theft");
    expect(options.map((o) => o.id)).toContain("burglary");
  });

  it("leaves out a factor that holds nothing but choices", () => {
    const options = viewOptions(
      manifestOf(FACTORS, [
        indicator("burglary", "user-choice"),
        indicator("theft", "user-choice"),
        indicator("lighting"),
        indicator("comfort"),
      ]),
    );
    expect(options.map((o) => o.id)).toEqual(["safety", "lighting", "comfort"]);
  });

  it("leaves out a measured indicator that the manifest does not describe", () => {
    const options = viewOptions(
      manifestOf(
        FACTORS,
        INDICATORS.filter((i) => i.id !== "comfort"),
      ),
    );
    expect(options.map((o) => o.id)).not.toContain("comfort");
  });

  it("gives nothing for a manifest with no factors", () => {
    expect(viewOptions(manifestOf([], []))).toEqual([]);
  });
});

describe("the groups of the list", () => {
  it("are told apart by the id of their top-level factor, not by its name", () => {
    const twins = [
      { ...leaf("a", "Same"), default_weight: 1 },
      { ...leaf("b", "Same"), default_weight: 1 },
    ];
    const options = viewOptions(
      manifestOf(twins, [indicator("a"), indicator("b")]),
    );
    expect(options.map((o) => o.groupId)).toEqual(["a", "b"]);
  });
});

describe("noDataNote", () => {
  const safety = FACTORS[0];
  const none: Profile = { weights: { crime: 0, lighting: 0 } };

  it("tells the user to give a weight where everything inside the factor weighs 0", () => {
    expect(noDataNote("Safety", safety, none)).toBe(
      "Nothing inside Safety counts: give a weight inside it above 0.",
    );
  });

  it("says there is no data where something inside the factor does count", () => {
    expect(noDataNote("Safety", safety, { weights: {} })).toBe(
      "There is no data for Safety.",
    );
    expect(noDataNote("Safety", safety, { weights: { crime: 0 } })).toBe(
      "There is no data for Safety.",
    );
  });

  it("says there is no data for a measured indicator, whatever its weight", () => {
    const lighting = safety.children?.[1];
    expect(
      noDataNote("Street lighting", lighting, { weights: { lighting: 0 } }),
    ).toBe("There is no data for Street lighting.");
  });

  it("says there is no data for a factor that cannot be found", () => {
    expect(noDataNote("Nothing", undefined, none)).toBe(
      "There is no data for Nothing.",
    );
  });
});

describe("the values at the ends of the legend", () => {
  const rent: ManifestIndicator = {
    ...indicator("renting-cost"),
    unit: "£ a month",
    curve: { shape: "ramp", t0: 3739, t1: 1540, log: true, from_region: true },
  };
  const manifest = manifestOf(
    [
      {
        id: "housing",
        name: "Housing",
        default_weight: 3,
        children: [leaf("renting-cost", "Renting cost")],
      },
    ],
    [rent],
  );

  it("are the values that score 0 and 1, where the map shows a measured indicator", () => {
    const shown = viewedIndicator(manifest, "renting-cost");
    expect(shown?.id).toBe("renting-cost");
    expect(legendEnds(shown, false)).toEqual({
      low: "£3,739 a month",
      high: "£1,540 a month",
      unit: null,
    });
  });

  it("swap where the user has turned the direction round", () => {
    expect(legendEnds(rent, true)).toEqual({
      low: "£1,540 a month",
      high: "£3,739 a month",
      unit: null,
    });
  });

  it("give a long unit once, under the bar, so that the two ends fit side by side", () => {
    const burglary: ManifestIndicator = {
      ...indicator("burglary"),
      unit: "crimes a year per 1,000 residents",
      curve: { shape: "ramp", t0: 14.85, t1: 2.47, log: true },
    };
    expect(legendEnds(burglary, false)).toEqual({
      low: "14.9",
      high: "2.47",
      unit: "crimes a year per 1,000 residents",
    });
    const tax: ManifestIndicator = {
      ...indicator("council-tax"),
      unit: "£ a year (Band D)",
      curve: { shape: "ramp", t0: 2609.2, t1: 1028.21 },
    };
    expect(legendEnds(tax, false)).toEqual({
      low: "£2,609",
      high: "£1,028",
      unit: "£ a year (Band D)",
    });
  });

  it("are not given for a factor, the livability score, or a curve with no two ends", () => {
    expect(viewedIndicator(manifest, "housing")).toBeNull();
    const choice = manifestOf(
      [leaf("community")],
      [
        {
          ...indicator("community", "user-choice"),
          options: [{ id: "a", name: "A", column: "community__a" }],
        },
      ],
    );
    // A choice has no column of its own: each option has one.
    expect(viewedIndicator(choice, "community")).toBeNull();
    expect(viewedIndicator(manifest, null)).toBeNull();
    expect(legendEnds(null, false)).toBeNull();
    const lookup = {
      ...indicator("zone"),
      curve: { shape: "lookup", scores: { "1": 1 } },
    } as ManifestIndicator;
    expect(legendEnds(lookup, false)).toBeNull();
  });
});

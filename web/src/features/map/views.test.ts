import { describe, expect, it } from "vitest";
import type {
  Manifest,
  ManifestFactor,
  ManifestIndicator,
} from "../../generated/manifest.schema";
import type { Profile } from "../../scoring/region";
import { noDataNote, viewOptions } from "./views";

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
    format_version: 1,
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

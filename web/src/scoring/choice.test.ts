import { describe, expect, it } from "vitest";
import type { Bundle } from "../data/bundle";
import type { Manifest } from "../generated/manifest.schema";
import { scoreCell } from "./engine";
import { allLeafScores, scoreCaseFor, scoreRegion } from "./region";

/**
 * A choice indicator, "faith", whose options are the walking minutes to a place of worship (a ramp
 * from 15 minutes, score 0, to 5, score 1), beside a plain indicator, "park".
 */
const manifest: Manifest = {
  format_version: 2,
  version: "test",
  region: { id: "test", name: "Test" },
  grid: { system: "h3", resolution: 9 },
  cell_count: 4,
  factors: [
    {
      id: "community",
      name: "Community",
      default_weight: 2,
      children: [
        { id: "faith", name: "Faith", default_weight: 0, indicator: "faith" },
        { id: "park", name: "Park", default_weight: 3, indicator: "park" },
      ],
    },
  ],
  indicators: [
    {
      id: "faith",
      name: "Faith",
      column: "faith",
      unit: "minutes on foot",
      evidence_type: "direct",
      preference_type: "user-choice",
      curve: { shape: "ramp", t0: 15, t1: 5 },
      datasets: [],
      options: [
        {
          id: "hindu",
          name: "Hindu",
          group: "Religion",
          column: "faith__hindu",
        },
        { id: "sikh", name: "Sikh", group: "Religion", column: "faith__sikh" },
      ],
    },
    {
      id: "park",
      name: "Park",
      column: "park",
      unit: "minutes on foot",
      evidence_type: "direct",
      preference_type: "fixed",
      curve: { shape: "ramp", t0: 15, t1: 5 },
      datasets: [],
    },
  ],
  datasets: [],
};

const bundle: Bundle = {
  manifest,
  cells: ["a", "b", "c", "d"],
  columns: {
    faith: [null, null, null, null], // a choice has no column of its own in the table
    faith__hindu: [5, 15, null, 10],
    faith__sikh: [15, 5, 15, null],
    park: [10, 10, 10, 10],
  },
};

const near = (value: number, want: number) =>
  expect(Math.abs(value - want)).toBeLessThan(1e-9);

describe("the leaf scores of a choice indicator", () => {
  it("score nothing until an option is picked", () => {
    const leaves = allLeafScores(bundle, [], {});
    expect(Array.from(leaves.get("faith") ?? []).every(Number.isNaN)).toBe(
      true,
    );
  });

  it("are the scores of the one option picked", () => {
    const faith = allLeafScores(bundle, [], { faith: ["hindu"] }).get("faith");
    expect(Array.from(faith ?? [])).toEqual([1, 0, Number.NaN, 0.5]);
  });

  it("are the best of the options picked, ignoring one a cell has no value for", () => {
    const faith = allLeafScores(bundle, [], { faith: ["hindu", "sikh"] }).get(
      "faith",
    );
    expect(Array.from(faith ?? [])).toEqual([1, 1, 0, 0.5]);
  });

  it("ignore an option that the bundle does not have", () => {
    const faith = allLeafScores(bundle, [], { faith: ["jedi"] }).get("faith");
    expect(Array.from(faith ?? []).every(Number.isNaN)).toBe(true);
  });

  it("keep a fixed direction, whatever flips are asked", () => {
    const faith = allLeafScores(bundle, ["faith"], { faith: ["hindu"] }).get(
      "faith",
    );
    expect(Array.from(faith ?? [])).toEqual([1, 0, Number.NaN, 0.5]);
  });
});

describe("the region's score with a choice", () => {
  const profile = (picked: string[]) => ({
    weights: { faith: 3 },
    choices: { faith: picked },
  });

  it("leaves the choice out while nothing is picked", () => {
    const leaves = allLeafScores(bundle, [], {});
    const scores = scoreRegion(bundle, profile([]), leaves);
    near(scores[0], 50); // the park alone: (15 - 10) / 10
  });

  it("weighs the best option against the other indicators", () => {
    const p = profile(["hindu"]);
    const scores = scoreRegion(bundle, p, allLeafScores(bundle, [], p.choices));
    near(scores[0], 75); // faith 1 and park 0.5, equal weights
    near(scores[1], 25);
    near(scores[2], 50); // no faith value: the park carries it
  });

  it("agrees with the one-cell engine, which explains the score", () => {
    const p = profile(["hindu", "sikh"]);
    const scores = scoreRegion(bundle, p, allLeafScores(bundle, [], p.choices));
    bundle.cells.forEach((_, i) => {
      const slow = scoreCell(scoreCaseFor(bundle, p, i)).score;
      near(scores[i], slow ?? Number.NaN);
    });
  });
});

describe("a choice whose options carry their own curves (a region ramp, D25)", () => {
  // Each option of "community" is scored against its own ends: a group that is 10% of the
  // residents at most scores 1 there, and one that is 40% at most needs 40% for full marks.
  const own: Bundle = {
    manifest: {
      ...manifest,
      factors: [
        {
          id: "people",
          name: "People",
          default_weight: 3,
          children: [
            {
              id: "community",
              name: "Community",
              default_weight: 3,
              indicator: "community",
            },
          ],
        },
      ],
      indicators: [
        {
          id: "community",
          name: "Community",
          column: "community",
          unit: "% of residents",
          evidence_type: "direct",
          preference_type: "user-choice",
          curve: null,
          datasets: [],
          options: [
            {
              id: "small",
              name: "Small",
              column: "community__small",
              curve: { shape: "ramp", t0: 0, t1: 10, from_region: true },
            },
            {
              id: "large",
              name: "Large",
              column: "community__large",
              curve: { shape: "ramp", t0: 0, t1: 40, from_region: true },
            },
          ],
        },
      ],
    },
    cells: ["a", "b"],
    columns: {
      community: [null, null],
      community__small: [5, 10],
      community__large: [10, 40],
    },
  };

  it("scores each option by its own curve", () => {
    const small = allLeafScores(own, [], { community: ["small"] });
    expect(Array.from(small.get("community") ?? [])).toEqual([0.5, 1]);
    const large = allLeafScores(own, [], { community: ["large"] });
    expect(Array.from(large.get("community") ?? [])).toEqual([0.25, 1]);
  });

  it("agrees with the one-cell engine", () => {
    const p = { weights: {}, choices: { community: ["small", "large"] } };
    const scores = scoreRegion(own, p, allLeafScores(own, [], p.choices));
    own.cells.forEach((_, i) => {
      near(scores[i], scoreCell(scoreCaseFor(own, p, i)).score ?? Number.NaN);
    });
  });
});

describe("the evidence of a choice in a cell where no picked option has a value", () => {
  it("still describes the curve of a picked option, not a missing one", async () => {
    const { explainCell } = await import("./explain");
    const own: Bundle = {
      manifest: {
        ...manifest,
        indicators: [
          {
            ...manifest.indicators[0],
            curve: null,
            options: [
              {
                id: "hindu",
                name: "Hindu",
                column: "faith__hindu",
                curve: { shape: "ramp", t0: 30, t1: 2, from_region: true },
              },
            ],
          },
          manifest.indicators[1],
        ],
      },
      cells: ["a"],
      columns: { faith: [null], faith__hindu: [null], park: [10] },
    };
    const profile = { weights: { faith: 3 }, choices: { faith: ["hindu"] } };
    const lines = explainCell(own, profile, 0).factors.flatMap((f) => [
      f,
      ...f.children,
    ]);
    const faith = lines.find((line) => line.id === "faith");
    expect(faith?.evidence?.curve).toEqual({
      shape: "ramp",
      t0: 30,
      t1: 2,
      from_region: true,
    });
  });
});

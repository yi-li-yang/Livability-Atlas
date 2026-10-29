import { describe, expect, it } from "vitest";
import type { Bundle, Value } from "../data/bundle";
import type {
  Manifest,
  ManifestFactor,
  ManifestIndicator,
} from "../generated/manifest.schema";
import { scoreCell } from "./engine";
import {
  allLeafScores,
  type Profile,
  scoreCaseFor,
  scoreRegion,
} from "./region";

/** A small seeded generator, so a failing case can be run again. */
function random(seed: number): () => number {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 2 ** 32;
    return state / 2 ** 32;
  };
}

const indicator = (
  id: string,
  curve: ManifestIndicator["curve"],
): ManifestIndicator => ({
  id,
  name: id,
  column: id,
  unit: "",
  evidence_type: "direct",
  preference_type: "fixed",
  curve,
  datasets: [],
});

const leaf = (id: string, weight: number): ManifestFactor => ({
  id,
  name: id,
  default_weight: weight,
  indicator: id,
});

const factors: ManifestFactor[] = [
  {
    id: "safety",
    name: "Safety",
    default_weight: 4,
    children: [leaf("crime", 3), leaf("band", 2)],
  },
  {
    id: "environment",
    name: "Environment",
    default_weight: 3,
    children: [
      {
        id: "quiet",
        name: "Quiet",
        default_weight: 2,
        children: [leaf("noise", 3), leaf("trees", 1)],
      },
      leaf("rank", 2),
    ],
  },
  leaf("comfort", 1),
];

const indicators = [
  indicator("crime", { shape: "ramp", t0: 100, t1: 0 }),
  indicator("band", { shape: "lookup", scores: { a: 0, b: 0.5, c: 1 } }),
  indicator("noise", { shape: "ideal-range", l0: 30, l1: 40, u0: 55, u1: 70 }),
  indicator("trees", { shape: "percentile", better: "higher" }),
  indicator("rank", { shape: "percentile", better: "lower" }),
  indicator("comfort", { shape: "ramp", t0: 0, t1: 10 }),
];

function makeBundle(size: number, seed: number): Bundle {
  const next = random(seed);
  // About one value in five is missing. Values repeat, so that percentiles have ties.
  const column = (make: () => Value): Value[] =>
    Array.from({ length: size }, () => (next() < 0.2 ? null : make()));
  const columns: Record<string, Value[]> = {
    crime: column(() => Math.round(next() * 120)),
    band: column(() => ["a", "b", "c", "d"][Math.floor(next() * 4)]),
    noise: column(() => 25 + Math.round(next() * 50)),
    trees: column(() => Math.floor(next() * 8)),
    rank: column(() => Math.floor(next() * 8)),
    comfort: column(() => next() * 12),
  };
  const manifest: Manifest = {
    format_version: 1,
    version: "test",
    region: { id: "test", name: "Test" },
    grid: { system: "h3", resolution: 9 },
    cell_count: size,
    factors,
    indicators,
    datasets: [],
  };
  return {
    manifest,
    cells: Array.from({ length: size }, (_, i) => `cell${i}`),
    columns,
  };
}

/** The scores that `scoreCell` gives, one cell at a time: the reference for the fast path. */
function slow(bundle: Bundle, profile: Profile): (number | null)[] {
  return bundle.cells.map(
    (_, i) => scoreCell(scoreCaseFor(bundle, profile, i)).score,
  );
}

function expectSame(fast: Float64Array, reference: (number | null)[]): void {
  expect(fast.length).toBe(reference.length);
  reference.forEach((want, i) => {
    if (want === null) expect(fast[i], `cell ${i}`).toBeNaN();
    else expect(Math.abs(fast[i] - want), `cell ${i}`).toBeLessThan(1e-9);
  });
}

const PROFILES: Record<string, Profile> = {
  "the defaults": { weights: {} },
  "some weights changed": { weights: { safety: 0, rank: 5, trees: 4 } },
  "a whole subtree at zero": { weights: { noise: 0, trees: 0 } },
  "directions flipped": { weights: {}, flipped: ["crime", "trees", "band"] },
  "everything at zero": {
    weights: { safety: 0, environment: 0, comfort: 0 },
  },
};

describe("scoring a whole region", () => {
  const bundle = makeBundle(300, 7);
  const leaves = (profile: Profile) => allLeafScores(bundle, profile.flipped);

  for (const [name, profile] of Object.entries(PROFILES)) {
    it(`gives the scores that scoreCell gives, with ${name}`, () => {
      expectSame(
        scoreRegion(bundle, profile, leaves(profile)),
        slow(bundle, profile),
      );
    });
  }

  it("gives the scores that scoreCell gives, over random weights", () => {
    const next = random(11);
    const ids = [
      "safety",
      "environment",
      "quiet",
      "crime",
      "band",
      "noise",
      "trees",
      "rank",
      "comfort",
    ];
    for (let round = 0; round < 15; round++) {
      const weights = Object.fromEntries(
        ids.map((id) => [id, Math.floor(next() * 6)]),
      );
      const profile: Profile = { weights };
      expectSame(
        scoreRegion(bundle, profile, leaves(profile)),
        slow(bundle, profile),
      );
    }
  });

  it("changes with the weights while the leaf scores stay the same", () => {
    const base = leaves({ weights: {} });
    const a = scoreRegion(bundle, { weights: {} }, base);
    const b = scoreRegion(bundle, { weights: { safety: 0 } }, base);
    expect(Array.from(a)).not.toEqual(Array.from(b));
  });

  it("scores 'a' as the worst category and a missing one as no data", () => {
    const leafScores = allLeafScores(bundle).get("band");
    const values = bundle.columns.band;
    values.forEach((value, i) => {
      const score = leafScores?.[i] ?? Number.NaN;
      if (value === "a") expect(score).toBe(0);
      if (value === "c") expect(score).toBe(1);
      if (value === null || value === "d") expect(score).toBeNaN();
    });
  });
});

describe("scoring a region by one factor", () => {
  const bundle = makeBundle(300, 7);
  const leaves = (profile: Profile) => allLeafScores(bundle, profile.flipped);

  /** What the one-cell engine gives one node of the tree, from 0 to 100. */
  function slowNode(profile: Profile, id: string): (number | null)[] {
    return bundle.cells.map((_, i) => {
      const node = scoreCell(scoreCaseFor(bundle, profile, i)).nodes[id];
      return node?.score == null ? null : node.score * 100;
    });
  }

  for (const id of ["safety", "environment", "quiet", "crime", "comfort"]) {
    for (const [name, profile] of Object.entries(PROFILES)) {
      it(`gives the score of ${id} that the one-cell engine gives, with ${name}`, () => {
        expectSame(
          scoreRegion(bundle, profile, leaves(profile), id),
          slowNode(profile, id),
        );
      });
    }
  }

  it("scores a factor by the weights inside it, whatever its own weight", () => {
    const profile: Profile = { weights: { safety: 0, crime: 5, band: 1 } };
    const alone = scoreRegion(bundle, profile, leaves(profile), "safety");
    expectSame(alone, slowNode(profile, "safety"));
    expect(alone.some((s) => !Number.isNaN(s))).toBe(true);
  });

  it("gives no data where everything inside the factor weighs 0", () => {
    const profile: Profile = { weights: { crime: 0, band: 0 } };
    const none = scoreRegion(bundle, profile, leaves(profile), "safety");
    expect(none.every((s) => Number.isNaN(s))).toBe(true);
  });

  it("leaves the leaf scores alone when it scores a measured indicator", () => {
    const base = leaves({ weights: {} });
    const before = new Map([...base].map(([id, scores]) => [id, [...scores]]));
    const crime = scoreRegion(bundle, { weights: {} }, base, "crime");
    for (const [id, scores] of base) {
      expect([...scores], id).toEqual(before.get(id));
    }
    // From 0 to 100, as the others are, and not a copy of the 0 to 1 scores.
    expect(
      Math.max(...[...crime].filter((s) => !Number.isNaN(s))),
    ).toBeGreaterThan(1);
  });

  it("scores the whole tree for an id that the tree does not have", () => {
    const profile: Profile = { weights: {} };
    expectSame(
      scoreRegion(bundle, profile, leaves(profile), "nonsense"),
      slow(bundle, profile),
    );
  });
});

describe("the time to rescore a region", () => {
  // The size of the MVP: about 17,000 cells, ten factors and forty measured indicators.
  const SIZE = 17_000;
  const next = random(3);
  const names = Array.from({ length: 40 }, (_, i) => `indicator-${i}`);
  const big: Bundle = {
    manifest: {
      format_version: 1,
      version: "big",
      region: { id: "big", name: "Big" },
      grid: { system: "h3", resolution: 9 },
      cell_count: SIZE,
      factors: Array.from({ length: 10 }, (_, f) => ({
        id: `factor-${f}`,
        name: `Factor ${f}`,
        default_weight: 3,
        children: names.slice(f * 4, f * 4 + 4).map((id) => leaf(id, 3)),
      })),
      indicators: names.map((id) =>
        indicator(id, { shape: "ramp", t0: 0, t1: 1 }),
      ),
      datasets: [],
    },
    cells: Array.from({ length: SIZE }, (_, i) => `cell${i}`),
    columns: Object.fromEntries(
      names.map((id) => [
        id,
        Array.from({ length: SIZE }, () => (next() < 0.1 ? null : next())),
      ]),
    ),
  };

  it("is under 100 ms after a change of weights, the budget of the roadmap", () => {
    const leaves = allLeafScores(big);
    const times: number[] = [];
    for (let round = 0; round < 7; round++) {
      const started = performance.now();
      scoreRegion(big, { weights: { "factor-0": round % 6 } }, leaves);
      times.push(performance.now() - started);
    }
    times.sort((a, b) => a - b);
    expect(times[3]).toBeLessThan(100);
  });
});

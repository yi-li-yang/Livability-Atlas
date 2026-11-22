import { describe, expect, it } from "vitest";
import type { Profile } from "./region";
import { sensitivity } from "./sensitivity";

/**
 * Four places scored on two factors. The ranking is by the weighted sum of the two scores, as a
 * stand-in for the app's ranking of neighbourhoods.
 */
const PLACES: Record<string, { a: number; b: number }> = {
  p: { a: 9, b: 1 },
  q: { a: 8, b: 3 },
  r: { a: 5, b: 5 },
  s: { a: 1, b: 9 },
};

function rankBy(profile: Profile, count: number): string[] {
  const wa = profile.weights.a ?? 3;
  const wb = profile.weights.b ?? 3;
  return Object.entries(PLACES)
    .map(([name, v]) => ({ name, score: wa * v.a + wb * v.b }))
    .sort((x, y) => y.score - x.score)
    .slice(0, count)
    .map((p) => p.name);
}

describe("the sensitivity of the top places to the weights", () => {
  it("changes each weight by 20% up and down, one at a time", () => {
    const seen: Record<string, number>[] = [];
    sensitivity(
      (profile) => {
        seen.push({ ...profile.weights });
        return rankBy(profile, 2);
      },
      { weights: {} },
      { a: 5, b: 2 },
    );
    // the first call is the baseline, then each factor up and down
    expect(seen).toHaveLength(5);
    expect(seen[0]).toEqual({});
    const changed = seen.slice(1).map((w) => Object.entries(w));
    expect(changed.map((c) => c[0][0])).toEqual(["a", "a", "b", "b"]);
    expect(changed.map((c) => c[0][1])).toEqual([
      expect.closeTo(6, 12),
      expect.closeTo(4, 12),
      expect.closeTo(2.4, 12),
      expect.closeTo(1.6, 12),
    ]);
    expect(changed.every((c) => c.length === 1)).toBe(true);
  });

  it("is 1 when no change of weights moves the top places", () => {
    const result = sensitivity(
      () => ["p", "q"],
      { weights: {} },
      { a: 3, b: 3 },
    );
    expect(result.stability).toBe(1);
    expect(result.baseline).toEqual(["p", "q"]);
    expect(result.staysIn).toEqual({ p: 1, q: 1 });
  });

  it("falls where a change of weights brings another place into the top", () => {
    // with both weights 3, q (33) and p (30) lead r (30) on the tie-break of the sort, and a
    // change of one weight moves r or s into the top two
    const result = sensitivity(
      (profile) => rankBy(profile, 2),
      { weights: { a: 3, b: 3 } },
      { a: 3, b: 3 },
    );
    expect(result.baseline).toHaveLength(2);
    expect(result.scenarios).toHaveLength(4);
    for (const s of result.scenarios) expect(s.kept).toBeLessThanOrEqual(2);
    const mean =
      result.scenarios.reduce((sum, s) => sum + s.kept / 2, 0) /
      result.scenarios.length;
    expect(result.stability).toBeCloseTo(mean, 12);
  });

  it("says in how many changes each of the top places stays", () => {
    const answers = [
      ["x", "y"], // the baseline
      ["x", "y"],
      ["x", "z"],
      ["x", "z"],
      ["x", "z"],
    ];
    let call = 0;
    const result = sensitivity(
      () => answers[call++],
      { weights: {} },
      { a: 3, b: 3 },
    );
    expect(result.staysIn).toEqual({ x: 1, y: 0.25 });
    expect(result.scenarios.map((s) => s.kept)).toEqual([2, 1, 1, 1]);
    expect(result.stability).toBeCloseTo((1 + 0.5 + 0.5 + 0.5) / 4, 12);
  });

  it("leaves out a factor with weight 0, which no change can move", () => {
    const result = sensitivity(
      (profile) => rankBy(profile, 2),
      { weights: {} },
      { a: 0, b: 3 },
    );
    expect(result.scenarios.map((s) => s.factor)).toEqual(["b", "b"]);
  });

  it("leaves the user's profile alone", () => {
    const profile: Profile = { weights: { a: 5 }, flipped: ["x"] };
    sensitivity((p) => rankBy(p, 2), profile, { a: 5, b: 3 });
    expect(profile).toEqual({ weights: { a: 5 }, flipped: ["x"] });
  });

  it("gives a result of 1 and no scenarios where every weight is 0", () => {
    const result = sensitivity(
      () => ["p", "q"],
      { weights: {} },
      { a: 0, b: 0 },
    );
    expect(result.scenarios).toEqual([]);
    expect(result.stability).toBe(1);
  });

  it("takes the size of the change as an option", () => {
    const seen: number[] = [];
    sensitivity(
      (p) => {
        seen.push(p.weights.a ?? 0);
        return ["p"];
      },
      { weights: {} },
      { a: 5 },
      { change: 0.5 },
    );
    expect(seen).toEqual([0, 7.5, 2.5]);
  });
});

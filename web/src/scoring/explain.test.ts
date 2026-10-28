import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { type Bundle, loadBundle } from "../data/bundle";
import { explainCell, rankOf, sortedScores } from "./explain";
import { allLeafScores, scoreRegion } from "./region";

const FIXTURES = fileURLToPath(
  new URL("../../e2e/fixtures/bundles/", import.meta.url),
);

async function fixtureFetch(url: string | URL | Request): Promise<Response> {
  return new Response(
    await readFile(FIXTURES + String(url).replace(/^\/bundles\//, "")),
  );
}

const load = (): Promise<Bundle> =>
  loadBundle("/bundles", "london", fixtureFetch);

describe("explainCell", () => {
  it("gives the score the region scorer gives, and contributions that add up to it", async () => {
    const bundle = await load();
    const profile = { weights: {} };
    const scores = scoreRegion(bundle, profile, allLeafScores(bundle));
    for (const index of [0, 17, 100, bundle.cells.length - 1]) {
      const explanation = explainCell(bundle, profile, index);
      expect(explanation.score).toBeCloseTo(scores[index], 9);
      const total = explanation.factors.reduce(
        (sum, f) => sum + (f.contribution ?? 0),
        0,
      );
      expect(total).toBeCloseTo(scores[index], 9);
    }
  });

  it("lists the top-level factors that count, and opens each into what is inside it", async () => {
    const bundle = await load();
    const explanation = explainCell(bundle, { weights: {} }, 0);
    expect(explanation.factors.map((f) => f.id)).toEqual([
      "transport",
      "environment",
      "safety",
      "health-care",
    ]);
    const transport = explanation.factors[0];
    expect(transport.children.map((c) => c.id)).toEqual(["getting-around"]);
    expect(transport.children[0].children.map((c) => c.id)).toEqual([
      "station-proximity",
      "service-level",
    ]);
  });

  it("leaves out a factor at weight 0", async () => {
    const bundle = await load();
    const explanation = explainCell(bundle, { weights: { transport: 0 } }, 0);
    expect(explanation.factors.map((f) => f.id)).toEqual([
      "environment",
      "safety",
      "health-care",
    ]);
  });

  it("names the two best factors as strengths and the worst as the weakness", async () => {
    const bundle = await load();
    for (let index = 0; index < bundle.cells.length; index++) {
      const { factors, strengths, weakness } = explainCell(
        bundle,
        { weights: {} },
        index,
      );
      const scored = factors
        .filter((f) => f.score !== null)
        .sort((a, b) => (b.score ?? 0) - (a.score ?? 0));
      expect(strengths.every((s) => (s.score ?? 0) > 0.5)).toBe(true);
      expect(strengths.length).toBeLessThanOrEqual(2);
      if (strengths.length > 0) expect(strengths[0]).toBe(scored[0]);
      if (weakness) {
        expect(weakness.score).toBeLessThan(0.5);
        expect(weakness).toBe(scored[scored.length - 1]);
        expect(strengths).not.toContain(weakness);
      }
    }
  });
});

describe("rankOf", () => {
  const ascending = sortedScores(Float64Array.of(10, Number.NaN, 40, 40, 90));

  it("ranks the best score 1 and the worst last", () => {
    expect(rankOf(ascending, 90)).toBe(1);
    expect(rankOf(ascending, 10)).toBe(4);
  });

  it("gives tied scores the best rank among them", () => {
    expect(rankOf(ascending, 40)).toBe(2);
  });

  it("leaves cells without a score out of the count", () => {
    expect(ascending).toHaveLength(4);
  });
});

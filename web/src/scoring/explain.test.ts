import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { type Bundle, loadBundle } from "../data/bundle";
import {
  explainCell,
  type FactorLine,
  rankableScores,
  rankOf,
  sortedScores,
} from "./explain";
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

describe("the evidence of a measured indicator", () => {
  const find = (lines: FactorLine[], id: string): FactorLine | undefined => {
    for (const line of lines) {
      if (line.id === id) return line;
      const inside = find(line.children, id);
      if (inside) return inside;
    }
    return undefined;
  };

  it("is the indicator, its raw value in the cell and its datasets", async () => {
    const bundle = await load();
    const explanation = explainCell(bundle, { weights: {} }, 17);
    const line = find(explanation.factors, "station-proximity");
    const evidence = line?.evidence;
    expect(evidence?.indicator.id).toBe("station-proximity");
    expect(evidence?.value).toBe(bundle.columns.station_proximity[17]);
    expect(evidence?.option).toBeNull();
    const credited = evidence?.datasets.map((d) => d.id) ?? [];
    expect(credited.length).toBeGreaterThan(0);
    expect(credited).toEqual(evidence?.indicator.datasets);
  });

  it("is absent from a factor that only holds others", async () => {
    const bundle = await load();
    const explanation = explainCell(bundle, { weights: {} }, 0);
    expect(find(explanation.factors, "transport")?.evidence).toBeNull();
  });

  it("names the picked option that carries a choice indicator, with its own value", async () => {
    const bundle = await load();
    const profile = {
      weights: { "community-and-people": 3, faith: 3 },
      choices: { faith: ["hindu", "sikh"] },
    };
    for (const index of [0, 50, 120]) {
      const explanation = explainCell(bundle, profile, index);
      const evidence = find(explanation.factors, "faith")?.evidence;
      const hindu = bundle.columns.faith__hindu[index] as number;
      const sikh = bundle.columns.faith__sikh[index] as number;
      expect(evidence?.option).toBe(hindu <= sikh ? "Hindu" : "Sikh");
      expect(evidence?.value).toBe(Math.min(hindu, sikh));
    }
  });
});

describe("the limits in an explanation", () => {
  it("lists each limit with its result in the cell, and says whether the cell is left out", async () => {
    const bundle = await load();
    const profile = {
      weights: {},
      limits: [
        { indicator: "station-proximity", max: 4 },
        { indicator: "gp-walk", min: 0 },
      ],
    };
    for (const index of [0, 40, 90]) {
      const explanation = explainCell(bundle, profile, index);
      expect(explanation.limits.map((l) => l.indicator?.id)).toEqual([
        "station-proximity",
        "gp-walk",
      ]);
      const walk = Number(bundle.columns.station_proximity[index]);
      expect(explanation.limits[0].result).toBe(walk <= 4 ? "pass" : "fail");
      expect(explanation.limits[1].result).toBe("pass");
      expect(explanation.excluded).toBe(walk > 4);
    }
  });

  it("is not excluded, and lists nothing, without limits", async () => {
    const bundle = await load();
    const explanation = explainCell(bundle, { weights: {} }, 5);
    expect(explanation.limits).toEqual([]);
    expect(explanation.excluded).toBe(false);
  });
});

describe("rankableScores", () => {
  it("leaves out the cells that limits exclude, so they are not ranked", () => {
    const scores = Float64Array.from([10, 90, 50]);
    const ranked = sortedScores(
      rankableScores(scores, Uint8Array.from([0, 1, 0])),
    );
    expect(Array.from(ranked)).toEqual([10, 50]);
    expect(rankOf(ranked, 50)).toBe(1);
  });
});

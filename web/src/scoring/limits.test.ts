import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { type Bundle, loadBundle } from "../data/bundle";
import { type HardLimit, scoreCell } from "./engine";
import {
  checkLimits,
  excludedCells,
  type Limit,
  limitResultsFor,
  scoreCaseFor,
} from "./region";

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

const LIMITS: Limit[] = [
  { indicator: "station-proximity", max: 8 },
  { indicator: "service-level", in: ["3", "4", "5", "6a", "6b"] },
  { indicator: "burglary", max: 20 },
  { indicator: "gp-walk", min: 6 },
];

describe("checkLimits", () => {
  it("passes a value that meets a number exactly, and fails one beyond it", async () => {
    const bundle = await load();
    const index = bundle.columns.station_proximity.findIndex(
      (v) => v !== null && Number(v) > 0,
    );
    const value = Number(bundle.columns.station_proximity[index]);
    const at = (max: number) =>
      limitResultsFor(
        bundle,
        [{ indicator: "station-proximity", max }],
        index,
      )[0].result;
    expect(at(value)).toBe("pass");
    expect(at(value - 0.001)).toBe("fail");
  });

  it("checks a minimum and a list of categories", async () => {
    const bundle = await load();
    const i = 10;
    const walk = Number(bundle.columns.gp_walk[i]);
    const results = (limits: Limit[]) =>
      limitResultsFor(bundle, limits, i).map((r) => r.result);
    expect(results([{ indicator: "gp-walk", min: walk }])).toEqual(["pass"]);
    expect(results([{ indicator: "gp-walk", min: walk + 1 }])).toEqual([
      "fail",
    ]);
    const band = String(bundle.columns.service_level[i]);
    expect(results([{ indicator: "service-level", in: [band] }])).toEqual([
      "pass",
    ]);
    expect(results([{ indicator: "service-level", in: ["zz"] }])).toEqual([
      "fail",
    ]);
  });

  it("could not check a cell that lacks the data, and keeps it", async () => {
    const bundle = await load();
    const missing = bundle.columns.station_proximity.indexOf(null);
    if (missing < 0) return; // the fixture has no gap: nothing to check
    const { excluded } = checkLimits(bundle, [
      { indicator: "station-proximity", max: 0 },
    ]);
    expect(excluded[missing]).toBe(0);
    expect(
      limitResultsFor(
        bundle,
        [{ indicator: "station-proximity", max: 0 }],
        missing,
      )[0].result,
    ).toBe("could_not_check");
  });

  it("ignores a limit on an indicator that the bundle does not have", async () => {
    const bundle = await load();
    const { excluded } = checkLimits(bundle, [
      { indicator: "nonsense", max: 1 },
    ]);
    expect(excluded.every((e) => e === 0)).toBe(true);
  });

  it("excludes a cell that fails any one limit, and no cell with no limits", async () => {
    const bundle = await load();
    expect(excludedCells(bundle, []).every((e) => e === 0)).toBe(true);
    const some = excludedCells(bundle, LIMITS);
    const count = some.reduce((a, b) => a + b, 0);
    expect(count).toBeGreaterThan(0);
    expect(count).toBeLessThan(bundle.cells.length);
  });

  it("agrees with the one-cell engine, as the region scorer does for scores", async () => {
    const bundle = await load();
    const excluded = excludedCells(bundle, LIMITS);
    const hard_limits: HardLimit[] = LIMITS.map((limit, n) =>
      "in" in limit
        ? { id: `limit-${n}`, indicator: limit.indicator, in: [...limit.in] }
        : { id: `limit-${n}`, ...limit },
    );
    bundle.cells.forEach((_, i) => {
      const reference = scoreCell({
        ...scoreCaseFor(bundle, { weights: {} }, i),
        hard_limits,
      });
      expect(excluded[i] === 1, `cell ${i}`).toBe(reference.excluded);
      const results = limitResultsFor(bundle, LIMITS, i).map((r) => r.result);
      expect(results, `cell ${i}`).toEqual(
        hard_limits.map((l) => reference.limits[l.id]),
      );
    });
  });
});

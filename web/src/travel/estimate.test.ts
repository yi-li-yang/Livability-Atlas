import { readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  estimateCase,
  meanMinutes,
  placeMinutes,
  straightMetres,
  type TravelCase,
  type TravelData,
} from "./estimate";

const FIXTURES = fileURLToPath(
  new URL("../../../shared/fixtures/travel/", import.meta.url),
);
const cases: TravelCase[] = readdirSync(FIXTURES)
  .filter((name) => name.endsWith(".json"))
  .map((name) => JSON.parse(readFileSync(FIXTURES + name, "utf-8")));

describe("the travel estimate", () => {
  it("has golden cases to reproduce", () => {
    expect(cases.length).toBeGreaterThanOrEqual(4);
  });

  for (const c of cases) {
    it(`reproduces the golden case ${c.id}`, () => {
      const got = estimateCase(c);
      if (c.expected === null) expect(got).toBeNull();
      else
        expect(Math.abs((got ?? Number.NaN) - c.expected)).toBeLessThan(1e-9);
    });
  }

  it("measures a straight line along a meridian as the radius times the angle", () => {
    expect(straightMetres(51, 0, 51.001, 0)).toBeCloseTo(111.19508023353292, 9);
  });
});

describe("the estimate for every cell of a region", () => {
  it("gives each cell what the one-cell estimate gives", () => {
    // The golden cases' stations and matrix, with each case's cell as one cell of a region.
    for (const c of cases) {
      const n = c.stations.length;
      const data: TravelData = {
        stations: c.stations.map(([lat, lng]) => ({ lat, lng })),
        matrix: Uint16Array.from(c.matrix.flat()),
        cellStart: Int32Array.from([0, c.cell.stations.length]),
        cellStation: Int32Array.from(c.cell.stations.map(([s]) => s)),
        cellMinutes: Float64Array.from(c.cell.stations.map(([, m]) => m)),
        centres: [{ lat: c.cell.lat, lng: c.cell.lng }],
        constants: c.constants,
      };
      expect(n).toBe(c.matrix.length);
      const [got] = placeMinutes(data, c.place);
      if (c.expected === null) expect(got).toBeNaN();
      else expect(Math.abs(got - c.expected)).toBeLessThan(1e-9);
    }
  });
});

describe("the mean over the user's places", () => {
  it("is the mean, cell by cell, and no value where one place has none", () => {
    const mean = meanMinutes([
      Float64Array.from([10, 20, 5]),
      Float64Array.from([30, Number.NaN, 15]),
    ]);
    expect(Array.from(mean)).toEqual([20, Number.NaN, 10]);
  });
});

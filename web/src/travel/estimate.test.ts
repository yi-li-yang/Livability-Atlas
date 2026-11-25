import { readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { cellToLatLng, latLngToCell } from "h3-js";
import { describe, expect, it } from "vitest";
import {
  estimateCase,
  meanMinutes,
  placeMinutes,
  straightMetres,
  type TravelCase,
  type TravelData,
} from "./estimate";
import { cellFinder } from "./load";

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

/**
 * A golden case as a region of two cells: the case's cell, and the cell that holds the place, with
 * the place's links when it has them.
 */
function regionOf(c: TravelCase, withPlaceCell = true): TravelData {
  const own = c.place.stations ?? [];
  const links = [...c.cell.stations, ...own];
  const placeCell = withPlaceCell && c.place.stations ? 1 : -1;
  return {
    stations: c.stations.map(([lat, lng]) => ({ lat, lng })),
    matrix: Uint16Array.from(c.matrix.flat()),
    cellStart: Int32Array.from([0, c.cell.stations.length, links.length]),
    cellStation: Int32Array.from(links.map(([s]) => s)),
    cellMinutes: Float64Array.from(links.map(([, m]) => m)),
    centres: [
      { lat: c.cell.lat, lng: c.cell.lng },
      { lat: c.place.lat, lng: c.place.lng },
    ],
    cellOf: () => placeCell,
    constants: c.constants,
  };
}

describe("the estimate for every cell of a region", () => {
  it("gives each cell what the one-cell estimate gives", () => {
    // The golden cases' stations and matrix, with each case's cell as one cell of a region.
    for (const c of cases) {
      expect(c.stations.length).toBe(c.matrix.length);
      const [got] = placeMinutes(regionOf(c), c.place);
      if (c.expected === null) expect(got).toBeNaN();
      else expect(Math.abs(got - c.expected)).toBeLessThan(1e-9);
    }
  });

  it("keeps the straight walk for a place outside the region's cells", () => {
    const c = cases.find((x) => x.id === "bus-at-the-far-end");
    if (!c) throw new Error("the golden case bus-at-the-far-end is missing");
    // No station is within a walk of the place, so without its cell there is no way.
    const [got] = placeMinutes(regionOf(c, false), c.place);
    expect(got).toBeNaN();
  });
});

describe("the cell that holds a place", () => {
  const cells = [
    latLngToCell(51.5136, -0.1337, 9),
    latLngToCell(51.5155, -0.0922, 9),
  ];
  const cellOf = cellFinder(cells, 9);

  it("is the position of the bundle's cell that holds the point", () => {
    expect(cellOf({ lat: 51.5155, lng: -0.0922 })).toBe(1);
    const [lat, lng] = cellToLatLng(cells[0]);
    expect(cellOf({ lat, lng })).toBe(0);
  });

  it("is -1 for a point outside the bundle's cells", () => {
    expect(cellOf({ lat: 48.8566, lng: 2.3522 })).toBe(-1);
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

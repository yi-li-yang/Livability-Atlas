import { describe, expect, it } from "vitest";
import type { Bundle } from "../../data/bundle";
import type { Manifest } from "../../generated/manifest.schema";
import { topNeighbourhoods } from "./top";

const manifest = (): Manifest => ({
  format_version: 1,
  version: "t",
  region: { id: "t", name: "T" },
  grid: { system: "h3", resolution: 9 },
  cell_count: 9,
  factors: [],
  indicators: [],
  datasets: [],
  neighbourhoods: [
    { name: "Soho", area: "Westminster" },
    { name: "Fitzrovia", area: "Camden" },
    { name: "Tiny", area: "Camden" },
  ],
});

// Soho: cells 0-3, Fitzrovia: cells 4-7, Tiny: cell 8 (one cell), and cell 9 has none.
const bundle = (): Bundle => ({
  manifest: manifest(),
  cells: Array.from({ length: 10 }, (_, i) => `c${i}`),
  columns: {},
  neighbourhoodOf: [0, 0, 0, 0, 1, 1, 1, 1, 2, null],
});

const N = Number.NaN;

describe("topNeighbourhoods", () => {
  it("ranks the neighbourhoods by the mean score of their cells, with the best cell of each", () => {
    const scores = Float64Array.from([60, 80, 70, 50, 40, 50, 60, 30, 99, 99]);
    const top = topNeighbourhoods(bundle(), scores, new Uint8Array(10), {
      minimumCells: 2,
    });
    expect(top.map((t) => t.name)).toEqual(["Soho", "Fitzrovia"]);
    expect(top[0].score).toBeCloseTo(65);
    expect(top[0].bestCell).toBe(1);
    expect(top[1].score).toBeCloseTo(45);
    expect(top[1].bestCell).toBe(6);
    expect(top[0].area).toBe("Westminster");
  });

  it("leaves out the cells that a hard limit excludes, and those with no score", () => {
    const scores = Float64Array.from([60, 80, N, 50, 40, 50, 60, 30, 0, 0]);
    const excluded = Uint8Array.from([0, 1, 0, 0, 0, 0, 0, 0, 0, 0]);
    const top = topNeighbourhoods(bundle(), scores, excluded, {
      minimumCells: 2,
    });
    expect(top[0].name).toBe("Soho");
    expect(top[0].score).toBeCloseTo(55); // 60 and 50: the excluded 80 and the unscored are out
    expect(top[0].bestCell).toBe(0);
  });

  it("skips a neighbourhood with too few cells that count", () => {
    const scores = Float64Array.from([60, 80, 70, 50, 40, 50, 60, 30, 99, 99]);
    const top = topNeighbourhoods(bundle(), scores, new Uint8Array(10), {
      minimumCells: 3,
    });
    expect(top.map((t) => t.name)).not.toContain("Tiny");
  });

  it("gives only as many as asked for", () => {
    const scores = Float64Array.from([60, 80, 70, 50, 40, 50, 60, 30, 99, 99]);
    const top = topNeighbourhoods(bundle(), scores, new Uint8Array(10), {
      minimumCells: 1,
      count: 2,
    });
    expect(top).toHaveLength(2);
    expect(top[0].name).toBe("Tiny"); // a single cell of 99 counts where the minimum is one
  });

  it("has nothing for a bundle that names no neighbourhoods", () => {
    const plain: Bundle = { ...bundle(), neighbourhoodOf: undefined };
    expect(
      topNeighbourhoods(plain, new Float64Array(10), new Uint8Array(10)),
    ).toEqual([]);
  });
});

import { describe, expect, it } from "vitest";
import type { Bundle } from "../../data/bundle";
import type { Manifest } from "../../generated/manifest.schema";
import { neighbourhoodStability } from "./stability";

// Four neighbourhoods of three cells. Factor "a" favours Aston and Bury; factor "b" favours Cole
// and Dene, so the weights decide which two lead.
const ramp = { shape: "ramp" as const, t0: 0, t1: 10 };
const indicator = (id: string) => ({
  id,
  name: id,
  column: id,
  unit: "",
  evidence_type: "direct" as const,
  preference_type: "fixed" as const,
  curve: ramp,
  datasets: [],
});
const manifest = (): Manifest => ({
  format_version: 2,
  version: "t",
  region: { id: "t", name: "T" },
  grid: { system: "h3", resolution: 9 },
  cell_count: 12,
  factors: [
    { id: "a", name: "A", default_weight: 3, indicator: "a" },
    { id: "b", name: "B", default_weight: 3, indicator: "b" },
  ],
  indicators: [indicator("a"), indicator("b")],
  datasets: [],
  neighbourhoods: ["Aston", "Bury", "Cole", "Dene"].map((name) => ({
    name,
    area: "Area",
  })),
});

const bundle = (a: number[], b: number[]): Bundle => ({
  manifest: manifest(),
  cells: Array.from({ length: 12 }, (_, i) => `c${i}`),
  columns: { a, b },
  neighbourhoodOf: [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3],
});

// Aston a=9, b=2; Bury a=8, b=3; Cole a=3, b=8; Dene a=2, b=9 (each repeated for its 3 cells).
const per = (values: number[]) => values.flatMap((v) => [v, v, v]);
const A = per([9, 8, 3, 2]);
const B = per([2, 3, 8, 9]);

describe("the stability of the top neighbourhoods", () => {
  it("ranks the neighbourhoods by the profile and counts what a change of weight does", () => {
    // equal weights: Aston 5.5, Bury 5.5, Cole 5.5, Dene 5.5: tied. A heavier "a" favours Aston.
    const result = neighbourhoodStability(
      bundle(A, B),
      { weights: { a: 5, b: 1 } },
      { count: 2 },
    );
    expect(result.baseline).toEqual(["0", "1"]); // Aston and Bury
    // every change of "a" or "b" by 20% leaves Aston and Bury on top: 5:1 is far from a tie
    expect(result.stability).toBe(1);
  });

  it("falls below 1 where the weights are near a tie", () => {
    const result = neighbourhoodStability(
      bundle(A, B),
      { weights: { a: 3, b: 3 } },
      { count: 2 },
    );
    expect(result.baseline).toHaveLength(2);
    expect(result.stability).toBeLessThan(1);
  });

  it("leaves out the cells that a hard limit excludes, as the app's ranking does", () => {
    const result = neighbourhoodStability(
      bundle(A, B),
      { weights: { a: 5, b: 1 }, limits: [{ indicator: "a", min: 6 }] },
      { count: 2 },
    );
    // only Aston and Bury have cells with a >= 6, so they are the only neighbourhoods ranked
    expect(result.baseline.sort()).toEqual(["0", "1"]); // Aston and Bury
  });

  it("changes the weights of the top-level factors only", () => {
    const result = neighbourhoodStability(bundle(A, B), { weights: {} });
    expect(new Set(result.scenarios.map((s) => s.factor))).toEqual(
      new Set(["a", "b"]),
    );
  });

  it("leaves out a factor that counts for nothing because everything inside it weighs 0", () => {
    const m = manifest();
    m.factors = [
      {
        id: "g",
        name: "G",
        default_weight: 3,
        children: [{ id: "a", name: "A", default_weight: 3, indicator: "a" }],
      },
      { id: "b", name: "B", default_weight: 3, indicator: "b" },
    ];
    const result = neighbourhoodStability(
      { ...bundle(A, B), manifest: m },
      { weights: { a: 0 } },
    );
    expect(new Set(result.scenarios.map((s) => s.factor))).toEqual(
      new Set(["b"]),
    );
  });

  it("tells apart two neighbourhoods with the same name", () => {
    const m = manifest();
    m.neighbourhoods = ["Aston", "Aston", "Cole", "Dene"].map((name, i) => ({
      name,
      area: `Area ${i}`,
    }));
    // the ranking is keyed by the position in the list, so the two are never taken for one
    const result = neighbourhoodStability(
      { ...bundle(per([9, 8, 3, 2]), per([2, 3, 8, 9])), manifest: m },
      { weights: { a: 5, b: 1 } },
      { count: 1 },
    );
    expect(result.baseline).toEqual(["0"]);
    expect(result.staysIn["0"]).toBe(1);
  });
});

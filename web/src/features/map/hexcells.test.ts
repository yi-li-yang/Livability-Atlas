import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { loadBundle } from "../../data/bundle";
import { scoreToColour, UNSCORED } from "./colour";
import { toHexCells } from "./hexcells";

const FIXTURES = fileURLToPath(
  new URL("../../../e2e/fixtures/bundles/", import.meta.url),
);

async function fixtureFetch(url: string | URL | Request): Promise<Response> {
  return new Response(
    await readFile(FIXTURES + String(url).replace(/^\/bundles\//, "")),
  );
}

describe("scoreToColour", () => {
  it("runs from the palette's first colour for 0 to its last for 1", () => {
    expect(scoreToColour(0)).toEqual([68, 1, 84, 255]);
    expect(scoreToColour(1)).toEqual([253, 231, 37, 255]);
  });

  it("blends between stops", () => {
    const [r, g, b] = scoreToColour(0.5);
    expect([r, g, b]).toEqual([33, 145, 140]);
  });

  it("clamps a score outside 0 to 1", () => {
    expect(scoreToColour(-1)).toEqual(scoreToColour(0));
    expect(scoreToColour(2)).toEqual(scoreToColour(1));
  });

  it("gives a cell without a score the colour for unscored", () => {
    expect(scoreToColour(null)).toEqual(UNSCORED);
  });
});

describe("toHexCells", () => {
  it("draws each cell as a hexagon coloured by the score of its value", async () => {
    const bundle = await loadBundle("/bundles", "london", fixtureFetch);
    const cells = toHexCells(bundle, "service-level");
    expect(cells).toHaveLength(bundle.cells.length);
    for (const cell of cells) {
      expect(cell.polygon.length).toBeGreaterThanOrEqual(6);
      const [lng, lat] = cell.polygon[0];
      expect(lng).toBeGreaterThan(-0.2);
      expect(lng).toBeLessThan(-0.05);
      expect(lat).toBeGreaterThan(51.45);
      expect(lat).toBeLessThan(51.55);
    }
  });

  it("scores the best PTAL band 1 and the lowest 0", async () => {
    const bundle = await loadBundle("/bundles", "london", fixtureFetch);
    const cells = toHexCells(bundle, "service-level");
    const best = cells.find((cell) => cell.value === "6b");
    expect(best?.score).toBe(1);
    const scores = cells
      .map((cell) => cell.score)
      .filter((s): s is number => s !== null);
    expect(Math.max(...scores)).toBeLessThanOrEqual(1);
    expect(Math.min(...scores)).toBeGreaterThanOrEqual(0);
  });

  it("refuses an indicator that the bundle does not hold", async () => {
    const bundle = await loadBundle("/bundles", "london", fixtureFetch);
    expect(() => toHexCells(bundle, "nope")).toThrow(/nope/);
  });
});

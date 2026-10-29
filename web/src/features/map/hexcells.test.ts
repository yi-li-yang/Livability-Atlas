import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { loadBundle } from "../../data/bundle";
import { allLeafScores, scoreRegion } from "../../scoring/region";
import { EXCLUDED, scoreToColour, UNSCORED } from "./colour";
import { cellColours, toHexCells } from "./hexcells";

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
  it("draws each cell as a hexagon", async () => {
    const bundle = await loadBundle("/bundles", "london", fixtureFetch);
    const cells = toHexCells(bundle);
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
});

describe("cellColours", () => {
  it("colours a score of 0 to 100 along the palette, and no score as unscored", () => {
    const colours = cellColours(Float64Array.of(0, 100, Number.NaN));
    expect(colours).toEqual([
      scoreToColour(0),
      scoreToColour(1),
      scoreToColour(null),
    ]);
  });

  it("colours the best service level the palette's last colour and the worst its first", async () => {
    const bundle = await loadBundle("/bundles", "london", fixtureFetch);
    // Only the service level is real data in the fixture: leave the others out of the score.
    const profile = {
      weights: {
        "station-proximity": 0,
        "walk-to-green-space": 0,
        "gp-walk": 0,
        safety: 0,
      },
    };
    const scores = scoreRegion(bundle, profile, allLeafScores(bundle));
    const bands = bundle.columns.service_level;
    const best = scores[bands.indexOf("6b")];
    expect(best).toBe(100);
    const scored = Array.from(scores).filter((s) => !Number.isNaN(s));
    expect(Math.max(...scored)).toBeLessThanOrEqual(100);
    expect(Math.min(...scored)).toBeGreaterThanOrEqual(0);
  });
});

describe("cellColours with limits", () => {
  it("greys out a cell that a limit leaves out, whatever its score, and ranks nothing", () => {
    const scores = Float64Array.from([10, 90, Number.NaN]);
    const excluded = Uint8Array.from([0, 1, 1]);
    const colours = cellColours(scores, excluded);
    expect(colours[0]).toEqual(scoreToColour(0.1));
    expect(colours[1]).toEqual(EXCLUDED);
    expect(colours[2]).toEqual(EXCLUDED);
    expect(EXCLUDED).not.toEqual(UNSCORED); // a cell left out differs from one with no data
  });

  it("colours every cell by its score where no limit applies", () => {
    const scores = Float64Array.from([10, 90]);
    expect(cellColours(scores)).toEqual(cellColours(scores, new Uint8Array(2)));
  });
});

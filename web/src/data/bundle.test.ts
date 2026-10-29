import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { loadBundle, neighbourhoodAt } from "./bundle";

const FIXTURES = fileURLToPath(
  new URL("../../e2e/fixtures/bundles/", import.meta.url),
);

/** A fetch that reads the fixture bundle from disk, as a static server would serve it. */
async function fixtureFetch(url: string | URL | Request): Promise<Response> {
  const path = String(url).replace(/^\/bundles\//, "");
  try {
    return new Response(await readFile(FIXTURES + path));
  } catch {
    return new Response("not found", { status: 404 });
  }
}

describe("loadBundle", () => {
  it("reads the manifest and the cells of the latest bundle", async () => {
    const bundle = await loadBundle("/bundles", "london", fixtureFetch);
    expect(bundle.manifest.region.id).toBe("london");
    expect(bundle.manifest.version).toMatch(/^[0-9a-f]{12}$/);
    expect(bundle.cells).toHaveLength(bundle.manifest.cell_count);
    expect(bundle.cells.length).toBeGreaterThan(100);
  });

  it("gives each indicator's values in the order of the cells", async () => {
    const bundle = await loadBundle("/bundles", "london", fixtureFetch);
    const [indicator] = bundle.manifest.indicators;
    const values = bundle.columns[indicator.column];
    expect(values).toHaveLength(bundle.cells.length);
    const bands = new Set(values);
    expect([...bands].every((band) => typeof band === "string")).toBe(true);
  });

  it("gives a choice indicator a column for each option, and none of its own", async () => {
    const bundle = await loadBundle("/bundles", "london", fixtureFetch);
    const faith = bundle.manifest.indicators.find((i) => i.id === "faith");
    expect(faith?.options?.map((o) => o.id)).toEqual(["hindu", "sikh"]);
    for (const option of faith?.options ?? []) {
      expect(bundle.columns[option.column]).toHaveLength(bundle.cells.length);
    }
    expect(bundle.columns[faith?.column ?? "faith"]).toBeUndefined();
  });

  it("holds whole numbers as numbers, not as the big integers that Parquet reads them as", async () => {
    const { columns } = await loadBundle("/bundles", "london", fixtureFetch);
    const kinds = new Set(
      Object.values(columns).flatMap((values) => values.map((v) => typeof v)),
    );
    expect(kinds).not.toContain("bigint");
    expect(kinds).toContain("number");
  });

  it("says which named neighbourhood each cell is in", async () => {
    const bundle = await loadBundle("/bundles", "london", fixtureFetch);
    const names = bundle.manifest.neighbourhoods ?? [];
    expect(names.length).toBeGreaterThan(0);
    expect(bundle.neighbourhoodOf).toHaveLength(bundle.cells.length);
    const first = neighbourhoodAt(bundle, 0);
    expect(first?.name).toBeTruthy();
    expect(first?.area).toBeTruthy();
    expect(neighbourhoodAt(bundle, bundle.cells.length)).toBeNull(); // no such cell
    const positions = new Set(bundle.neighbourhoodOf);
    expect(
      [...positions].every((p) => p === null || (p >= 0 && p < names.length)),
    ).toBe(true);
  });

  it("holds the cells as H3 indexes, sorted", async () => {
    const { cells } = await loadBundle("/bundles", "london", fixtureFetch);
    expect(cells.every((cell) => /^[0-9a-f]{15}$/.test(cell))).toBe(true);
    expect([...cells].sort()).toEqual(cells);
  });

  it("names the datasets and their attribution, for the interface to show", async () => {
    const { manifest } = await loadBundle("/bundles", "london", fixtureFetch);
    const ptal = manifest.datasets.find((dataset) => dataset.id === "tfl-ptal");
    expect(ptal?.attribution).toContain("Transport for London");
  });

  it("says what went wrong when a file is missing", async () => {
    await expect(
      loadBundle("/nowhere", "london", fixtureFetch),
    ).rejects.toThrow(/latest\.json/);
  });

  it("refuses a manifest of a format it does not know", async () => {
    const odd = async (url: string | URL | Request): Promise<Response> => {
      const path = String(url);
      if (path.endsWith("latest.json"))
        return new Response('{"version":"abc"}');
      return new Response(JSON.stringify({ format_version: 2 }));
    };
    await expect(loadBundle("/bundles", "london", odd)).rejects.toThrow(
      /format/,
    );
  });
});

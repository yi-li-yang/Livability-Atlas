import { expect, type Locator, type Page, test } from "@playwright/test";
import { PNG } from "pngjs";
import { CELL_OPACITY, scoreToColour } from "../src/features/map/colour";
import { clearOfPanel } from "./clip";

// Every colour the map can give a cell: the palette, blended between its stops.
const COLOURS = Array.from({ length: 101 }, (_, i) => scoreToColour(i / 100));

test("the page shows a map of London under its heading", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Livability Atlas" }),
  ).toBeVisible();
  await expect(page.getByTestId("map").locator("canvas").first()).toBeVisible();
});

test("the map's worker script is served as JavaScript, so that the map can draw", async ({
  page,
}) => {
  const worker = page.waitForResponse((response) =>
    response.url().includes("maplibre-gl-worker"),
  );
  await page.goto("/");
  expect((await worker).headers()["content-type"]).toMatch(/javascript/);
});

test("the app loads the data bundle, and says what it is and where it comes from", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByTestId("map")).toHaveAttribute(
    "data-cells",
    /^[1-9]\d*$/,
  );
  await expect(
    page.getByRole("region", { name: "Legend" }).getByText("Worse"),
  ).toBeVisible();
  // The credits are behind "About the data", each line once.
  const sources = page.getByRole("region", { name: "Data sources" });
  await expect(sources.getByText(/Transport for London/)).toBeHidden();
  await sources.getByText("About the data").click();
  await expect(sources.getByText(/Transport for London/)).toBeVisible();
  await expect(sources.getByText(/data\.police\.uk/)).toBeVisible();
  // And where the user's own settings go: nowhere.
  await expect(sources.getByText(/stay in your browser/)).toBeVisible();
  await expect(sources.getByText(/sent to no server/)).toBeVisible();
  const lines = await sources.locator("p").allTextContents();
  expect(new Set(lines).size).toBe(lines.length);
  await expect(page.getByRole("alert")).toHaveCount(0);
});

test("the app says so when the data cannot be loaded", async ({ page }) => {
  await page.route("**/bundles/**", (route) => route.fulfill({ status: 404 }));
  await page.goto("/");
  await expect(page.getByRole("alert")).toHaveText(/could not be loaded/);
});

const HEX_LAYER = '[data-testid="map"] canvas:not(.maplibregl-canvas)';

/**
 * Whether `after` is a colour of the palette drawn over `before` at some opacity: it fits the colour's blend with `before` at the best opacity, which must be a plausible one. The opacity is
 * fitted, since what deck.gl composites is not exactly the opacity that the layer is given.
 */
function fitsPalette(after: number[], before: number[]): boolean {
  return COLOURS.some((colour) => {
    let along = 0;
    let norm = 0;
    for (let k = 0; k < 3; k++) {
      along += (after[k] - before[k]) * (colour[k] - before[k]);
      norm += (colour[k] - before[k]) ** 2;
    }
    if (norm === 0) return false;
    const alpha = along / norm;
    if (alpha < CELL_OPACITY - 0.15 || alpha > 1) return false;
    return after.every(
      (c, k) =>
        Math.abs(c - (before[k] + alpha * (colour[k] - before[k]))) <= 8,
    );
  });
}

/**
 * Screenshots the map with the hex layer shown, hidden and shown again, and compares them. Returns how many
 * pixels the layer changed, and how many of those are a palette colour drawn at the cells'
 * opacity over the pixel that was there before.
 */
async function hexLayerPixels(
  page: Page,
  map: Locator,
): Promise<{ changed: number; explained: number }> {
  const show = (visible: boolean) =>
    page.evaluate(
      ([selector, value]) => {
        for (const canvas of document.querySelectorAll<HTMLElement>(selector)) {
          canvas.style.visibility = value;
        }
      },
      [HEX_LAYER, visible ? "visible" : "hidden"],
    );
  const clip = await clearOfPanel(page, map);
  await show(true);
  const withCells = PNG.sync.read(await page.screenshot({ clip }));
  await show(false);
  const without = PNG.sync.read(await page.screenshot({ clip }));
  await show(true);
  const again = PNG.sync.read(await page.screenshot({ clip }));

  let changed = 0;
  let explained = 0;
  for (let i = 0; i < withCells.data.length; i += 4) {
    const after = [
      withCells.data[i],
      withCells.data[i + 1],
      withCells.data[i + 2],
    ];
    const before = [without.data[i], without.data[i + 1], without.data[i + 2]];
    if (after.every((c, k) => Math.abs(c - before[k]) < 4)) continue;
    // A pixel that is not the same in two shots with the cells shown is still changing, such as
    // a basemap tile that arrives meanwhile (it did, on a slow runner): it says nothing of the cells.
    if (after.some((c, k) => Math.abs(c - again.data[i + k]) >= 4)) continue;
    changed++;
    if (fitsPalette(after, before)) explained++;
  }
  return { changed, explained };
}

test("the hex cells are drawn on the map, in the palette's colours", async ({
  page,
}) => {
  await page.goto("/");
  const map = page.getByTestId("map");
  await expect(map).toHaveAttribute("data-cells", /^[1-9]\d*$/);
  await page.waitForLoadState("networkidle");
  await expect
    .poll(async () => (await hexLayerPixels(page, map)).changed, {
      timeout: 20_000,
    })
    .toBeGreaterThan(2000);
  const { changed, explained } = await hexLayerPixels(page, map);
  expect(explained / changed).toBeGreaterThan(0.9);
});

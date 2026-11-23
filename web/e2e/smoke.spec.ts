import { expect, type Locator, type Page, test } from "@playwright/test";
import { PNG } from "pngjs";
import {
  CELL_OPACITY,
  LAND_COLOURS,
  scoreToColour,
} from "../src/features/map/colour";
import { clearCentre, clearOfPanel } from "./clip";

// Every colour the map can give a cell: the palette, blended between its stops.
const COLOURS = Array.from({ length: 101 }, (_, i) => scoreToColour(i / 100));

const rgb = (hex: string) =>
  [1, 3, 5].map((i) => Number.parseInt(hex.slice(i, i + 2), 16));

// The colours of bare land under the cells: the land use and the background. Elsewhere a road, a
// river or a name's halo is drawn over the cells and only partly shows them, so only these pixels
// say how the cells are coloured. The match is exact, or a halo over bare land would pass for it.
const LAND = [...Object.values(LAND_COLOURS).map(rgb), [242, 243, 240]];
const onLand = (pixel: number[]) =>
  LAND.some((land) => land.every((c, k) => Math.abs(c - pixel[k]) <= 1));

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

/** Waits for the map to draw a frame or two after a change. */
async function settle(page: Page): Promise<void> {
  await page.evaluate(
    () =>
      new Promise<void>((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
      ),
  );
  await page.waitForTimeout(300);
}

/**
 * Screenshots the map with the cells shown, faded out with the opacity slider, and shown again,
 * and compares them. The cells are drawn inside the map, under its roads and names (D23), so the
 * slider is the way to take them away. Returns how many pixels the cells changed, how many of those
 * had bare land under them, and how many of those are a palette colour drawn at the cells' opacity
 * over the land.
 */
async function hexLayerPixels(
  page: Page,
  map: Locator,
): Promise<{ changed: number; land: number; explained: number }> {
  const slider = page.getByRole("slider", { name: "Cell opacity" });
  const show = async (visible: boolean) => {
    await slider.fill(visible ? String(Math.round(CELL_OPACITY * 100)) : "0");
    await settle(page);
  };
  const clip = await clearOfPanel(page, map);
  await show(true);
  const withCells = PNG.sync.read(await page.screenshot({ clip }));
  await show(false);
  const without = PNG.sync.read(await page.screenshot({ clip }));
  await show(true);
  const again = PNG.sync.read(await page.screenshot({ clip }));

  let changed = 0;
  let land = 0;
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
    if (!onLand(before)) continue;
    land++;
    if (fitsPalette(after, before)) explained++;
  }
  return { changed, land, explained };
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
  const { land, explained } = await hexLayerPixels(page, map);
  expect(land).toBeGreaterThan(2000);
  expect(explained / land).toBeGreaterThan(0.9);
});

test("the hex cells are drawn while the map's tiles still load, as on a slow network", async ({
  page,
}) => {
  // deck.gl adds its layers only when MapLibre says the style is loaded, which it says only once
  // every tile has loaded: the cells must not wait for that (HexMap's withStyleLoaded).
  await page.route(/\.pbf(\?|$)/, async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 60_000));
    await route.continue().catch(() => {});
  });
  await page.goto("/");
  const map = page.getByTestId("map");
  await expect(map).toHaveAttribute("data-cells", /^[1-9]\d*$/);
  await expect
    .poll(async () => (await hexLayerPixels(page, map)).land, {
      timeout: 20_000,
    })
    .toBeGreaterThan(2000);
});

test("one click on a cell of a still map opens its reasons", async ({
  page,
}) => {
  // With deck.gl's own onClick, interleaved with MapLibre, a click on the full London bundle was
  // lost (HexMap now picks it from MapLibre's click). The small fixture bundle did not show that
  // fault, so this test guards the click path, not that fault itself.
  await page.goto("/");
  const map = page.getByTestId("map");
  await expect(map).toHaveAttribute("data-cells", /^[1-9]\d*$/);
  await page.waitForLoadState("networkidle");
  const { x, y } = await clearCentre(page, map);
  await expect(async () => {
    await page.mouse.move(x - 5, y - 5);
    await page.mouse.move(x, y);
    await expect(page.getByTestId("quick-look")).toBeVisible({ timeout: 500 });
  }).toPass({ timeout: 10_000 });
  // Change the cells once, as a user does, let the map come to rest, then click once.
  const slider = page.getByRole("slider", { name: "Cell opacity" });
  await slider.fill("0");
  await slider.fill(String(Math.round(CELL_OPACITY * 100)));
  await page.mouse.move(x - 5, y - 5);
  await page.mouse.move(x, y);
  await page.waitForTimeout(1500);
  await page.mouse.click(x, y);
  await expect(
    page.getByRole("complementary", { name: "Why this score" }),
  ).toBeVisible({ timeout: 3000 });
});

import { expect, type Page, test } from "@playwright/test";
import { PNG } from "pngjs";
import { clearOfPanel } from "./clip";

async function openApp(page: Page) {
  await page.goto("/");
  await expect(page.getByTestId("map")).toHaveAttribute(
    "data-cells",
    /^[1-9]\d*$/,
  );
  await expect(page.getByTestId("factor-tree")).toBeVisible();
  await page.waitForLoadState("networkidle");
}

const tile = (page: Page, id: string) =>
  page.locator(`[data-testid="factor-tile"][data-factor="${id}"]`);

const share = async (page: Page, id: string) =>
  Number(await tile(page, id).getAttribute("data-share"));

/** How many pixels of the map differ between two screenshots. */
function differing(before: Buffer, after: Buffer): number {
  const a = PNG.sync.read(before);
  const b = PNG.sync.read(after);
  let count = 0;
  for (let i = 0; i < a.data.length; i += 4) {
    const gap =
      Math.abs(a.data[i] - b.data[i]) +
      Math.abs(a.data[i + 1] - b.data[i + 1]) +
      Math.abs(a.data[i + 2] - b.data[i + 2]);
    if (gap > 24) count++;
  }
  return count;
}

test("the factor tree shows each factor with its share of the weight and a slider", async ({
  page,
}) => {
  await openApp(page);
  // Only the essentials count at the start (D14), each at weight 3, so the three that hold one
  // have a third each. Health care holds none, so it starts under "Not counted".
  for (const [id, want] of [
    ["transport", 1 / 3],
    ["environment", 1 / 3],
    ["safety", 1 / 3],
  ] as const) {
    expect(await share(page, id)).toBeCloseTo(want, 3);
  }
  await expect(tile(page, "health-care")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Count Health care" }),
  ).toBeVisible();
  await expect(
    page.getByRole("slider", { name: "Weight of Transport" }),
  ).toHaveValue("3");
  await expect(
    page.getByRole("slider", { name: "Weight of Environment" }),
  ).toHaveValue("3");
});

test("moving a slider resizes the factor at once, and the others shrink or grow to match", async ({
  page,
}) => {
  await openApp(page);
  const before = await share(page, "transport");
  await page.getByRole("slider", { name: "Weight of Transport" }).fill("5");
  await expect.poll(() => share(page, "transport")).toBeGreaterThan(before);
  expect(await share(page, "transport")).toBeCloseTo(5 / 11, 3);
  expect(await share(page, "environment")).toBeCloseTo(3 / 11, 3);
});

test("a factor at weight 0 leaves the drawing for the not counted list, and can come back", async ({
  page,
}) => {
  await openApp(page);
  const slider = page.getByRole("slider", { name: "Weight of Transport" });
  await slider.fill("0");
  await slider.blur();
  await expect(tile(page, "transport")).toHaveCount(0);
  const notCounted = page.getByRole("heading", { name: "Not counted" });
  await expect(notCounted).toBeVisible();
  expect(await share(page, "environment")).toBeCloseTo(3 / 6, 3);

  await page.getByRole("button", { name: "Count Transport" }).click();
  await expect(tile(page, "transport")).toHaveCount(1);
  // Health care starts out not counted, so the list stays, without Transport.
  await expect(
    page.getByRole("button", { name: "Count Transport" }),
  ).toHaveCount(0);
  expect(await share(page, "transport")).toBeCloseTo(1 / 3, 3);
});

test("a weight moved to 0 keeps its row and the focus until the slider is let go", async ({
  page,
}) => {
  await openApp(page);
  const slider = page.getByRole("slider", { name: "Weight of Transport" });
  await slider.focus();
  await page.keyboard.press("ArrowLeft");
  await page.keyboard.press("ArrowLeft");
  await page.keyboard.press("ArrowLeft");
  await expect(slider).toHaveValue("0");
  await expect(slider).toBeFocused();
  // The drawing leaves it out at once; its row says so and stays.
  await expect(tile(page, "transport")).toHaveCount(0);
  await expect(
    page.getByText("Not counted now. Move it up to count it."),
  ).toBeVisible();
  await expect(
    page
      .getByRole("status")
      .filter({ hasText: "Transport is not counted now." }),
  ).toHaveCount(1);
  await expect(
    page.getByRole("button", { name: "Count Transport" }),
  ).toHaveCount(0);

  // Back up again before letting go: it counts, and never left.
  await page.keyboard.press("ArrowRight");
  await expect(tile(page, "transport")).toHaveCount(1);
  await page.keyboard.press("ArrowLeft");

  await page.keyboard.press("Tab");
  await expect(slider).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Count Transport" }),
  ).toBeVisible();
});

test("the boxes are a short strip, so the sliders come first", async ({
  page,
}) => {
  await openApp(page);
  const box = await page.getByTestId("factor-tree").boundingBox();
  if (!box) throw new Error("no drawing");
  expect(box.height).toBeLessThanOrEqual(box.width * 0.3);
});

test("clicking a box opens its factor, as its name does", async ({ page }) => {
  await openApp(page);
  await tile(page, "transport").click();
  await expect(tile(page, "getting-around")).toHaveCount(1);
});

test("with one factor counted, there is no picture of the shares", async ({
  page,
}) => {
  await openApp(page);
  await page.getByRole("button", { name: "Open Transport" }).click();
  const slider = page.getByRole("slider", { name: "Weight of Getting around" });
  await slider.fill("0");
  // While the slider is held, the picture stays, so the slider under the pointer does not move.
  await expect(slider).toBeFocused();
  await expect(page.getByTestId("factor-tile")).toHaveCount(1);
  await slider.blur();
  // Only travel time to places counts at this level now: a picture of one share says nothing.
  await expect(page.getByTestId("factor-tile")).toHaveCount(0);
  await expect(
    page.getByRole("slider", { name: "Weight of Travel time to places" }),
  ).toBeVisible();
});

test("opening a factor shows its sub-factors, and the trail leads back", async ({
  page,
}) => {
  await openApp(page);
  await page.getByRole("button", { name: "Open Transport" }).click();
  await expect(tile(page, "transport")).toHaveCount(0);
  await expect(tile(page, "getting-around")).toHaveCount(1);
  // Transport has two sub-factors in the test bundle, at the same default weight.
  expect(await share(page, "getting-around")).toBeCloseTo(0.5, 3);
  await expect(
    page.getByRole("navigation", { name: "Where you are in the factors" }),
  ).toContainText("Transport");

  await page.getByRole("button", { name: "All factors" }).click();
  await expect(tile(page, "transport")).toHaveCount(1);
});

test("changing a weight recolours the map", async ({ page }) => {
  await openApp(page);
  const map = page.getByTestId("map");
  const clip = await clearOfPanel(page, map);
  const before = await page.screenshot({ clip });
  await page.getByRole("slider", { name: "Weight of Transport" }).fill("0");
  await page.getByRole("slider", { name: "Weight of Environment" }).fill("0");
  await expect
    .poll(async () => differing(before, await page.screenshot({ clip })), {
      timeout: 10_000,
    })
    .toBeGreaterThan(2000);
});

test("the panel and the legend are stacked above the hex cells, so none are drawn over them", async ({
  page,
}) => {
  await openApp(page);
  // The cells are drawn in the map's canvas (D23), which has no z-index of its own: it takes the
  // first one among its ancestors.
  const stacking = await page.evaluate(() => {
    const zOf = (element: Element | null): number => {
      for (let e = element; e; e = e.parentElement) {
        const z = Number.parseInt(getComputedStyle(e).zIndex, 10);
        if (!Number.isNaN(z)) return z;
      }
      return 0;
    };
    const cells = document.querySelector('[data-testid="map"] canvas');
    return {
      cells: zOf(cells),
      panel: zOf(document.querySelector("aside")),
      legend: zOf(document.querySelector('section[aria-label="Legend"]')),
    };
  });
  expect(stacking.panel).toBeGreaterThan(stacking.cells);
  expect(stacking.legend).toBeGreaterThan(stacking.cells);
});

test("the colour strength slider fades the cells, so the map shows through", async ({
  page,
}) => {
  await openApp(page);
  const map = page.getByTestId("map");
  const slider = page.getByRole("slider", { name: "Colour strength" });
  await expect(slider).toHaveValue("80");
  const clip = await clearOfPanel(page, map);
  const normal = await page.screenshot({ clip });
  await slider.fill("0");
  await expect
    .poll(async () => differing(normal, await page.screenshot({ clip })), {
      timeout: 10_000,
    })
    .toBeGreaterThan(2000);
});

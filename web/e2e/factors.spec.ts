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
  // Every factor starts at weight 3, so the four that count have a quarter each.
  for (const [id, want] of [
    ["transport", 1 / 4],
    ["environment", 1 / 4],
    ["safety", 1 / 4],
    ["health-care", 1 / 4],
  ] as const) {
    expect(await share(page, id)).toBeCloseTo(want, 3);
  }
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
  expect(await share(page, "transport")).toBeCloseTo(5 / 14, 3);
  expect(await share(page, "environment")).toBeCloseTo(3 / 14, 3);
});

test("a factor at weight 0 leaves the drawing for the not counted list, and can come back", async ({
  page,
}) => {
  await openApp(page);
  await page.getByRole("slider", { name: "Weight of Transport" }).fill("0");
  await expect(tile(page, "transport")).toHaveCount(0);
  const notCounted = page.getByRole("heading", { name: "Not counted" });
  await expect(notCounted).toBeVisible();
  expect(await share(page, "environment")).toBeCloseTo(3 / 9, 3);

  await page.getByRole("button", { name: "Count Transport again" }).click();
  await expect(tile(page, "transport")).toHaveCount(1);
  // Community and people starts out not counted, so the list stays, without Transport.
  await expect(
    page.getByRole("button", { name: "Count Transport again" }),
  ).toHaveCount(0);
  expect(await share(page, "transport")).toBeCloseTo(1 / 4, 3);
});

test("opening a factor shows its sub-factors, and the trail leads back", async ({
  page,
}) => {
  await openApp(page);
  await page.getByRole("button", { name: "Open Transport" }).click();
  await expect(tile(page, "transport")).toHaveCount(0);
  await expect(tile(page, "getting-around")).toHaveCount(1);
  expect(await share(page, "getting-around")).toBeCloseTo(1, 3);
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
  // deck.gl's canvas has no z-index of its own: it takes the first one among its ancestors.
  const stacking = await page.evaluate(() => {
    const zOf = (element: Element | null): number => {
      for (let e = element; e; e = e.parentElement) {
        const z = Number.parseInt(getComputedStyle(e).zIndex, 10);
        if (!Number.isNaN(z)) return z;
      }
      return 0;
    };
    const cells = document.querySelector(
      '[data-testid="map"] canvas:not(.maplibregl-canvas)',
    );
    return {
      cells: zOf(cells),
      panel: zOf(document.querySelector("aside")),
      legend: zOf(document.querySelector('section[aria-label="Legend"]')),
    };
  });
  expect(stacking.panel).toBeGreaterThan(stacking.cells);
  expect(stacking.legend).toBeGreaterThan(stacking.cells);
});

test("the cell opacity slider fades the cells, so the map shows through", async ({
  page,
}) => {
  await openApp(page);
  const map = page.getByTestId("map");
  const slider = page.getByRole("slider", { name: "Cell opacity" });
  await expect(slider).toHaveValue("50");
  const clip = await clearOfPanel(page, map);
  const normal = await page.screenshot({ clip });
  await slider.fill("0");
  await expect
    .poll(async () => differing(normal, await page.screenshot({ clip })), {
      timeout: 10_000,
    })
    .toBeGreaterThan(2000);
});

import { expect, type Page, test } from "@playwright/test";

// A phone held upright. Below 768 px wide the panels become sheets (docs/specs/2026-10-29-phone-layout.md).
test.use({ viewport: { width: 390, height: 844 }, hasTouch: true });

/** Opens the app with every factor counted ("Everything, equally"), as these tests use them all. */
async function openApp(page: Page) {
  await page.goto("/#v=2&s=all");
  const map = page.getByTestId("map");
  await expect(map).toHaveAttribute("data-cells", /^[1-9]\d*$/);
  await page.waitForLoadState("networkidle");
  const box = await map.boundingBox();
  const top = await page.getByRole("region", { name: "Legend" }).boundingBox();
  const bar = await page
    .getByRole("complementary", { name: "Your preferences" })
    .boundingBox();
  if (!box || !top || !bar) throw new Error("the map is not shown");
  // The middle of the map between the legend and the sheet's bar, where the app puts London's
  // centre (the map keeps clear of the panels over it).
  return {
    box,
    x: box.x + box.width / 2,
    y: (top.y + top.height + bar.y) / 2,
  };
}

const sheet = (page: Page) =>
  page.getByRole("complementary", { name: "Your preferences" });
const handle = (page: Page) =>
  page.getByRole("button", { name: "What matters to you" });
const legend = (page: Page) => page.getByRole("region", { name: "Legend" });
const reasons = (page: Page) =>
  page.getByRole("complementary", { name: "Why this score" });
const tile = (page: Page, id: string) =>
  page.locator(`[data-testid="factor-tile"][data-factor="${id}"]`);

/** Whether two boxes share any area. */
const overlap = (
  a: { x: number; y: number; width: number; height: number },
  b: { x: number; y: number; width: number; height: number },
): boolean =>
  a.x < b.x + b.width &&
  b.x < a.x + a.width &&
  a.y < b.y + b.height &&
  b.y < a.y + a.height;

test("the preferences are a sheet along the bottom, closed at first, so the map shows", async ({
  page,
}) => {
  const { box: map } = await openApp(page);
  const closed = await sheet(page).boundingBox();
  if (!closed) throw new Error("the sheet is not shown");
  expect(closed.height).toBeLessThan(80);
  expect(closed.width).toBeGreaterThan(380);
  expect(
    Math.abs(closed.y + closed.height - (map.y + map.height)),
  ).toBeLessThan(2);
  await expect(handle(page)).toHaveAttribute("aria-expanded", "false");
  await expect(
    page.getByRole("slider", { name: "Weight of Transport" }),
  ).toBeHidden();
});

test("opening the sheet shows the factors and the sliders work, and closing keeps where the user was", async ({
  page,
}) => {
  const { box: map } = await openApp(page);
  await handle(page).tap();
  await expect(handle(page)).toHaveAttribute("aria-expanded", "true");
  const slider = page.getByRole("slider", { name: "Weight of Transport" });
  await expect(slider).toBeVisible();
  const open = await sheet(page).boundingBox();
  if (!open) throw new Error("the sheet is not shown");
  expect(open.height).toBeLessThanOrEqual(map.height * 0.66 + 1);

  await slider.fill("5");
  await expect
    .poll(async () =>
      Number(await tile(page, "transport").getAttribute("data-share")),
    )
    .toBeCloseTo(5 / 14, 2);

  await page.getByRole("button", { name: "Open Transport" }).tap();
  await expect(tile(page, "getting-around")).toHaveCount(1);
  await handle(page).tap(); // close
  await expect(handle(page)).toHaveAttribute("aria-expanded", "false");
  await expect(slider).toBeHidden();
  await handle(page).tap(); // open again, where it was
  await expect(tile(page, "getting-around")).toHaveCount(1);
  await expect(tile(page, "transport")).toHaveCount(0);
});

test("the sheet opens half-way, with the sliders in view and the map above, and opens further on Show more", async ({
  page,
}) => {
  const { box: map } = await openApp(page);
  await handle(page).tap();
  const half = await sheet(page).boundingBox();
  if (!half) throw new Error("the sheet is not shown");
  // At least half of the map stays in view, so a weight's effect on the colours shows.
  expect(half.height).toBeLessThanOrEqual(map.height * 0.46);
  expect(half.y).toBeGreaterThan(map.y + map.height * 0.5);
  const slider = page.getByRole("slider", { name: "Weight of Transport" });
  await expect(slider).toBeInViewport();
  // A finger's target: at least WCAG 2.2's 24 px.
  expect((await slider.boundingBox())?.height).toBeGreaterThanOrEqual(24);

  await page.getByRole("button", { name: "Show more of the panel" }).tap();
  const full = await sheet(page).boundingBox();
  if (!full) throw new Error("the sheet is not shown");
  expect(full.height).toBeGreaterThan(half.height + 40);
  await page.getByRole("button", { name: "Show less of the panel" }).tap();
  await expect
    .poll(async () => (await sheet(page).boundingBox())?.height)
    .toBeLessThanOrEqual(half.height + 1);

  await handle(page).tap();
  await expect(handle(page)).toHaveAttribute("aria-expanded", "false");
});

test("the legend is across the top of the map and never meets the sheet", async ({
  page,
}) => {
  const { box: map } = await openApp(page);
  const bar = await legend(page).boundingBox();
  if (!bar) throw new Error("the legend is not shown");
  expect(bar.y - map.y).toBeLessThan(16);
  expect(bar.width).toBeGreaterThan(map.width - 32);
  await expect(
    page.getByRole("combobox", { name: "Show on the map" }),
  ).toBeVisible();
  // The opacity slider is behind "Colours".
  const opacity = page.getByRole("slider", { name: "Colour strength" });
  await expect(opacity).toBeHidden();
  await page.locator("summary", { hasText: "Colours" }).tap();
  await expect(opacity).toBeVisible();

  await handle(page).tap();
  const open = await sheet(page).boundingBox();
  const top = await legend(page).boundingBox();
  if (!open || !top) throw new Error("the sheet or the legend is not shown");
  expect(overlap(open, top)).toBe(false);
});

test("the basemap's credit stays in view, clear of the closed sheet", async ({
  page,
}) => {
  await openApp(page);
  const credit = page.locator(".maplibregl-ctrl-attrib");
  await expect(credit).toBeVisible();
  const [box, bar] = await Promise.all([
    credit.boundingBox(),
    sheet(page).boundingBox(),
  ]);
  if (!box || !bar) throw new Error("the credit or the sheet is not shown");
  expect(overlap(box, bar)).toBe(false);
});

test("tapping a cell shows the reasons as a sheet over the preferences, and Close brings them back", async ({
  page,
}) => {
  const { box: map, x, y } = await openApp(page);
  await expect(async () => {
    await page.touchscreen.tap(x, y);
    await expect(reasons(page)).toBeVisible({ timeout: 700 });
  }).toPass({ timeout: 15_000 });
  const sheetBox = await reasons(page).boundingBox();
  if (!sheetBox) throw new Error("the reasons are not shown");
  expect(sheetBox.width).toBeGreaterThan(380);
  expect(
    Math.abs(sheetBox.y + sheetBox.height - (map.y + map.height)),
  ).toBeLessThan(2);
  expect(sheetBox.height).toBeLessThanOrEqual(map.height * 0.7 + 1);
  await expect(sheet(page)).toBeHidden();

  await reasons(page).getByRole("button", { name: "Close" }).tap();
  await expect(reasons(page)).toHaveCount(0);
  await expect(sheet(page)).toBeVisible();
});

test("a tap opens a short peek that keeps the map in sight, and Show the reasons opens them in full", async ({
  page,
}) => {
  const { box: map, x, y } = await openApp(page);
  await expect(async () => {
    await page.touchscreen.tap(x, y);
    await expect(reasons(page)).toBeVisible({ timeout: 700 });
  }).toPass({ timeout: 15_000 });
  const show = reasons(page).getByRole("button", { name: "Show the reasons" });
  await expect(show).toBeVisible();
  await expect(reasons(page)).toContainText("out of 100");
  // The peek leaves most of the map in sight; the factors' bars wait for "Show the reasons".
  const peek = await reasons(page).boundingBox();
  if (!peek) throw new Error("the reasons are not shown");
  expect(peek.height).toBeLessThan(map.height * 0.45);
  await expect(reasons(page).getByTestId("score-bar")).toHaveCount(0);

  await show.tap();
  await expect(show).toHaveCount(0);
  await expect(reasons(page).getByTestId("score-bar").first()).toBeVisible();
});

test("there is no quick look on a phone, where there is no hover", async ({
  page,
}) => {
  const { x, y } = await openApp(page);
  await page.mouse.move(x - 5, y - 5);
  await page.mouse.move(x, y);
  await page.waitForTimeout(1000);
  await expect(page.getByTestId("quick-look")).toHaveCount(0);
});

test("the basemap's credit is also in About the data, which no sheet covers", async ({
  page,
}) => {
  await openApp(page);
  await handle(page).tap(); // the open sheet covers the map's own credit
  await page.getByText("About the data", { exact: true }).tap();
  await expect(
    page.getByRole("region", { name: "Data sources" }),
  ).toContainText("OpenFreeMap");
  await expect(
    page.getByRole("region", { name: "Data sources" }),
  ).toContainText("OpenStreetMap");
});

test("choosing a neighbourhood from the list shuts the sheet, so the map shows where it went", async ({
  page,
}) => {
  await openApp(page);
  await handle(page).tap();
  await page.getByText("Top neighbourhoods", { exact: true }).tap();
  await page
    .getByTestId("top-neighbourhoods")
    .getByRole("button")
    .first()
    .tap();
  await expect(reasons(page)).toBeVisible();
  await reasons(page).getByRole("button", { name: "Close" }).tap();
  await expect(handle(page)).toHaveAttribute("aria-expanded", "false");
});

test.describe("a phone held sideways", () => {
  test.use({ viewport: { width: 667, height: 375 }, hasTouch: true });

  test("the legend, the sheet and the reasons do not meet, and the map keeps room", async ({
    page,
  }) => {
    const { box: map, x, y } = await openApp(page);
    const top = await legend(page).boundingBox();
    if (!top) throw new Error("the legend is not shown");
    expect(top.height).toBeLessThan(map.height * 0.4);

    await handle(page).tap();
    const open = await sheet(page).boundingBox();
    if (!open) throw new Error("the sheet is not shown");
    expect(overlap(open, top)).toBe(false);
    await handle(page).tap();

    await expect(async () => {
      await page.touchscreen.tap(x, y);
      await expect(reasons(page)).toBeVisible({ timeout: 700 });
    }).toPass({ timeout: 15_000 });
    const sheetBox = await reasons(page).boundingBox();
    if (!sheetBox) throw new Error("the reasons are not shown");
    expect(overlap(sheetBox, top)).toBe(false);
  });
});

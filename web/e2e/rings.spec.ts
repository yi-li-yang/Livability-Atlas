import { expect, type Page, test } from "@playwright/test";

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
const part = (page: Page, id: string) =>
  page.locator(`[data-testid="factor-part"][data-factor="${id}"]`);
const share = async (page: Page, id: string) =>
  Number(await tile(page, id).getAttribute("data-share"));

const boxes = (page: Page) =>
  page.getByRole("button", { name: "Boxes", exact: true });
const rings = (page: Page) =>
  page.getByRole("button", { name: "Rings", exact: true });

// A click or a pointer on an arc is sent to the arc itself: the middle of an arc's box is often in
// the hole of the ring, where Playwright's own pointer would hit another shape.
const click = (arc: ReturnType<typeof tile>) => arc.dispatchEvent("click");

test("the factors are drawn as boxes first, and a switch draws them as rings", async ({
  page,
}) => {
  await openApp(page);
  await expect(boxes(page)).toHaveAttribute("aria-pressed", "true");
  await expect(rings(page)).toHaveAttribute("aria-pressed", "false");
  await expect(page.getByTestId("factor-rings")).toHaveCount(0);

  const inBoxes = [
    await share(page, "transport"),
    await share(page, "environment"),
  ];
  await rings(page).click();
  await expect(rings(page)).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByTestId("factor-rings")).toBeVisible();
  // Every factor starts at weight 3, so the four that count have a quarter each.
  await expect(page.getByTestId("factor-tile")).toHaveCount(4);
  // An arc with room for it says its share, which is a quarter.
  await expect(
    page.getByTestId("factor-rings").getByText("25%", { exact: true }).first(),
  ).toBeVisible();
  expect([
    await share(page, "transport"),
    await share(page, "environment"),
  ]).toEqual(inBoxes);

  await boxes(page).click();
  await expect(page.getByTestId("factor-rings")).toHaveCount(0);
  expect(await share(page, "transport")).toBeCloseTo(1 / 4, 3);
});

test("a slider resizes an arc at once, and a factor at weight 0 leaves the rings", async ({
  page,
}) => {
  await openApp(page);
  await rings(page).click();
  await page.getByRole("slider", { name: "Weight of Transport" }).fill("5");
  await expect
    .poll(() => share(page, "transport"))
    .toBeGreaterThan(1 / 4 + 0.01);
  expect(await share(page, "transport")).toBeCloseTo(5 / 14, 3);
  expect(await share(page, "environment")).toBeCloseTo(3 / 14, 3);

  await page.getByRole("slider", { name: "Weight of Transport" }).fill("0");
  await expect(tile(page, "transport")).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Not counted" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Count Transport again" }).click();
  await expect(tile(page, "transport")).toHaveCount(1);
});

test("the sub-factors of each factor are the arcs outside it, sharing its angle", async ({
  page,
}) => {
  await openApp(page);
  await rings(page).click();
  // Transport has one sub-factor in the test bundle, which takes all of it.
  await expect(part(page, "getting-around")).toHaveAttribute(
    "data-parent",
    "transport",
  );
  expect(
    Number(await part(page, "getting-around").getAttribute("data-share")),
  ).toBeCloseTo(1, 3);
  // Each factor's parts add up to the whole of it.
  const sums = await page.evaluate(() => {
    const totals = new Map<string, number>();
    for (const arc of document.querySelectorAll(
      '[data-testid="factor-part"]',
    )) {
      const parent = arc.getAttribute("data-parent") ?? "";
      totals.set(
        parent,
        (totals.get(parent) ?? 0) + Number(arc.getAttribute("data-share")),
      );
    }
    return [...totals.values()];
  });
  expect(sums.length).toBeGreaterThan(2);
  for (const sum of sums) expect(sum).toBeCloseTo(1, 3);
});

/** Where an arc starts, in turns clockwise from the top, read from the start of its path. */
async function startsAt(arc: ReturnType<typeof tile>): Promise<number> {
  const d = (await arc.getAttribute("d")) ?? "";
  const [, x, y] = d.match(/^M (-?[\d.]+) (-?[\d.]+)/) ?? [];
  const turns = Math.atan2(Number(x), -Number(y)) / (2 * Math.PI);
  return turns < 0 ? turns + 1 : turns;
}

test("an outer arc starts where its factor's arc starts", async ({ page }) => {
  await openApp(page);
  await rings(page).click();
  // The first sub-factor of each factor begins at the angle that the factor begins at.
  for (const [factor, first] of [
    ["transport", "getting-around"],
    ["environment", "green-space"],
    ["safety", "crime"],
  ] as const) {
    const outer = await startsAt(part(page, first));
    const inner = await startsAt(tile(page, factor));
    expect(Math.abs(outer - inner)).toBeLessThan(0.002);
  }
  // And the factors are not all drawn from the top: the arcs follow one another round the circle.
  expect(await startsAt(tile(page, "safety"))).toBeGreaterThan(0.1);
});

test("clicking an arc opens the factor, and the centre goes back up", async ({
  page,
}) => {
  await openApp(page);
  await rings(page).click();
  const trail = page.getByRole("navigation", {
    name: "Where you are in the factors",
  });
  const centre = page.getByTestId("factor-title");
  await expect(centre).toHaveAttribute("data-title", "All factors");

  await click(tile(page, "transport"));
  await expect(trail).toContainText("Transport");
  await expect(tile(page, "transport")).toHaveCount(0);
  await expect(tile(page, "getting-around")).toHaveCount(1);
  await expect(centre).toHaveAttribute("data-title", "Transport");

  await page.getByTestId("factor-centre").dispatchEvent("click");
  await expect(tile(page, "transport")).toHaveCount(1);
  await expect(centre).toHaveAttribute("data-title", "All factors");
  await expect(
    page.getByRole("button", { name: "All factors" }),
  ).toBeDisabled();
});

test("clicking an outer arc opens its factor and the sub-factor inside it", async ({
  page,
}) => {
  await openApp(page);
  await rings(page).click();
  const trail = page.getByRole("navigation", {
    name: "Where you are in the factors",
  });
  await click(part(page, "getting-around"));
  await expect(trail).toContainText("Transport");
  await expect(trail).toContainText("Getting around");
  // The measured indicators inside it are at the level below, and do not open.
  await expect(tile(page, "service-level")).toHaveCount(1);

  // The centre goes up one level, not to the top.
  await page.getByTestId("factor-centre").dispatchEvent("click");
  await expect(trail).toContainText("Transport");
  await expect(trail).not.toContainText("Getting around");
  await expect(tile(page, "getting-around")).toHaveCount(1);
});

test("pointing at an arc names it below the rings", async ({ page }) => {
  await openApp(page);
  await rings(page).click();
  await tile(page, "transport").dispatchEvent("mouseover");
  await expect(page.getByTestId("factor-rings").locator("..")).toContainText(
    "Transport: 25%",
  );
});

test("what the pointer named is forgotten when the level changes", async ({
  page,
}) => {
  await openApp(page);
  await rings(page).click();
  const caption = page.getByTestId("factor-rings").locator("..");
  await tile(page, "transport").dispatchEvent("mouseover");
  await expect(caption).toContainText("Transport: 25%");
  await click(tile(page, "transport"));
  await expect(tile(page, "getting-around")).toHaveCount(1);
  await expect(caption).not.toContainText("Transport: 25%");
});

test("the layout is remembered for the next visit, and no link carries it", async ({
  page,
}) => {
  await openApp(page);
  await rings(page).click();
  await page.reload();
  await expect(page.getByTestId("factor-tree")).toBeVisible();
  await expect(rings(page)).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByTestId("factor-rings")).toBeVisible();
  expect(new URL(page.url()).hash).not.toContain("rings");
});

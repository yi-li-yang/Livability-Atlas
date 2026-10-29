import { expect, type Page, test } from "@playwright/test";

/** Opens the app and returns the pixel at the middle of the map, which is over the fixture's cells. */
async function openOverCells(page: Page) {
  await page.goto("/");
  const map = page.getByTestId("map");
  await expect(map).toHaveAttribute("data-cells", /^[1-9]\d*$/);
  await page.waitForLoadState("networkidle");
  const box = await map.boundingBox();
  if (!box) throw new Error("the map is not shown");
  return { x: box.x + box.width / 2, y: box.y + box.height / 2, box };
}

test("hovering over a hex cell shows its score, rank, strengths and weakness", async ({
  page,
}) => {
  const { x, y } = await openOverCells(page);
  // The layer picks asynchronously: move until it has registered the cell.
  await expect(async () => {
    await page.mouse.move(x - 5, y - 5);
    await page.mouse.move(x, y);
    await expect(page.getByTestId("quick-look")).toBeVisible({ timeout: 500 });
  }).toPass({ timeout: 10_000 });
  const card = page.getByTestId("quick-look");
  await expect(card).toContainText("out of 100");
  await expect(card.locator("p").first()).toContainText(/\w, \w/); // the neighbourhood and its borough
  await expect(card).toContainText(/Rank [\d,]+ of [\d,]+/);
  await expect(card).toContainText("Click for the reasons");
});

test("clicking a hex cell says why it scores what it does, and the parts add up", async ({
  page,
}) => {
  const { x, y } = await openOverCells(page);
  const panel = page.getByRole("complementary", { name: "Why this score" });
  await expect(async () => {
    await page.mouse.move(x, y);
    await page.mouse.click(x, y);
    await expect(panel).toBeVisible({ timeout: 500 });
  }).toPass({ timeout: 10_000 });

  // The factors that count, each with what it adds.
  for (const name of ["Transport", "Environment", "Safety", "Health care"]) {
    await expect(
      panel.locator("summary", { hasText: name }).first(),
    ).toBeVisible();
  }
  const heading = await panel
    .getByText(/out of 100/)
    .first()
    .textContent();
  const score = Number(heading?.match(/(\d+)\s*out of 100/)?.[1]);
  const contributions = (
    await panel
      .locator(":scope > ul > li > details > summary")
      .allTextContents()
  ).map((text) => Number(text.match(/(\d+) of \d+ points/)?.[1]));
  expect(contributions).toHaveLength(4);
  const total = contributions.reduce((a, b) => a + b, 0);
  // Each is rounded to a whole number, so they add up to the score within the rounding.
  expect(Math.abs(total - score)).toBeLessThanOrEqual(2);

  // Opening a factor shows what is inside it.
  await panel.locator("summary", { hasText: "Transport" }).first().click();
  await expect(panel.getByText("Getting around")).toBeVisible();
  await panel.locator("summary", { hasText: "Getting around" }).first().click();
  await expect(panel.getByText("Service level", { exact: true })).toBeVisible();
  await expect(
    panel.getByText("Walk to the nearest station", { exact: true }),
  ).toBeVisible();
});

test("the reasons close with the button, with Escape, and by clicking where there is no cell", async ({
  page,
}) => {
  const { x, y, box } = await openOverCells(page);
  const panel = page.getByRole("complementary", { name: "Why this score" });
  const open = async () => {
    await expect(async () => {
      await page.mouse.move(x, y);
      await page.mouse.click(x, y);
      await expect(panel).toBeVisible({ timeout: 500 });
    }).toPass({ timeout: 10_000 });
  };

  await open();
  await panel.getByRole("button", { name: "Close" }).click();
  await expect(panel).toHaveCount(0);

  await open();
  await page.keyboard.press("Escape");
  await expect(panel).toHaveCount(0);

  await open();
  await page.mouse.click(box.x + box.width - 30, box.y + 30);
  await expect(panel).toHaveCount(0);
});

test("the details of a measured indicator give its value, its curve, its kind of evidence and its source", async ({
  page,
}) => {
  const { x, y } = await openOverCells(page);
  const panel = page.getByRole("complementary", { name: "Why this score" });
  await expect(async () => {
    await page.mouse.move(x, y);
    await page.mouse.click(x, y);
    await expect(panel).toBeVisible({ timeout: 500 });
  }).toPass({ timeout: 10_000 });

  const details = panel.getByTestId("evidence-service-level");
  await expect(details).toBeHidden(); // nothing of it shows until the factors are opened
  await panel.locator("summary", { hasText: "Transport" }).first().click();
  await panel.locator("summary", { hasText: "Getting around" }).first().click();
  await expect(details.getByText("Value here")).toBeHidden();
  await details.locator("summary").click();
  await expect(details.getByText(/^PTAL band /)).toBeVisible();
  await expect(details.getByText("How it scores")).toBeVisible();
  await expect(details.getByText(/Each value has its own score/)).toBeVisible();
  await expect(details.getByText("Measured directly")).toBeVisible();
  await expect(
    details.getByRole("link", { name: /PTAL/ }).first(),
  ).toHaveAttribute("href", /^https?:\/\//);
  await expect(details).toContainText("Transport for London");
  await expect(details).toContainText("Licence");
});

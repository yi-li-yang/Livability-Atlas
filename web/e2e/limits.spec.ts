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

/** Adds "Walk to the nearest station: at most `max`" through the form. */
async function addWalkLimit(page: Page, max: string) {
  await page.getByRole("button", { name: "Add a hard limit" }).click();
  await page
    .getByLabel("Measure")
    .selectOption({ label: "Walk to the nearest station" });
  await page.getByLabel("At most").check();
  await page.getByLabel(/^Value/).fill(max);
  await page.getByRole("button", { name: "Add limit" }).click();
}

const section = (page: Page) =>
  page.getByRole("region", { name: "Hard limits" });

test("a hard limit is added with a form, listed in words, and removed again", async ({
  page,
}) => {
  await openApp(page);
  await expect(section(page)).toContainText("greyed out and not ranked");
  await addWalkLimit(page, "5");
  await expect(section(page)).toContainText(
    "Walk to the nearest station: at most 5 minutes on foot",
  );
  await page
    .getByRole("button", {
      name: "Remove the limit on Walk to the nearest station",
    })
    .click();
  await expect(section(page)).not.toContainText("at most");
});

test("the form shows what the region's values are, and will not add a limit without a value", async ({
  page,
}) => {
  await openApp(page);
  await page.getByRole("button", { name: "Add a hard limit" }).click();
  await page
    .getByLabel("Measure")
    .selectOption({ label: "Walk to the nearest station" });
  await expect(section(page)).toContainText(
    /Across the region: .* to .*, middle/,
  );
  await expect(page.getByRole("button", { name: "Add limit" })).toBeDisabled();
  await page.getByLabel(/^Value/).fill("abc");
  await expect(page.getByRole("button", { name: "Add limit" })).toBeDisabled();
  await page.getByLabel(/^Value/).fill("4.5");
  await expect(page.getByRole("button", { name: "Add limit" })).toBeEnabled();
});

test("a limit on categories lists the values in the data", async ({ page }) => {
  await openApp(page);
  await page.getByRole("button", { name: "Add a hard limit" }).click();
  await page.getByLabel("Measure").selectOption({ label: "Service level" });
  const options = section(page).getByRole("checkbox");
  expect(await options.count()).toBeGreaterThan(2);
  await expect(page.getByRole("button", { name: "Add limit" })).toBeDisabled();
  await options.first().check();
  await page.getByRole("button", { name: "Add limit" }).click();
  await expect(section(page)).toContainText("Service level: only PTAL band");
});

test("cells that fail a limit are greyed out, and the map comes back when it is removed", async ({
  page,
}) => {
  await openApp(page);
  const clip = await clearOfPanel(page, page.getByTestId("map"));
  const area = () => page.screenshot({ clip });
  const before = await area();
  await addWalkLimit(page, "0.5"); // almost every cell is farther than half a minute
  await page.waitForTimeout(500);
  const limited = await area();
  expect(differs(before, limited)).toBeGreaterThan(1000);
  await page
    .getByRole("button", {
      name: "Remove the limit on Walk to the nearest station",
    })
    .click();
  await page.waitForTimeout(500);
  expect(differs(before, await area())).toBeLessThan(
    differs(before, limited) / 4,
  );
});

test("a limit is still there after a reload, and travels in the link", async ({
  page,
}) => {
  await openApp(page);
  await addWalkLimit(page, "6");
  await expect.poll(() => page.url()).toContain("l=station-proximity:max:6");
  await page.goto("/");
  await expect(page.getByTestId("factor-tree")).toBeVisible();
  await expect(section(page)).toContainText("at most 6 minutes on foot");
});

test("the quick look and the reasons say that a cell is left out, and give no rank", async ({
  page,
}) => {
  await page.goto("/#l=station-proximity:max:0.1");
  await expect(page.getByTestId("map")).toHaveAttribute(
    "data-cells",
    /^[1-9]\d*$/,
  );
  await page.waitForLoadState("networkidle");
  const box = await page.getByTestId("map").boundingBox();
  if (!box) throw new Error("the map is not shown");
  const x = box.x + box.width / 2;
  const y = box.y + box.height / 2;
  const panel = page.getByRole("complementary", { name: "Why this score" });
  await expect(async () => {
    await page.mouse.move(x - 5, y - 5);
    await page.mouse.move(x, y);
    await page.mouse.click(x, y);
    await expect(panel).toBeVisible({ timeout: 500 });
  }).toPass({ timeout: 10_000 });
  await expect(panel).toContainText("Left out of the ranking");
  await expect(panel).toContainText("Your hard limits");
  await expect(panel).toContainText("Failed");
  await expect(panel).not.toContainText(/rank [\d,]+ of/);
});

/** How many pixels differ between two screenshots of the part of the map the panel does not cover. */
function differs(a: Buffer, b: Buffer): number {
  const one = PNG.sync.read(a);
  const two = PNG.sync.read(b);
  let count = 0;
  for (let i = 0; i < one.data.length; i += 4) {
    const gap =
      Math.abs(one.data[i] - two.data[i]) +
      Math.abs(one.data[i + 1] - two.data[i + 1]) +
      Math.abs(one.data[i + 2] - two.data[i + 2]);
    if (gap > 24) count++;
  }
  return count;
}

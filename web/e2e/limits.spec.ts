import { expect, type Page, test } from "@playwright/test";
import { PNG } from "pngjs";
import { clearCentre, clearOfPanel } from "./clip";

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
  // A picture of the map once it has stopped changing: tiles and cells draw at their own pace.
  const settled = async (): Promise<Buffer> => {
    let last = await page.screenshot({ clip });
    for (let i = 0; i < 20; i++) {
      await page.waitForTimeout(250);
      const next = await page.screenshot({ clip });
      if (differs(last, next) < 50) return next;
      last = next;
    }
    return last;
  };
  const before = await settled();
  await addWalkLimit(page, "0.5"); // almost every cell is farther than half a minute
  await expect
    .poll(async () => differs(before, await page.screenshot({ clip })), {
      timeout: 10_000,
    })
    .toBeGreaterThan(1000);
  const limited = await settled();
  await page
    .getByRole("button", {
      name: "Remove the limit on Walk to the nearest station",
    })
    .click();
  await expect
    .poll(async () => differs(limited, await page.screenshot({ clip })), {
      timeout: 10_000,
    })
    .toBeGreaterThan(1000);
  const after = await settled();
  expect(differs(before, after)).toBeLessThan(differs(before, limited) / 4);
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
  const { x, y } = await clearCentre(page, page.getByTestId("map"));
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

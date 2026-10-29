import { expect, type Page, test } from "@playwright/test";

const tile = (page: Page, id: string) =>
  page.locator(`[data-testid="factor-tile"][data-factor="${id}"]`);

async function ready(page: Page) {
  await expect(page.getByTestId("map")).toHaveAttribute(
    "data-cells",
    /^[1-9]\d*$/,
  );
  await expect(page.getByTestId("factor-tree")).toBeVisible();
}

/** Opens Community and people, which starts out not counted, and picks a faith. */
async function pickHindu(page: Page) {
  await page.getByRole("button", { name: "Open Community and people" }).click();
  const picker = page.getByTestId("picker-faith");
  await picker.locator("summary").click();
  await picker.getByLabel("Hindu").check();
}

test("picking a faith counts the faith, which started out not counted", async ({
  page,
}) => {
  await page.goto("/");
  await ready(page);
  await expect(tile(page, "community-and-people")).toHaveCount(0);
  await pickHindu(page);
  await expect(tile(page, "faith")).toHaveCount(1);
  await expect(
    page.getByRole("slider", { name: "Weight of Faith" }),
  ).toHaveValue("3");
  await expect(
    page.getByTestId("picker-faith").locator("summary"),
  ).toContainText("Chosen: 1");
});

test("a choice stays in this browser and out of the link", async ({ page }) => {
  await page.goto("/");
  await ready(page);
  await pickHindu(page);
  await expect.poll(() => page.url()).toContain("w=");
  expect(page.url()).not.toContain("hindu");
  expect(page.url()).not.toContain("c=");

  // The same browser remembers it.
  await page.goto("/");
  await ready(page);
  await page.getByRole("button", { name: "Open Community and people" }).click();
  await expect(
    page.getByTestId("picker-faith").locator("summary"),
  ).toContainText("Chosen: 1");

  // A friend who opens the link has no choice of their own.
  const friend = await page.context().browser()?.newContext();
  if (!friend) throw new Error("no browser");
  const theirs = await friend.newPage();
  await theirs.goto(page.url());
  await ready(theirs);
  await theirs
    .getByRole("button", { name: "Open Community and people" })
    .click();
  await expect(
    theirs.getByTestId("picker-faith").locator("summary"),
  ).toHaveText(/Choose/);
  await friend.close();
});

test("clearing the last option stops counting the choice", async ({ page }) => {
  await page.goto("/");
  await ready(page);
  await pickHindu(page);
  await page.getByTestId("picker-faith").getByLabel("Hindu").uncheck();
  await expect(tile(page, "faith")).toHaveCount(0);
});

test("picking a faith recolours the map", async ({ page }) => {
  await page.goto("/");
  await ready(page);
  await page.waitForLoadState("networkidle");
  const before = await page.getByTestId("map").screenshot();
  await pickHindu(page);
  await page.waitForTimeout(400);
  const after = await page.getByTestId("map").screenshot();
  expect(after.equals(before)).toBe(false);
});

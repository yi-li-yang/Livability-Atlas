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

test("a weight the user sets is still there after a reload", async ({
  page,
}) => {
  await page.goto("/");
  await ready(page);
  await page.getByRole("slider", { name: "Weight of Transport" }).fill("5");
  // Drop the link's fragment, so that the reload can only read what the browser stored.
  await page.goto("/");
  await ready(page);
  await expect(
    page.getByRole("slider", { name: "Weight of Transport" }),
  ).toHaveValue("5");
});

test("the link carries the weights, so that sharing it shares them", async ({
  page,
}) => {
  await page.goto("/");
  await ready(page);
  await page.getByRole("slider", { name: "Weight of Environment" }).fill("1");
  await expect.poll(() => page.url()).toContain("w=environment:1");

  // A new browser context has no storage: the link alone must carry the weights.
  const friend = await page.context().browser()?.newContext();
  if (!friend) throw new Error("no browser");
  const theirs = await friend.newPage();
  await theirs.goto(page.url());
  await ready(theirs);
  await expect(
    theirs.getByRole("slider", { name: "Weight of Environment" }),
  ).toHaveValue("1");
  await friend.close();
});

test("a link can set a factor to weight 0", async ({ page }) => {
  await page.goto("/#w=transport:0");
  await ready(page);
  await expect(tile(page, "transport")).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Not counted" }),
  ).toBeVisible();
});

test("reset returns every weight to its default and clears the link", async ({
  page,
}) => {
  await page.goto("/#w=transport:0,environment:1");
  await ready(page);
  await page.getByRole("button", { name: "Reset to defaults" }).click();
  await expect(tile(page, "transport")).toHaveCount(1);
  await expect(
    page.getByRole("slider", { name: "Weight of Environment" }),
  ).toHaveValue("4");
  await expect(
    page.getByRole("button", { name: "Reset to defaults" }),
  ).toHaveCount(0);
  await expect.poll(() => page.url()).not.toContain("w=");
});

test("a broken link, or one for factors that do not exist, does not break the app", async ({
  page,
}) => {
  await page.goto("/#w=<script>:3,transport:99,nope:2,environment:2&f=ghost");
  await ready(page);
  await expect(
    page.getByRole("slider", { name: "Weight of Environment" }),
  ).toHaveValue("2");
  await expect(
    page.getByRole("slider", { name: "Weight of Transport" }),
  ).toHaveValue("3");
  await expect(page.getByRole("alert")).toHaveCount(0);
  // What the bundle does not have is dropped from the link.
  await expect.poll(() => page.url()).not.toContain("nope");
});

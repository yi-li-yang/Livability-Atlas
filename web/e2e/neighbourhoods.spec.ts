import { expect, test } from "@playwright/test";

async function open(page: import("@playwright/test").Page) {
  await page.goto("/");
  await expect(page.getByTestId("map")).toHaveAttribute(
    "data-cells",
    /^[1-9]\d*$/,
  );
  await expect(page.getByTestId("factor-tree")).toBeVisible();
  await page.waitForLoadState("networkidle");
}

test("the top neighbourhoods open from a link, by name and score", async ({
  page,
}) => {
  await open(page);
  const list = page.getByTestId("top-neighbourhoods");
  await expect(list.locator("summary")).toHaveText("Top neighbourhoods");
  await expect(list.getByRole("listitem")).toHaveCount(0); // closed: nothing shows
  await list.locator("summary").click();
  const items = list.getByRole("listitem");
  expect(await items.count()).toBeGreaterThan(0);
  const scores = (
    await items.locator("span.tabular-nums").allTextContents()
  ).map(Number);
  expect(scores.every((s) => s >= 0 && s <= 100)).toBe(true);
  expect([...scores].sort((a, b) => b - a)).toEqual(scores); // best first
});

test("choosing a neighbourhood selects its best cell and opens the reasons, named", async ({
  page,
}) => {
  await open(page);
  const list = page.getByTestId("top-neighbourhoods");
  await list.locator("summary").click();
  const first = list.getByRole("button").first();
  const name = (await first.textContent())?.split(",")[0] ?? "";
  await first.click();
  const panel = page.getByRole("complementary", { name: "Why this score" });
  await expect(panel).toBeVisible();
  await expect(panel).toContainText(name);
});

test("the list follows the user's weights: it changes when a weight does", async ({
  page,
}) => {
  await open(page);
  const list = page.getByTestId("top-neighbourhoods");
  await list.locator("summary").click();
  const before = await list.getByRole("button").allTextContents();
  await page.getByRole("slider", { name: "Weight of Safety" }).fill("0");
  await page.getByRole("slider", { name: "Weight of Transport" }).fill("5");
  await page.getByRole("slider", { name: "Weight of Environment" }).fill("0");
  const after = await list.getByRole("button").allTextContents();
  expect(after).not.toEqual(before);
});

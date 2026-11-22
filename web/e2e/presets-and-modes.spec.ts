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

const weight = (page: Page, name: string) =>
  page.getByRole("slider", { name: `Weight of ${name}` });

test("starting from a preset sets its weights, says so, and can be undone", async ({
  page,
}) => {
  await openApp(page);
  await weight(page, "Safety").fill("1");
  const start = page.getByRole("combobox", { name: "Start from" });
  await start.selectOption({ label: "Renter who works in the centre" });
  await expect(weight(page, "Transport")).toHaveValue("5");
  await expect(weight(page, "Safety")).toHaveValue("4");
  await expect(start).toHaveValue("renter-near-the-centre");
  await expect(page.getByTestId("presets")).toContainText("Undo");

  // A change of weight leaves the preset: the list no longer names it.
  await weight(page, "Transport").fill("2");
  await expect(start).toHaveValue("");

  // Another preset, then Undo: back to the weights just before it.
  await start.selectOption({ label: "Retired" });
  await expect(weight(page, "Safety")).toHaveValue("5");
  await page
    .getByTestId("presets")
    .getByRole("button", { name: "Undo" })
    .click();
  await expect(weight(page, "Transport")).toHaveValue("2");
  await expect(weight(page, "Safety")).toHaveValue("4");
});

test("the no weak spots switch changes the score, goes in the link, and the reasons show scores", async ({
  page,
}) => {
  await openApp(page);
  const add = page.getByRole("button", { name: "Add up" });
  const weak = page.getByRole("button", { name: "No weak spots" });
  await expect(add).toHaveAttribute("aria-pressed", "true");

  const list = page.getByTestId("top-neighbourhoods");
  await list.locator("summary").click();
  const scores = () =>
    list.getByRole("listitem").locator("span.tabular-nums").allTextContents();
  const before = await scores();
  await weak.click();
  await expect(weak).toHaveAttribute("aria-pressed", "true");
  await expect.poll(() => page.url()).toContain("m=balanced");
  await expect.poll(scores).not.toEqual(before);

  await list.getByRole("button").first().click();
  const panel = page.getByRole("complementary", { name: "Why this score" });
  await expect(panel).toContainText("No weak spots");
  await expect(panel).toContainText("out of 100");
  await expect(panel).not.toContainText("points");
});

test("the top neighbourhoods say how many stay when a weight moves", async ({
  page,
}) => {
  await openApp(page);
  const list = page.getByTestId("top-neighbourhoods");
  await expect(list.getByTestId("stability")).toHaveCount(0); // closed: not worked out
  await list.locator("summary").click();
  await expect(list.getByTestId("stability")).toContainText(
    /^\d+ of these \d+ stay, on average, when a weight moves by a fifth/,
  );
});

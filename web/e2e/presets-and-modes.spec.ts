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

test("a new visitor starts with a few essentials, and can count everything or one factor more", async ({
  page,
}) => {
  await openApp(page);
  const start = page.getByRole("combobox", { name: "Start from" });
  await expect(start).toHaveValue("a-few-essentials");
  await expect(page.getByTestId("presets")).toContainText(
    "Only a few things count to start with:",
  );
  // Health care holds no essential (D14), so it starts under "Not counted".
  await expect(weight(page, "Health care")).toHaveCount(0);
  await page.getByRole("button", { name: "Count Health care" }).click();
  await expect(weight(page, "Health care")).toHaveValue("3");
  await expect(start).toHaveValue("");

  await start.selectOption({ label: "Everything, equally" });
  await expect(weight(page, "Health care")).toHaveValue("3");
  await expect(start).toHaveValue("everything-equally");
  await expect.poll(() => page.url()).toContain("s=all");

  await start.selectOption({ label: "A few essentials" });
  await expect(weight(page, "Health care")).toHaveCount(0);
});

test("a link from before the start changed still counts every factor", async ({
  page,
}) => {
  await page.goto("/#w=transport:4");
  await expect(page.getByTestId("factor-tree")).toBeVisible();
  await expect(weight(page, "Transport")).toHaveValue("4");
  await expect(weight(page, "Health care")).toHaveValue("3");
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

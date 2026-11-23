import { expect, type Page, test } from "@playwright/test";

// The critique of the map (2026-11-23): the legend's keys look like the map draws the cells, it
// names the grey that hard limits leave, and its slider says what it does in plain words.

async function openApp(page: Page, path = "/") {
  await page.goto(path);
  await expect(page.getByTestId("map")).toHaveAttribute(
    "data-cells",
    /^[1-9]\d*$/,
  );
  await page.waitForLoadState("networkidle");
}

const legend = (page: Page) => page.getByRole("region", { name: "Legend" });

test("each key in the legend is a small hexagon, drawn as the map draws its cells", async ({
  page,
}) => {
  await openApp(page);
  const key = legend(page).getByTestId("few-homes-key");
  await expect(key).toBeVisible();
  expect(await key.evaluate((element) => element.tagName.toLowerCase())).toBe(
    "svg",
  );
  await expect(key.locator("polygon")).toHaveCount(1);
});

test("with a hard limit, the legend names the grey and counts the hex cells it leaves out", async ({
  page,
}) => {
  await openApp(page);
  await expect(legend(page)).not.toContainText("Left out by your hard limits");
  // A new page, so that the app reads the limit from the link as it opens.
  await page.goto("about:blank");
  await openApp(page, "/#l=station-proximity:max:0.1");
  await expect(legend(page)).toContainText(
    /Left out by your hard limits: [\d,]+ of [\d,]+/,
  );
  await expect(legend(page).getByTestId("left-out-key")).toBeVisible();
});

test("the slider says it sets how strong the colours are", async ({ page }) => {
  await openApp(page);
  const slider = legend(page).getByRole("slider", { name: "Colour strength" });
  await expect(slider).toHaveValue("80");
  await expect(legend(page)).toContainText("Colour strength");
  await expect(legend(page)).not.toContainText("Cell opacity");
});

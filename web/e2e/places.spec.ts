import { expect, type Page, test } from "@playwright/test";
import { clearCentre } from "./clip";

async function openApp(page: Page, fragment = "") {
  await page.goto(`/${fragment}`);
  await expect(page.getByTestId("map")).toHaveAttribute(
    "data-cells",
    /^[1-9]\d*$/,
  );
  await expect(page.getByTestId("factor-tree")).toBeVisible();
  await page.waitForLoadState("networkidle");
}

/** Points at the middle of the map's clear part, which is over the fixture's cells, until the layer has
 * registered the cell under the pointer (it picks asynchronously), and returns that point. */
async function pointAtCell(page: Page) {
  const { x, y } = await clearCentre(page, page.getByTestId("map"));
  await expect(async () => {
    await page.mouse.move(x - 5, y - 5);
    await page.mouse.move(x, y);
    await expect(page.getByTestId("quick-look")).toBeVisible({ timeout: 500 });
  }).toPass({ timeout: 10_000 });
  return { x, y };
}

const section = (page: Page) =>
  page.getByRole("region", { name: "Your places" }).first();

// A postcode in Soho, inside the fixture bundle's cells.
const POSTCODE = "W1D 3QF";

test("a place added by postcode becomes the travel time, stays after a reload, and never goes in the link", async ({
  page,
}) => {
  await openApp(page);
  const places = section(page);
  await places.getByLabel("Name").fill("Work");
  await places.getByLabel("Postcode").fill(POSTCODE);
  await places.getByRole("button", { name: "Add by postcode" }).click();
  await expect(places.getByRole("listitem")).toHaveText(["WorkRemove"]);
  await expect(places).toContainText(
    "Travel time on the map is now the time to your places.",
  );
  expect(page.url()).not.toContain("Work");
  expect(page.url()).not.toContain("W1D");

  // The reasons list the minutes to the place.
  // A click is picked asynchronously too, so it is repeated until it lands, as in view.spec.ts.
  const { x, y } = await pointAtCell(page);
  const panel = page.getByRole("complementary", { name: "Why this score" });
  await expect(async () => {
    await page.mouse.click(x, y);
    await expect(panel).toBeVisible({ timeout: 500 });
  }).toPass({ timeout: 10_000 });
  await expect(panel).toContainText("Your places");
  await expect(panel).toContainText(/Work\s*\d+ minutes/);

  await openApp(page);
  await expect(section(page).getByRole("listitem")).toHaveText(["WorkRemove"]);
});

test("a postcode outside the region is not added, and says so", async ({
  page,
}) => {
  await openApp(page);
  const places = section(page);
  await places.getByLabel("Postcode").fill("ZZ9 9ZZ");
  await places.getByRole("button", { name: "Add by postcode" }).click();
  await expect(places.getByRole("alert")).toHaveText(
    "That postcode is not in this region.",
  );
  await expect(places.getByRole("listitem")).toHaveCount(0);
});

test("a place can be chosen on the map, and removed", async ({ page }) => {
  await openApp(page);
  const places = section(page);
  await places.getByLabel("Name").fill("Family");
  await places.getByRole("button", { name: "Choose on the map" }).click();
  await expect(places.getByRole("status")).toContainText(
    "Click the map where Family is.",
  );
  // A click that picks no cell leaves the choosing on, so it is repeated until it lands.
  const { x, y } = await pointAtCell(page);
  await expect(async () => {
    await page.mouse.click(x, y);
    await expect(places.getByRole("listitem")).toHaveText(["FamilyRemove"], {
      timeout: 500,
    });
  }).toPass({ timeout: 10_000 });
  // Choosing the place did not open the reasons of the cell clicked.
  await expect(
    page.getByRole("complementary", { name: "Why this score" }),
  ).toHaveCount(0);
  await places.getByRole("button", { name: "Remove Family" }).click();
  await expect(places.getByRole("listitem")).toHaveCount(0);
});

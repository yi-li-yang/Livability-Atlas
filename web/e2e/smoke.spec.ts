import { expect, test } from "@playwright/test";

test("the page shows a map of London under its heading", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Livability Atlas" }),
  ).toBeVisible();
  await expect(page.getByTestId("map").locator("canvas")).toBeVisible();
});

test("the map's worker script is served as JavaScript, so that the map can draw", async ({
  page,
}) => {
  const worker = page.waitForResponse((response) =>
    response.url().includes("maplibre-gl-worker"),
  );
  await page.goto("/");
  expect((await worker).headers()["content-type"]).toMatch(/javascript/);
});

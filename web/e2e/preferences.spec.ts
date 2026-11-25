import { expect, type Page, test } from "@playwright/test";
import { PNG } from "pngjs";
import { clearOfPanel } from "./clip";

/**
 * The fixture bundle has no indicator that the user can turn or band, so these tests serve its
 * manifest with two of its indicators changed: the walk to a station becomes a user-direction
 * indicator (its ramp says that less is better), and the walk to a GP a user-range one. The app
 * must offer the controls from the manifest alone.
 */
async function openApp(page: Page, fragment = "") {
  await page.route("**/manifest.json", async (route) => {
    const response = await route.fetch();
    const manifest = await response.json();
    for (const indicator of manifest.indicators) {
      if (indicator.id === "station-proximity") {
        indicator.preference_type = "user-direction";
      }
      if (indicator.id === "gp-walk") {
        indicator.preference_type = "user-range";
        indicator.curve = {
          shape: "ideal-range",
          l0: 0,
          l1: 5,
          u1: 15,
          u0: 20,
        };
      }
    }
    await route.fulfill({ response, json: manifest });
  });
  await page.goto(`/${fragment}`);
  await expect(page.getByTestId("map")).toHaveAttribute(
    "data-cells",
    /^[1-9]\d*$/,
  );
  // With one factor counted there is no picture of the shares, so wait for the section itself.
  await expect(
    page.getByRole("region", { name: "What matters to you" }),
  ).toBeVisible();
  await page.waitForLoadState("networkidle");
}

/** How many pixels of the map differ between two screenshots. */
function differing(before: Buffer, after: Buffer): number {
  const a = PNG.sync.read(before);
  const b = PNG.sync.read(after);
  let count = 0;
  for (let i = 0; i < a.data.length; i += 4) {
    const gap =
      Math.abs(a.data[i] - b.data[i]) +
      Math.abs(a.data[i + 1] - b.data[i + 1]) +
      Math.abs(a.data[i + 2] - b.data[i + 2]);
    if (gap > 24) count++;
  }
  return count;
}

test("a user-direction indicator has a more or less switch that turns its scores round", async ({
  page,
}) => {
  // Only the walk to a station counts, so turning it round must recolour the map.
  await openApp(
    page,
    "#w=safety:0,environment:0,health-care:0,service-level:0",
  );
  await page.getByRole("button", { name: "Open Transport" }).click();
  await page
    .getByRole("button", { name: "Open Getting around in general" })
    .click();
  const less = page.getByRole("button", { name: "Less is better" });
  const more = page.getByRole("button", { name: "More is better" });
  await expect(less).toHaveAttribute("aria-pressed", "true");
  await expect(more).toHaveAttribute("aria-pressed", "false");

  const map = page.getByTestId("map");
  const clip = await clearOfPanel(page, map);
  const before = await page.screenshot({ clip });
  await more.click();
  await expect(more).toHaveAttribute("aria-pressed", "true");
  await expect.poll(() => page.url()).toContain("f=station-proximity");
  await expect
    .poll(async () => differing(before, await page.screenshot({ clip })), {
      timeout: 10_000,
    })
    .toBeGreaterThan(2000);

  // The browser keeps it.
  await openApp(page);
  await page.getByRole("button", { name: "Open Transport" }).click();
  await page
    .getByRole("button", { name: "Open Getting around in general" })
    .click();
  await expect(
    page.getByRole("button", { name: "More is better" }),
  ).toHaveAttribute("aria-pressed", "true");
});

test("a user-range indicator has a band that the user drags, which rescores the map", async ({
  page,
}) => {
  await openApp(page, "#w=safety:0,environment:0,transport:0");
  await page.getByRole("button", { name: "Open Health care" }).click();
  await page.getByRole("button", { name: "Open GP access" }).click();
  const band = page.getByTestId("band");
  await expect(band).toContainText("Full marks from 5 to 15");

  const map = page.getByTestId("map");
  const clip = await clearOfPanel(page, map);
  const before = await page.screenshot({ clip });
  await page
    .getByRole("slider", {
      name: "Walk to a GP practice: lowest for full marks",
    })
    .fill("10");
  await expect(band).toContainText("Full marks from 10 to 15");
  await expect.poll(() => page.url()).toContain("r=gp-walk:10~15");
  await expect
    .poll(async () => differing(before, await page.screenshot({ clip })), {
      timeout: 10_000,
    })
    .toBeGreaterThan(2000);

  // "Start again" brings the catalogue's band back.
  await page.getByRole("button", { name: "Start again" }).click();
  await expect(page.getByTestId("band")).toContainText(
    "Full marks from 5 to 15",
  );
});

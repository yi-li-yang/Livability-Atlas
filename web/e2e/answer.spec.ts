import { expect, type Page, test } from "@playwright/test";
import { PNG } from "pngjs";
import { clearOfPanel } from "./clip";

// The critique of the map (2026-11-23): the map should show the answer. The legend shows where the
// region's scores lie, the map can colour by rank in the region (D24), and it marks the top
// neighbourhoods.

async function openApp(page: Page, path = "/") {
  await page.goto(path);
  await expect(page.getByTestId("map")).toHaveAttribute(
    "data-cells",
    /^[1-9]\d*$/,
  );
  await page.waitForLoadState("networkidle");
}

const legend = (page: Page) => page.getByRole("region", { name: "Legend" });

/** How many pixels differ between two screenshots. */
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

test("the legend shows where the region's scores lie, with numbers on the scale", async ({
  page,
}) => {
  await openApp(page);
  await expect(legend(page).getByTestId("score-spread")).toBeVisible();
  await expect(legend(page)).toContainText("0");
  await expect(legend(page)).toContainText("100");
  await expect(legend(page)).toContainText(
    /Most of London scores \d+ to \d+\./,
  );
});

test("the map can colour by rank in London, in fifths, and keeps that choice in the browser only", async ({
  page,
}) => {
  await openApp(page);
  const score = legend(page).getByRole("button", { name: "Score" });
  const rank = legend(page).getByRole("button", { name: "Rank in London" });
  await expect(score).toHaveAttribute("aria-pressed", "true");

  const clip = await clearOfPanel(page, page.getByTestId("map"));
  const before = await page.screenshot({ clip });
  await rank.click();
  await expect(rank).toHaveAttribute("aria-pressed", "true");
  await expect(legend(page)).toContainText("Bottom fifth");
  await expect(legend(page)).toContainText("Top fifth");
  await expect(legend(page).getByTestId("score-spread")).toHaveCount(0);
  await expect
    .poll(async () => differing(before, await page.screenshot({ clip })), {
      timeout: 10_000,
    })
    .toBeGreaterThan(1000);
  expect(page.url()).not.toContain("rank");

  await openApp(page);
  await expect(
    legend(page).getByRole("button", { name: "Rank in London" }),
  ).toHaveAttribute("aria-pressed", "true");
});

test("the top neighbourhoods are marked on the map while it shows the livability score", async ({
  page,
}) => {
  await openApp(page);
  const key = legend(page).getByText("Top neighbourhoods, numbered by rank");
  await expect(key).toBeVisible();
  // A factor's own score is not the answer to where to live: the marks go.
  await page
    .getByRole("combobox", { name: "Show on the map" })
    .selectOption({ label: "Safety" });
  await expect(key).toHaveCount(0);
});

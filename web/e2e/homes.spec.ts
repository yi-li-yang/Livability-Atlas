import { expect, type Page, test } from "@playwright/test";
import { LONDON_CENTRE } from "../src/features/map/london";
import { clearCentre } from "./clip";

/**
 * The middle of a hex cell in Regent's Park, with no homes in the fixture bundle and few or none in
 * five of its six neighbours: the map leaves it clear and it has no score (D22).
 */
const REGENTS_PARK: [number, number] = [-0.1524, 51.5305];
/** The zoom the map opens at, centred on `LONDON_CENTRE`. */
const START_ZOOM = 10;

/**
 * The pixel of a point on the map as it opens, by the Web Mercator projection that it uses, from
 * `centre`, where the map puts `LONDON_CENTRE`: the middle of the part the panel leaves clear.
 */
function pixelOf(
  [lng, lat]: [number, number],
  centre: { x: number; y: number },
) {
  const world = 512 * 2 ** START_ZOOM; // MapLibre's tiles are 512 px
  const x = (l: number) => ((l + 180) / 360) * world;
  const y = (l: number) => {
    const sin = Math.sin((l * Math.PI) / 180);
    return (0.5 - Math.log((1 + sin) / (1 - sin)) / (4 * Math.PI)) * world;
  };
  return {
    x: centre.x + x(lng) - x(LONDON_CENTRE[0]),
    y: centre.y + y(lat) - y(LONDON_CENTRE[1]),
  };
}

async function openApp(page: Page) {
  await page.goto("/");
  const map = page.getByTestId("map");
  await expect(map).toHaveAttribute("data-cells", /^[1-9]\d*$/);
  await page.waitForLoadState("networkidle");
  const box = await map.boundingBox();
  if (!box) throw new Error("the map is not shown");
  return box;
}

test("the legend says that a hex cell with few or no homes has no score", async ({
  page,
}) => {
  await openApp(page);
  const legend = page.getByRole("region", { name: "Legend" });
  await expect(legend).toContainText("Few or no homes: no score");
  await expect(legend.getByTestId("few-homes-key")).toBeVisible();
});

test("a park has no score, no rank and no reasons, and says why", async ({
  page,
}) => {
  await openApp(page);
  const { x, y } = pixelOf(
    REGENTS_PARK,
    await clearCentre(page, page.getByTestId("map")),
  );
  // Zoom in on the park, which stays under the pointer, so that its hex cell is easy to hit.
  await page.mouse.move(x, y);
  for (let i = 0; i < 6; i++) {
    await page.mouse.wheel(0, -300);
    await page.waitForTimeout(150);
  }
  await page.waitForLoadState("networkidle");
  const card = page.getByTestId("quick-look");
  await expect(async () => {
    await page.mouse.move(x - 3, y - 3);
    await page.mouse.move(x, y);
    await expect(card).toBeVisible({ timeout: 500 });
  }).toPass({ timeout: 10_000 });
  await expect(card).toContainText("Few or no homes here");
  await expect(card).not.toContainText("out of 100");
  await expect(card).not.toContainText(/Rank/);

  const panel = page.getByRole("complementary", { name: "Why this score" });
  await expect(async () => {
    await page.mouse.click(x, y);
    await expect(panel).toBeVisible({ timeout: 500 });
  }).toPass({ timeout: 10_000 });
  await expect(panel).toContainText("Few or no homes here");
  await expect(panel).not.toContainText("out of 100");
  await expect(panel.getByTestId("score-bar")).toHaveCount(0);
});

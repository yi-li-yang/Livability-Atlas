import { expect, type Page, test } from "@playwright/test";
import { PNG } from "pngjs";
import { clearOfPanel } from "./clip";

/** Opens the app and returns the pixel at the middle of the map, which is over the fixture's cells. */
async function openOverCells(page: Page) {
  await page.goto("/");
  const map = page.getByTestId("map");
  await expect(map).toHaveAttribute("data-cells", /^[1-9]\d*$/);
  await page.waitForLoadState("networkidle");
  const box = await map.boundingBox();
  if (!box) throw new Error("the map is not shown");
  return { x: box.x + box.width / 2, y: box.y + box.height / 2 };
}

const view = (page: Page) =>
  page.getByRole("combobox", { name: "Show on the map" });
const legend = (page: Page) =>
  page.getByRole("region", { name: "Legend" }).getByRole("heading");

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

interface Node {
  id: string;
  name: string;
  indicator?: string | null;
  children?: Node[];
}

test("the map shows the livability score first, and a list offers each factor and indicator", async ({
  page,
  request,
}) => {
  await openOverCells(page);
  await expect(legend(page)).toHaveText("Livability score");
  await expect(view(page)).toHaveValue("");

  // The list is made from the manifest alone: every factor and measured indicator in the tree,
  // in its order, with no code for any of them. Choice indicators have no score until picked.
  const latest = await (
    await request.get("/bundles/london/latest.json")
  ).json();
  const manifest = await (
    await request.get(`/bundles/london/${latest.version}/manifest.json`)
  ).json();
  const choices = new Set<string>(
    manifest.indicators
      .filter(
        (i: { preference_type: string }) => i.preference_type === "user-choice",
      )
      .map((i: { id: string }) => i.id),
  );
  const names = (node: Node): string[] => {
    const inside = (node.children ?? []).flatMap(names);
    const offered = node.children
      ? inside.length > 0
      : !choices.has(node.indicator ?? "");
    return offered ? [node.name, ...inside] : [];
  };
  const expected = (manifest.factors as Node[]).flatMap(names);
  expect(expected.length).toBeGreaterThan(8);
  const listed = (
    await view(page).locator("optgroup option").allTextContents()
  ).map((text) => text.replaceAll(" ", "").trim());
  expect(listed).toEqual(expected);
  await expect(view(page).locator("optgroup")).toHaveCount(
    manifest.factors.filter((f: Node) => names(f).length > 0).length,
  );
});

test("choosing a factor shows its own score, with its name on the legend, and recolours the map", async ({
  page,
}) => {
  await openOverCells(page);
  const map = page.getByTestId("map");
  const clip = await clearOfPanel(page, map);
  const before = await page.screenshot({ clip });

  await view(page).selectOption({ label: "Safety" });
  await expect(legend(page)).toHaveText("Safety score");
  await expect
    .poll(async () => differing(before, await page.screenshot({ clip })), {
      timeout: 10_000,
    })
    .toBeGreaterThan(2000);

  await view(page).selectOption({ label: "Livability score" });
  await expect(legend(page)).toHaveText("Livability score");
});

test("the quick look and the reasons give the score on the map, and the livability score as before", async ({
  page,
}) => {
  const { x, y } = await openOverCells(page);
  await view(page).selectOption({ label: "Safety" });
  const card = page.getByTestId("quick-look");
  await expect(async () => {
    await page.mouse.move(x - 5, y - 5);
    await page.mouse.move(x, y);
    await expect(card).toBeVisible({ timeout: 500 });
  }).toPass({ timeout: 10_000 });
  await expect(card.getByTestId("on-the-map")).toContainText(
    /On the map: Safety, \d+ out of 100/,
  );
  await expect(card).toContainText("Livability score");
  await expect(card).toContainText(/Rank [\d,]+ of [\d,]+/);

  const panel = page.getByRole("complementary", { name: "Why this score" });
  await expect(async () => {
    await page.mouse.move(x, y);
    await page.mouse.click(x, y);
    await expect(panel).toBeVisible({ timeout: 500 });
  }).toPass({ timeout: 10_000 });
  await expect(panel.getByTestId("on-the-map")).toContainText(
    /On the map: Safety, \d+ out of 100/,
  );
  await expect(panel).toContainText("Livability score");

  // With the livability score on the map the line goes.
  await view(page).selectOption({ label: "Livability score" });
  await expect(panel.getByTestId("on-the-map")).toHaveCount(0);
});

test("a view does not change the ranking: the livability score and rank stay the same", async ({
  page,
}) => {
  const { x, y } = await openOverCells(page);
  const card = page.getByTestId("quick-look");
  const hover = async () => {
    await expect(async () => {
      await page.mouse.move(x - 5, y - 5);
      await page.mouse.move(x, y);
      await expect(card).toBeVisible({ timeout: 500 });
    }).toPass({ timeout: 10_000 });
    return (await card.textContent()) ?? "";
  };
  const rank = (text: string) => text.match(/Rank [\d,]+ of [\d,]+/)?.[0];
  const before = await hover();
  await view(page).selectOption({ label: "Safety" });
  const during = await hover();
  expect(rank(during)).toBe(rank(before));
});

test("the preferences panel cannot grow down over the legend, with its list", async ({
  page,
}) => {
  await openOverCells(page);
  const reach = await page.evaluate(() => {
    const panel = document.querySelector("aside");
    const legend = document.querySelector('section[aria-label="Legend"]');
    const map = panel?.offsetParent;
    if (!panel || !legend || !map)
      throw new Error("the panel or the legend is not shown");
    // The lowest the panel can ever reach: its top, and the most it may be tall, which the style
    // gives as a share of the map less a length.
    const given = getComputedStyle(panel).maxHeight.match(
      /^calc\(100% - ([\d.]+)px\)$/,
    );
    if (!given)
      throw new Error("the panel has no height limit under the map's");
    const bottom =
      panel.getBoundingClientRect().top + map.clientHeight - Number(given[1]);
    return { bottom, legend: legend.getBoundingClientRect().top };
  });
  expect(reach.bottom).toBeLessThanOrEqual(reach.legend);
});

test("a factor with nothing counted inside it says so", async ({ page }) => {
  await openOverCells(page);
  await view(page).selectOption({ label: "Safety" });
  await expect(page.getByRole("note")).toHaveCount(0);
  // Safety holds one group in the test bundle: counting nothing in it leaves the map without data.
  await page.getByRole("button", { name: "Open Safety" }).click();
  await page
    .getByRole("slider", { name: /^Weight of / })
    .first()
    .fill("0");
  await expect(
    page.getByRole("note").filter({ hasText: "Nothing inside Safety counts" }),
  ).toBeVisible();
});

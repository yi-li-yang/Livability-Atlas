import { expect, type Page, test } from "@playwright/test";

// A factor is added to the catalogue by the recipe, with no change to the app's code: the app
// builds its factor tree from the bundle's manifest alone. This reads the manifest and walks the
// app's factor tree, level by level, and checks that every factor and measured indicator is there.

interface Node {
  id: string;
  name: string;
  children?: Node[];
}

const allFactors = (page: Page) =>
  page.getByRole("button", { name: "All factors" });

/** The names that a level of the factor tree shows: those with a slider, and those not counted. */
async function shownNames(page: Page): Promise<string[]> {
  const counted = await page
    .getByRole("slider", { name: /^Weight of / })
    .evaluateAll((sliders) =>
      sliders.map(
        (s) => s.getAttribute("aria-label")?.replace(/^Weight of /, "") ?? "",
      ),
    );
  const notCounted = await page
    .getByRole("heading", { name: "Not counted" })
    .locator(
      "xpath=following-sibling::ul[1]/li//span[contains(@class,'flex-1')]",
    )
    .allTextContents();
  return [...counted, ...notCounted];
}

/** Opens the factors of `path`, one inside the other, from the top. */
async function openPath(page: Page, path: readonly Node[]) {
  if (await allFactors(page).isEnabled()) await allFactors(page).click();
  for (const node of path) {
    await page.getByRole("button", { name: `Open ${node.name}` }).click();
  }
}

test("the factor tree shows every factor and measured indicator of the manifest, and no other", async ({
  page,
  request,
}) => {
  const latest = await (
    await request.get("/bundles/london/latest.json")
  ).json();
  const manifest = await (
    await request.get(`/bundles/london/${latest.version}/manifest.json`)
  ).json();
  await page.goto("/");
  await expect(page.getByTestId("factor-tree")).toBeVisible();
  await page.waitForLoadState("networkidle");

  let levels = 0;
  let names = 0;
  const walk = async (nodes: readonly Node[], path: readonly Node[]) => {
    await openPath(page, path);
    expect(
      (await shownNames(page)).sort(),
      path.map((n) => n.name).join(" › "),
    ).toEqual(nodes.map((n) => n.name).sort());
    levels += 1;
    names += nodes.length;
    for (const node of nodes) {
      if (node.children?.length) await walk(node.children, [...path, node]);
    }
  };
  await walk(manifest.factors as Node[], []);

  // Not a test of nothing: the fixture has several levels and a good many names.
  expect(levels).toBeGreaterThan(5);
  expect(names).toBeGreaterThan(15);
});

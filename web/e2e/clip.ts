import type { Locator, Page } from "@playwright/test";

/**
 * The part of the map that the panel of preferences leaves clear, as a clip for a screenshot. The
 * panel is translucent, so pixels under it change when the panel does, and say nothing of the map.
 */
export async function clearOfPanel(page: Page, map: Locator) {
  const mapBox = await map.boundingBox();
  const panelBox = await page.getByRole("complementary").boundingBox();
  if (!mapBox || !panelBox)
    throw new Error("the map or the panel is not shown");
  const left = panelBox.x + panelBox.width + 8 - mapBox.x;
  return {
    x: mapBox.x + left,
    y: mapBox.y,
    width: mapBox.width - left,
    height: mapBox.height,
  };
}

/**
 * The middle of the part of the map that the panel leaves clear: the app puts the region's centre
 * there in its first view, so it is over the cells of the test bundle (D23's follow-up: the camera
 * keeps clear of the panels).
 */
export async function clearCentre(page: Page, map: Locator) {
  const clip = await clearOfPanel(page, map);
  return {
    x: clip.x + clip.width / 2,
    y: clip.y + clip.height / 2,
  };
}

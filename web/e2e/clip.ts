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

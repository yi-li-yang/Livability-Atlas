import type { Store } from "../../profile/storage";

/**
 * How the factor tree is drawn (D17): as boxes, which show first, or as rings, which the
 * glossary calls the treemap and the sunburst.
 */
export type Layout = "boxes" | "rings";

/** Where the browser keeps the choice of layout between visits. */
export const LAYOUT_KEY = "atlas.layout.v1";

export function loadLayout(store: Store | null): Layout {
  try {
    return store?.getItem(LAYOUT_KEY) === "rings" ? "rings" : "boxes";
  } catch {
    return "boxes"; // Storage is blocked: the boxes show.
  }
}

export function saveLayout(layout: Layout, store: Store | null): void {
  try {
    store?.setItem(LAYOUT_KEY, layout);
  } catch {
    // Storage can be full or blocked, as in a private window: the app works without it.
  }
}

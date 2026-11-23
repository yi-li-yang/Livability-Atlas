/** A rectangle on the screen, in pixels, as `getBoundingClientRect` gives it. */
export interface Box {
  left: number;
  top: number;
  right: number;
  bottom: number;
}

/** How far in from each edge of the map its clear part starts, in pixels. */
export interface Inset {
  top: number;
  right: number;
  bottom: number;
  left: number;
}

/** A panel at least this share of the map's width is a bar across it, not a column down it. */
const BAR = 0.6;

/** The share of the map that always stays clear, however much the panels cover. */
const CLEAR = 1 / 3;

/**
 * Which part of the map the panels over it leave clear (the critique of the map: the panels hid
 * what the map showed). A panel at least 60% of the map's width is a bar, which covers from the
 * top or the bottom edge, whichever it is nearer; any other panel is a column, which covers from
 * the left or the right edge. What lies outside the map, or has no size, covers nothing. At least
 * a third of the map's width and height stays clear.
 */
export function insetFor(map: Box, panels: readonly Box[]): Inset {
  const inset: Inset = { top: 0, right: 0, bottom: 0, left: 0 };
  const width = map.right - map.left;
  const height = map.bottom - map.top;
  for (const panel of panels) {
    const left = Math.max(panel.left, map.left);
    const right = Math.min(panel.right, map.right);
    const top = Math.max(panel.top, map.top);
    const bottom = Math.min(panel.bottom, map.bottom);
    if (right <= left || bottom <= top) continue;
    if (right - left >= BAR * width) {
      if (top - map.top <= map.bottom - bottom) {
        inset.top = Math.max(inset.top, bottom - map.top);
      } else {
        inset.bottom = Math.max(inset.bottom, map.bottom - top);
      }
    } else if (left - map.left <= map.right - right) {
      inset.left = Math.max(inset.left, right - map.left);
    } else {
      inset.right = Math.max(inset.right, map.right - left);
    }
  }
  const squeeze = (a: number, b: number, size: number): [number, number] => {
    const most = size * (1 - CLEAR);
    return a + b <= most
      ? [a, b]
      : [(a * most) / (a + b), (b * most) / (a + b)];
  };
  [inset.top, inset.bottom] = squeeze(inset.top, inset.bottom, height);
  [inset.left, inset.right] = squeeze(inset.left, inset.right, width);
  return inset;
}

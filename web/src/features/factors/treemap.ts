export interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface Tile<T> extends Rect {
  item: T;
}

/**
 * Lays items out as a squarified treemap (Bruls, Huizing and van Wijk): nested rectangles whose
 * areas are proportional to the items' values, kept as close to squares as the layout allows.
 * Items with a value of 0 or less take no space and are left out.
 */
export function squarify<T extends { value: number }>(
  items: readonly T[],
  rect: Rect,
): Tile<T>[] {
  const sorted = items.filter((item) => item.value > 0);
  sorted.sort((a, b) => b.value - a.value);
  const total = sorted.reduce((sum, item) => sum + item.value, 0);
  if (total === 0 || rect.w <= 0 || rect.h <= 0) return [];

  const scale = (rect.w * rect.h) / total;
  const tiles: Tile<T>[] = [];
  let { x, y, w, h } = rect;
  let row: T[] = [];

  /** The worst aspect ratio in a row laid along a side of this length. */
  const worst = (candidates: readonly T[], side: number): number => {
    const areas = candidates.map((item) => item.value * scale);
    const sum = areas.reduce((a, b) => a + b, 0);
    return Math.max(
      (side * side * Math.max(...areas)) / (sum * sum),
      (sum * sum) / (side * side * Math.min(...areas)),
    );
  };

  /** Places a finished row against the shorter side of the space that is left. */
  const place = (finished: readonly T[]): void => {
    const sum = finished.reduce((a, item) => a + item.value * scale, 0);
    if (w >= h) {
      const width = sum / h;
      let top = y;
      for (const item of finished) {
        const height = (item.value * scale) / width;
        tiles.push({ item, x, y: top, w: width, h: height });
        top += height;
      }
      x += width;
      w -= width;
    } else {
      const height = sum / w;
      let left = x;
      for (const item of finished) {
        const width = (item.value * scale) / height;
        tiles.push({ item, x: left, y, w: width, h: height });
        left += width;
      }
      y += height;
      h -= height;
    }
  };

  for (const item of sorted) {
    const side = Math.min(w, h);
    if (row.length === 0 || worst([...row, item], side) <= worst(row, side)) {
      row.push(item);
    } else {
      place(row);
      row = [item];
    }
  }
  if (row.length > 0) place(row);
  return tiles;
}

import { describe, expect, it } from "vitest";
import { type Rect, squarify } from "./treemap";

const BOX: Rect = { x: 0, y: 0, w: 100, h: 60 };
const item = (id: string, value: number) => ({ id, value });

const overlap = (a: Rect, b: Rect): number =>
  Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x)) *
  Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y));

describe("squarify", () => {
  const items = [
    item("a", 4),
    item("b", 4),
    item("c", 3),
    item("d", 2),
    item("e", 1),
    item("f", 1),
  ];

  it("gives each item an area in proportion to its value", () => {
    const tiles = squarify(items, BOX);
    const total = 15;
    expect(tiles).toHaveLength(6);
    for (const tile of tiles) {
      expect(tile.w * tile.h).toBeCloseTo(
        (tile.item.value / total) * BOX.w * BOX.h,
        9,
      );
    }
  });

  it("fills the box exactly, with tiles inside it that do not overlap", () => {
    const tiles = squarify(items, BOX);
    expect(tiles.reduce((sum, t) => sum + t.w * t.h, 0)).toBeCloseTo(6000, 6);
    for (const t of tiles) {
      expect(t.x).toBeGreaterThanOrEqual(-1e-9);
      expect(t.y).toBeGreaterThanOrEqual(-1e-9);
      expect(t.x + t.w).toBeLessThanOrEqual(BOX.w + 1e-9);
      expect(t.y + t.h).toBeLessThanOrEqual(BOX.h + 1e-9);
    }
    for (let i = 0; i < tiles.length; i++) {
      for (let j = i + 1; j < tiles.length; j++) {
        expect(overlap(tiles[i], tiles[j])).toBeLessThan(1e-6);
      }
    }
  });

  it("keeps the tiles close to squares", () => {
    for (const tile of squarify(items, BOX)) {
      const ratio = Math.max(tile.w / tile.h, tile.h / tile.w);
      expect(ratio).toBeLessThan(3);
    }
  });

  it("leaves out an item of weight 0 and lets the others have its space", () => {
    const tiles = squarify([item("a", 3), item("zero", 0), item("b", 1)], BOX);
    expect(tiles.map((t) => t.item.id).sort()).toEqual(["a", "b"]);
    expect(tiles.reduce((sum, t) => sum + t.w * t.h, 0)).toBeCloseTo(6000, 6);
  });

  it("gives a single item the whole box", () => {
    const [tile] = squarify([item("only", 2)], BOX);
    expect(tile).toMatchObject(BOX);
  });

  it("gives nothing for no items, or none with a value", () => {
    expect(squarify([], BOX)).toEqual([]);
    expect(squarify([item("zero", 0)], BOX)).toEqual([]);
  });

  it("works inside a box that does not start at the origin", () => {
    const box = { x: 10, y: 20, w: 30, h: 90 };
    const tiles = squarify(items, box);
    for (const t of tiles) {
      expect(t.x).toBeGreaterThanOrEqual(10 - 1e-9);
      expect(t.y).toBeGreaterThanOrEqual(20 - 1e-9);
      expect(t.x + t.w).toBeLessThanOrEqual(40 + 1e-9);
      expect(t.y + t.h).toBeLessThanOrEqual(110 + 1e-9);
    }
  });
});

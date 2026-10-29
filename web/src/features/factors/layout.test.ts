import { describe, expect, it } from "vitest";
import type { Store } from "../../profile/storage";
import { LAYOUT_KEY, loadLayout, saveLayout } from "./layout";

const memory = (
  initial: Record<string, string> = {},
): Store & { data: Record<string, string> } => {
  const data = { ...initial };
  return {
    data,
    getItem: (key) => data[key] ?? null,
    setItem: (key, value) => {
      data[key] = value;
    },
  };
};

const blocked: Store = {
  getItem: () => {
    throw new Error("blocked");
  },
  setItem: () => {
    throw new Error("blocked");
  },
};

describe("loadLayout", () => {
  it("starts with the boxes, which D17 shows first", () => {
    expect(loadLayout(memory())).toBe("boxes");
  });

  it("returns what was saved", () => {
    expect(loadLayout(memory({ [LAYOUT_KEY]: "rings" }))).toBe("rings");
    expect(loadLayout(memory({ [LAYOUT_KEY]: "boxes" }))).toBe("boxes");
  });

  it("ignores anything else that is stored", () => {
    for (const text of ["", "sunburst", "RINGS", "1", "null"]) {
      expect(loadLayout(memory({ [LAYOUT_KEY]: text }))).toBe("boxes");
    }
  });

  it("works where the storage is missing or blocked", () => {
    expect(loadLayout(null)).toBe("boxes");
    expect(loadLayout(blocked)).toBe("boxes");
  });
});

describe("saveLayout", () => {
  it("keeps the layout for the next visit", () => {
    const store = memory();
    saveLayout("rings", store);
    expect(loadLayout(store)).toBe("rings");
    saveLayout("boxes", store);
    expect(loadLayout(store)).toBe("boxes");
  });

  it("works where the storage is missing or blocked", () => {
    expect(() => saveLayout("rings", null)).not.toThrow();
    expect(() => saveLayout("rings", blocked)).not.toThrow();
  });
});

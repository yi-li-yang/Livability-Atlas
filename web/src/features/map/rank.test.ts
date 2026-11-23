import { describe, expect, it } from "vitest";
import { EXCLUDED, FEW_HOMES, PALETTE, UNSCORED } from "./colour";
import {
  COLOUR_BY_KEY,
  fifthColours,
  loadColourBy,
  saveColourBy,
  scoreSpread,
} from "./rank";

const stop = (i: number) => [...PALETTE[i], 255];

describe("fifthColours", () => {
  it("gives each fifth of the cells that count one colour of the scale, worst to best", () => {
    const scores = Float64Array.from([50, 10, 90, 30, 70, 20, 40, 60, 80, 100]);
    const colours = fifthColours(scores);
    // 10 and 20 are the bottom fifth, 90 and 100 the top.
    expect(colours[1]).toEqual(stop(0));
    expect(colours[5]).toEqual(stop(0));
    expect(colours[3]).toEqual(stop(1));
    expect(colours[0]).toEqual(stop(2));
    expect(colours[4]).toEqual(stop(3));
    expect(colours[2]).toEqual(stop(4));
    expect(colours[9]).toEqual(stop(4));
  });

  it("ranks only the cells that count: not a left-out cell, nor one with few homes or no score", () => {
    const scores = Float64Array.from([10, 20, 30, 40, 50, 99, Number.NaN, 1]);
    const excluded = Uint8Array.from([0, 0, 0, 0, 0, 1, 0, 0]);
    const few = Uint8Array.from([0, 0, 0, 0, 0, 0, 0, 1]);
    const colours = fifthColours(scores, excluded, few);
    expect(colours[0]).toEqual(stop(0));
    expect(colours[4]).toEqual(stop(4));
    expect(colours[5]).toEqual(EXCLUDED);
    expect(colours[6]).toEqual(UNSCORED);
    expect(colours[7]).toEqual(FEW_HOMES);
  });

  it("puts equal scores in the same fifth", () => {
    const scores = Float64Array.from([5, 5, 5, 5, 5, 5, 5, 5, 9, 9]);
    const colours = fifthColours(scores);
    expect(new Set(colours.slice(0, 8).map(String)).size).toBe(1);
    expect(colours[8]).toEqual(colours[9]);
  });
});

describe("scoreSpread", () => {
  it("counts the cells that count in each band of the scale", () => {
    const scores = Float64Array.from([0, 4.9, 5, 50, 99, 100, Number.NaN, 60]);
    const excluded = Uint8Array.from([0, 0, 0, 0, 0, 0, 0, 1]);
    const bands = scoreSpread(scores, excluded, undefined, 20);
    expect(bands).toHaveLength(20);
    expect(bands[0]).toBe(2); // 0 and 4.9
    expect(bands[1]).toBe(1); // 5
    expect(bands[10]).toBe(1); // 50
    expect(bands[19]).toBe(2); // 99 and 100
    expect(bands.reduce((a, b) => a + b, 0)).toBe(6);
  });
});

describe("the choice of colouring", () => {
  const memory = (items: Record<string, string> = {}) => ({
    getItem: (key: string) => items[key] ?? null,
    setItem: (key: string, value: string) => {
      items[key] = value;
    },
  });

  it("starts with the score, and remembers the rank in the browser", () => {
    const store = memory();
    expect(loadColourBy(store)).toBe("score");
    saveColourBy("rank", store);
    expect(loadColourBy(store)).toBe("rank");
    expect(loadColourBy(memory({ [COLOUR_BY_KEY]: "nonsense" }))).toBe("score");
  });

  it("works with no storage, or blocked storage", () => {
    const blocked = {
      getItem: () => {
        throw new Error("blocked");
      },
      setItem: () => {
        throw new Error("blocked");
      },
    };
    expect(loadColourBy(null)).toBe("score");
    expect(loadColourBy(blocked)).toBe("score");
    expect(() => saveColourBy("rank", blocked)).not.toThrow();
  });
});

describe("middleOf", () => {
  it("names the scores between which the middle 80% of the cells lie, at the bands' edges", async () => {
    const { middleOf } = await import("./Legend");
    const spread = new Array(20).fill(0);
    spread[10] = 5; // 50 to 55
    spread[12] = 90; // 60 to 65
    spread[15] = 5; // 75 to 80
    expect(middleOf(spread)).toEqual([60, 65]);
    expect(middleOf(new Array(20).fill(0))).toBeNull();
  });
});

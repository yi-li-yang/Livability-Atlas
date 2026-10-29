import { describe, expect, it } from "vitest";
import { arcPath, slices, TURN, wrapName } from "./arcs";

const item = (id: string, value: number) => ({ id, value });

describe("slices", () => {
  it("shares the angle among the items in proportion to their values, in order", () => {
    const result = slices([item("a", 1), item("b", 1), item("c", 2)]);
    expect(result.map((s) => s.item.id)).toEqual(["a", "b", "c"]);
    expect(result.map((s) => [s.start, s.end])).toEqual([
      [0, TURN / 4],
      [TURN / 4, TURN / 2],
      [TURN / 2, TURN],
    ]);
  });

  it("leaves out an item whose value is 0 or less, and takes no space for it", () => {
    const result = slices([item("a", 1), item("b", 0), item("c", -3)]);
    expect(result.map((s) => s.item.id)).toEqual(["a"]);
    expect(result[0].end - result[0].start).toBeCloseTo(TURN, 12);
  });

  it("gives nothing where no item has a value", () => {
    expect(slices([])).toEqual([]);
    expect(slices([item("a", 0)])).toEqual([]);
  });

  it("fits the items into a part of the circle, as the sub-factors of a factor are", () => {
    const parent = slices([item("a", 1), item("b", 3)])[1];
    const kids = slices([item("x", 1), item("y", 1)], parent.start, parent.end);
    expect(kids[0].start).toBe(parent.start);
    expect(kids[1].end).toBe(parent.end);
    expect(kids[0].end - kids[0].start).toBeCloseTo(
      (parent.end - parent.start) / 2,
      12,
    );
  });

  it("ends exactly where it was told to, even where the shares do not divide evenly", () => {
    // Here (TURN * total) / total is not TURN: it is one rounding error short.
    const values = Array.from(
      { length: 6 },
      (_, n) => 0.1 * (n + 1) + 75 / 997,
    );
    const result = slices(values.map((value, n) => item(`i${n}`, value)));
    expect(result[result.length - 1].end).toBe(TURN);
  });

  it("ends exactly where it was told to, however many slices there are", () => {
    const many = Array.from({ length: 17 }, (_, n) => item(`i${n}`, 1 + n / 7));
    const result = slices(many);
    expect(result[0].start).toBe(0);
    expect(result[result.length - 1].end).toBe(TURN);
    for (let n = 1; n < result.length; n++) {
      expect(result[n].start).toBe(result[n - 1].end);
    }
  });
});

describe("arcPath", () => {
  it("draws a quarter of a ring from the top round to the right", () => {
    expect(arcPath(10, 20, 0, TURN / 4)).toBe(
      "M 0 -20 A 20 20 0 0 1 20 0 L 10 0 A 10 10 0 0 0 0 -10 Z",
    );
  });

  it("draws the next quarter, from the right round to the bottom", () => {
    expect(arcPath(10, 20, TURN / 4, TURN / 2)).toBe(
      "M 20 0 A 20 20 0 0 1 0 20 L 0 10 A 10 10 0 0 0 10 0 Z",
    );
  });

  it("flags an arc of more than half a turn as the long way round", () => {
    const path = arcPath(10, 20, 0, (TURN * 3) / 4);
    expect(path.split(" A ")[1].startsWith("20 20 0 1 1")).toBe(true);
    expect(path.split(" A ")[2].startsWith("10 10 0 1 0")).toBe(true);
  });

  it("draws a whole turn as two halves, which a single arc cannot be", () => {
    const path = arcPath(10, 20, 0, TURN);
    expect(path.match(/ A /g)).toHaveLength(4);
    expect(path).not.toContain("NaN");
    expect(
      path.startsWith("M 0 -20 A 20 20 0 0 1 0 20 A 20 20 0 0 1 0 -20 Z"),
    ).toBe(true);
    // The inner circle runs the other way, so that the ring has a hole when it is filled.
    expect(path).toContain("M 0 -10 A 10 10 0 0 0 0 10 A 10 10 0 0 0 0 -10 Z");
  });

  it("writes no minus zero and no long fractions", () => {
    const path = arcPath(10.123456, 20.987654, 0.1, 1.2);
    expect(path).not.toContain("-0 ");
    for (const number of path.match(/-?\d+\.\d+/g) ?? []) {
      expect(number.split(".")[1].length).toBeLessThanOrEqual(3);
    }
  });

  it("is a pie slice where the inner radius is 0", () => {
    const path = arcPath(0, 20, 0, TURN / 4);
    expect(path).toBe("M 0 -20 A 20 20 0 0 1 20 0 L 0 0 Z");
  });
});

describe("wrapName", () => {
  it("keeps a short name on one line", () => {
    expect(wrapName("Safety", 10)).toEqual(["Safety"]);
    expect(wrapName("All factors", 11)).toEqual(["All factors"]);
  });

  it("breaks a longer name between words, not inside them", () => {
    expect(wrapName("All factors", 10)).toEqual(["All", "factors"]);
    expect(wrapName("Community and people", 10)).toEqual([
      "Community",
      "and people",
    ]);
    expect(wrapName("Housing and cost", 10)).toEqual(["Housing", "and cost"]);
  });

  it("puts a word that is longer than a line on a line of its own", () => {
    expect(wrapName("Extraordinarily big", 8)).toEqual([
      "Extraordinarily",
      "big",
    ]);
  });

  it("stops at three lines and ends the last with an ellipsis", () => {
    expect(wrapName("one two three four five six seven", 7)).toEqual([
      "one two",
      "three",
      "four…",
    ]);
  });

  it("gives no lines for no name", () => {
    expect(wrapName("", 10)).toEqual([]);
    expect(wrapName("   ", 10)).toEqual([]);
  });
});

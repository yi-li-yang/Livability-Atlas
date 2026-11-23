import { describe, expect, it } from "vitest";
import { type Box, insetFor } from "./inset";

const box = (
  left: number,
  top: number,
  right: number,
  bottom: number,
): Box => ({
  left,
  top,
  right,
  bottom,
});

// A desktop map, 1440 by 850, and a phone map, 390 by 790.
const DESKTOP = box(0, 50, 1440, 900);
const PHONE = box(0, 54, 390, 844);

describe("insetFor", () => {
  it("is nothing when nothing covers the map", () => {
    expect(insetFor(DESKTOP, [])).toEqual({
      top: 0,
      right: 0,
      bottom: 0,
      left: 0,
    });
  });

  it("keeps the map clear of a panel down the left, and of a legend below it", () => {
    const panel = box(16, 66, 336, 620);
    const legend = box(16, 640, 240, 884);
    expect(insetFor(DESKTOP, [panel, legend])).toEqual({
      top: 0,
      right: 0,
      bottom: 0,
      left: 336,
    });
  });

  it("keeps the map clear of the reasons down the right too", () => {
    const panel = box(16, 66, 336, 620);
    const reasons = box(1104, 66, 1424, 780);
    expect(insetFor(DESKTOP, [panel, reasons])).toEqual({
      top: 0,
      right: 336,
      bottom: 0,
      left: 336,
    });
  });

  it("on a phone, keeps clear of the legend across the top and the sheet across the bottom", () => {
    const legend = box(8, 62, 382, 170);
    const sheet = box(0, 600, 390, 844);
    expect(insetFor(PHONE, [legend, sheet])).toEqual({
      top: 116,
      right: 0,
      bottom: 244,
      left: 0,
    });
  });

  it("ignores what lies outside the map, or is hidden (no size)", () => {
    const outside = box(0, 0, 1440, 50);
    const hidden = box(0, 0, 0, 0);
    expect(insetFor(DESKTOP, [outside, hidden])).toEqual({
      top: 0,
      right: 0,
      bottom: 0,
      left: 0,
    });
  });

  it("always leaves a third of the map clear, however much is covered", () => {
    const sheet = box(0, 120, 390, 844); // a sheet over nearly all of a phone's map
    const { top, bottom } = insetFor(PHONE, [sheet]);
    expect(PHONE.bottom - PHONE.top - top - bottom).toBeGreaterThanOrEqual(
      (PHONE.bottom - PHONE.top) / 3 - 1,
    );
  });
});

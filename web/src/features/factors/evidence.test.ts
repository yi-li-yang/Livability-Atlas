import { describe, expect, it } from "vitest";
import type { ManifestIndicator } from "../../generated/manifest.schema";
import { describeCurve, evidenceTypeText, formatValue } from "./evidence";

describe("formatValue", () => {
  it("puts a number before its unit and keeps a few significant figures", () => {
    expect(formatValue(7.4999, "minutes on foot")).toBe("7.5 minutes on foot");
    expect(formatValue(12.34, "minutes on foot")).toBe("12.3 minutes on foot");
    expect(formatValue(1234.5, "patients per full-time GP")).toBe(
      "1,235 patients per full-time GP",
    );
  });

  it("writes a percentage and pounds as people do", () => {
    expect(formatValue(12.34, "% of residents")).toBe("12.3% of residents");
    expect(formatValue(6102.4, "£ per m²")).toBe("£6,102 per m²");
    expect(formatValue(2207.55, "£ a year")).toBe("£2,208 a year");
  });

  it("names a category by its unit", () => {
    expect(formatValue("6b", "PTAL band")).toBe("PTAL band 6b");
    expect(formatValue("3", "fare zone")).toBe("fare zone 3");
  });

  it("says when there is no value", () => {
    expect(formatValue(null, "minutes")).toBe("No data here");
  });

  it("works without a unit", () => {
    expect(formatValue(3, "")).toBe("3");
  });
});

describe("describeCurve", () => {
  const unit = "minutes on foot";

  it("says where a ramp gives full marks and none, whichever way it runs", () => {
    expect(describeCurve({ shape: "ramp", t0: 15, t1: 5 }, unit)).toBe(
      "Full marks at 5 minutes on foot or less, none at 15 or more.",
    );
    expect(describeCurve({ shape: "ramp", t0: 0, t1: 100 }, "% of homes")).toBe(
      "Full marks at 100% of homes or more, none at 0 or less.",
    );
  });

  it("describes an ideal range by its flat top and its slopes", () => {
    expect(
      describeCurve(
        { shape: "ideal-range", l0: 30, l1: 40, u0: 55, u1: 70 },
        "dB",
      ),
    ).toBe("Full marks from 40 to 55 dB, falling to none at 30 and at 70.");
  });

  it("lists what a lookup gives each value", () => {
    expect(
      describeCurve(
        { shape: "lookup", scores: { "1": 1, "2": 0.5, "3": 0 } },
        "fare zone",
      ),
    ).toBe(
      "Each value has its own score: 1 gives 100%, 2 gives 50%, 3 gives 0%.",
    );
  });

  it("explains a percentile as a rank among the region's cells", () => {
    expect(describeCurve({ shape: "percentile", better: "higher" }, unit)).toBe(
      "Ranked against the region's other hex cells: the higher, the better.",
    );
    expect(describeCurve({ shape: "percentile", better: "lower" }, unit)).toBe(
      "Ranked against the region's other hex cells: the lower, the better.",
    );
  });

  it("says when an indicator has no curve", () => {
    expect(describeCurve(undefined, unit)).toBe("It has no scoring curve yet.");
  });
});

describe("evidenceTypeText", () => {
  it.each([
    ["direct", "Measured directly"],
    ["estimate", "An estimate, worked out approximately"],
    ["indirect", "Indirect: a sign of the thing, not the thing"],
    ["perception", "How people see the place"],
    ["ranking", "From a published ranking"],
  ] as const)("describes %s", (type, text) => {
    const indicator = { evidence_type: type } as ManifestIndicator;
    expect(evidenceTypeText(indicator.evidence_type)).toBe(text);
  });
});

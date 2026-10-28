import { describe, expect, it } from "vitest";
import type { FactorsFile } from "./factors.schema";

describe("generated catalogue types", () => {
  it("describe a factor tree", () => {
    const file: FactorsFile = {
      factors: [{ id: "safety", name: "Safety", default_weight: 4 }],
    };
    expect(file.factors[0].name).toBe("Safety");
  });
});

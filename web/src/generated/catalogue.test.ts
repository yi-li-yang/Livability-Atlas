import { describe, expect, it } from "vitest";
import type { Factor, FactorsFile } from "./factors.schema";

describe("generated catalogue types", () => {
  it("describe a factor tree", () => {
    const file: FactorsFile = {
      factors: [{ id: "safety", name: "Safety", default_weight: 4 }],
    };
    expect(file.factors[0].name).toBe("Safety");
  });

  it("require what the Pydantic models require", () => {
    // @ts-expect-error a factor without a name is not a Factor
    const nameless: Factor = { id: "safety", default_weight: 4 };
    expect(nameless.id).toBe("safety");
  });
});

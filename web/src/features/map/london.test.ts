import { describe, expect, it } from "vitest";
import { LONDON_BOUNDS, LONDON_CENTRE } from "./london";

describe("London view", () => {
  it("lists bounds as west, south, east, north", () => {
    const [west, south, east, north] = LONDON_BOUNDS;
    expect(west).toBeLessThan(east);
    expect(south).toBeLessThan(north);
  });

  it("has a centre inside its bounds", () => {
    const [west, south, east, north] = LONDON_BOUNDS;
    const [lng, lat] = LONDON_CENTRE;
    expect(lng).toBeGreaterThan(west);
    expect(lng).toBeLessThan(east);
    expect(lat).toBeGreaterThan(south);
    expect(lat).toBeLessThan(north);
  });
});

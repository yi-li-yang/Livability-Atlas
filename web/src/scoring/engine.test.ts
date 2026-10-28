import { readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { type ScoreCase, type ScoreResult, scoreCell } from "./engine";

const FIXTURES = fileURLToPath(
  new URL("../../../shared/fixtures/scoring/", import.meta.url),
);
const TOLERANCE = 1e-9;

interface Fixture extends ScoreCase {
  id: string;
  expected: ScoreResult;
}

const fixtures: Fixture[] = readdirSync(FIXTURES)
  .filter((name) => name.endsWith(".json"))
  .sort()
  .map((name) => JSON.parse(readFileSync(FIXTURES + name, "utf8")) as Fixture);

/** Asserts that `actual` is `expected`, numbers within the tolerance, and says where it is not. */
function same(actual: unknown, expected: unknown, where: string): void {
  if (expected === null || actual === null) {
    expect(actual, where).toBe(expected);
  } else if (typeof expected === "number") {
    expect(typeof actual, where).toBe("number");
    expect(Math.abs((actual as number) - expected), where).toBeLessThanOrEqual(
      TOLERANCE,
    );
  } else if (typeof expected === "object") {
    const want = expected as Record<string, unknown>;
    const got = actual as Record<string, unknown>;
    expect(Object.keys(got).sort(), where).toEqual(Object.keys(want).sort());
    for (const key of Object.keys(want))
      same(got[key], want[key], `${where}.${key}`);
  } else {
    expect(actual, where).toBe(expected);
  }
}

describe("the TypeScript scoring engine", () => {
  it("has the golden test cases to reproduce", () => {
    expect(fixtures.length).toBeGreaterThanOrEqual(15);
  });

  for (const fixture of fixtures) {
    it(`reproduces the golden case ${fixture.id}`, () => {
      same(scoreCell(fixture), fixture.expected, fixture.id);
    });
  }

  it("ignores the expected result in a case it is given", () => {
    const [first] = fixtures;
    const { expected: _, ...bare } = first;
    same(scoreCell(bare), first.expected, first.id);
  });
});

import type { Profile } from "./region";

/** One change of one weight and how much of the top places it leaves. */
export interface SensitivityScenario {
  /** The id of the factor whose weight changed. */
  factor: string;
  direction: "up" | "down";
  /** The places that lead with the changed weight. */
  top: string[];
  /** How many of the baseline top places are still among them. */
  kept: number;
}

export interface Sensitivity {
  /** The leading places for the profile as it is. */
  baseline: string[];
  scenarios: SensitivityScenario[];
  /**
   * How stable the leading places are, from 0 to 1: the mean over the scenarios of the share of
   * the baseline top places that stay. It is 1 where no change of weights moves them.
   */
  stability: number;
  /** For each baseline place, the share of the scenarios in which it stays in the top. */
  staysIn: Record<string, number>;
}

/** How much a weight changes in each scenario, as a share of the weight: 20%. */
export const CHANGE = 0.2;

/**
 * How stable the top places stay when the weights shift (scoring.md, section 12). Each of the
 * `factors` (id and current weight) is made `change` heavier, and then `change` lighter, one at a
 * time, with every other weight as the profile has it. `rank` gives the leading places, by name,
 * for a profile: the caller scores the region and ranks it, so this stays a pure computation.
 *
 * A factor with weight 0 is left out: a share of nothing is nothing. The profile it is given is
 * not changed.
 */
export function sensitivity(
  rank: (profile: Profile) => string[],
  profile: Profile,
  factors: Readonly<Record<string, number>>,
  options: { change?: number } = {},
): Sensitivity {
  const { change = CHANGE } = options;
  const baseline = rank(profile);
  const scenarios: SensitivityScenario[] = [];
  for (const [factor, weight] of Object.entries(factors)) {
    if (weight <= 0) continue;
    for (const [direction, scale] of [
      ["up", 1 + change],
      ["down", 1 - change],
    ] as const) {
      const top = rank({
        ...profile,
        weights: { ...profile.weights, [factor]: weight * scale },
      });
      const kept = baseline.filter((name) => top.includes(name)).length;
      scenarios.push({ factor, direction, top, kept });
    }
  }
  const share = (kept: number): number =>
    baseline.length === 0 ? 1 : kept / baseline.length;
  const stability =
    scenarios.length === 0
      ? 1
      : scenarios.reduce((sum, s) => sum + share(s.kept), 0) / scenarios.length;
  const staysIn = Object.fromEntries(
    baseline.map((name) => [
      name,
      scenarios.length === 0
        ? 1
        : scenarios.filter((s) => s.top.includes(name)).length /
          scenarios.length,
    ]),
  );
  return { baseline, scenarios, stability, staysIn };
}

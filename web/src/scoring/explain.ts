import type { Bundle } from "../data/bundle";
import type { ManifestFactor } from "../generated/manifest.schema";
import { scoreCell } from "./engine";
import { effectiveWeight, type Profile, scoreCaseFor } from "./region";

/** One factor's part in a hex cell's score. */
export interface FactorLine {
  id: string;
  name: string;
  /** From 0 (worst) to 1 (best), or null where the cell has no data for it. */
  score: number | null;
  /** The points of the livability score that it adds: the lines of a level add up to the score. */
  contribution: number | null;
  /** Its share of the weight in this cell, from 0 to 1, once what has no data is left out. */
  share: number | null;
  /** The factors inside it that count, or an empty list for a measured indicator. */
  children: FactorLine[];
}

export interface Explanation {
  /** The livability score from 0 to 100, or null where no factor has data. */
  score: number | null;
  /** Whether the score rests on thin data: under 70% of the weight has data. */
  lowCoverage: boolean;
  /** The top-level factors that count, in the catalogue's order. */
  factors: FactorLine[];
  /** The two best-scoring top-level factors, where they score above the middle. */
  strengths: FactorLine[];
  /** The worst-scoring top-level factor, where it scores below the middle. */
  weakness: FactorLine | null;
}

/** A factor scoring above this is a strength, and one scoring below it a weakness. */
const MIDDLE = 0.5;

/** Explains one cell's livability score, factor by factor, from the user's profile. */
export function explainCell(
  bundle: Bundle,
  profile: Profile,
  cellIndex: number,
): Explanation {
  const result = scoreCell(scoreCaseFor(bundle, profile, cellIndex));
  const line = (factor: ManifestFactor): FactorLine => {
    const node = result.nodes[factor.id];
    return {
      id: factor.id,
      name: factor.name,
      score: node?.score ?? null,
      contribution: node?.contribution ?? null,
      share: node?.effective_share ?? null,
      children: (factor.children ?? [])
        .filter((kid) => effectiveWeight(kid, profile) > 0)
        .map(line),
    };
  };
  const factors = bundle.manifest.factors
    .filter((factor) => effectiveWeight(factor, profile) > 0)
    .map(line);

  const scored = factors
    .filter((f): f is FactorLine & { score: number } => f.score !== null)
    .sort((a, b) => b.score - a.score);
  return {
    score: result.score,
    lowCoverage: result.low_coverage,
    factors,
    strengths: scored.filter((f) => f.score > MIDDLE).slice(0, 2),
    weakness:
      scored.length > 1 && scored[scored.length - 1].score < MIDDLE
        ? scored[scored.length - 1]
        : null,
  };
}

/**
 * The rank of a score among the region's scored cells: 1 for the best. Ties share the best rank.
 * `ascending` holds every finite score of the region, sorted from lowest to highest.
 */
export function rankOf(ascending: Float64Array, score: number): number {
  let lo = 0;
  let hi = ascending.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (ascending[mid] <= score) lo = mid + 1;
    else hi = mid;
  }
  return ascending.length - lo + 1;
}

/** The finite scores of a region, sorted from lowest to highest, for `rankOf`. */
export function sortedScores(scores: Float64Array): Float64Array {
  return Float64Array.from(scores.filter((s) => !Number.isNaN(s))).sort();
}

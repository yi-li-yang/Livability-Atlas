import {
  type Bundle,
  type Neighbourhood,
  neighbourhoodAt,
  type Value,
} from "../data/bundle";
import type {
  ManifestDataset,
  ManifestFactor,
  ManifestIndicator,
} from "../generated/manifest.schema";
import { scoreCell } from "./engine";
import {
  bestPickedOption,
  effectiveWeight,
  type Limit,
  type LimitResult,
  limitResultsFor,
  type Profile,
  scoreCaseFor,
} from "./region";

/** The evidence behind a measured indicator's score in one hex cell (interface layer 5). */
export interface Evidence {
  indicator: ManifestIndicator;
  /** The raw value in this cell, or null where there is none. */
  value: Value | null;
  /** For a choice indicator, the name of the picked option that scores best here. */
  option: string | null;
  /** The datasets the indicator is built from, with their licences and credits. */
  datasets: ManifestDataset[];
}

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
  /** For a measured indicator, its evidence here; null for a factor that holds others. */
  evidence: Evidence | null;
}

/** A hard limit and how this hex cell stands against it. */
export interface LimitLine {
  limit: Limit;
  /** The indicator the limit is on, or undefined where the bundle no longer has it. */
  indicator: ManifestIndicator | undefined;
  result: LimitResult;
}

export interface Explanation {
  /** The named neighbourhood the cell is in, or null where the bundle names none. */
  neighbourhood: Neighbourhood | null;
  /** The livability score from 0 to 100, or null where no factor has data. */
  score: number | null;
  /** Whether the score rests on thin data: under 70% of the weight has data. */
  lowCoverage: boolean;
  /** The top-level factors that count, in the catalogue's order. */
  factors: FactorLine[];
  /** The user's hard limits and the cell's result on each, in order. */
  limits: LimitLine[];
  /** Whether a failed hard limit leaves the cell out: greyed on the map and not ranked. */
  excluded: boolean;
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
  const evidenceOf = (factor: ManifestFactor): Evidence | null => {
    const indicator = bundle.manifest.indicators.find(
      (i) => i.id === factor.indicator,
    );
    if (!indicator) return null;
    const datasets = indicator.datasets.flatMap((id) =>
      bundle.manifest.datasets.filter((d) => d.id === id),
    );
    if (indicator.options) {
      const best = bestPickedOption(
        bundle,
        indicator,
        profile.choices?.[indicator.id],
        cellIndex,
      );
      return {
        indicator,
        value: best ? bundle.columns[best.option.column][cellIndex] : null,
        option: best?.option.name ?? null,
        datasets,
      };
    }
    return {
      indicator,
      value: bundle.columns[indicator.column][cellIndex],
      option: null,
      datasets,
    };
  };
  const line = (factor: ManifestFactor): FactorLine => {
    const node = result.nodes[factor.id];
    return {
      evidence: evidenceOf(factor),
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
  const limits = limitResultsFor(bundle, profile.limits ?? [], cellIndex).map(
    ({ limit, result }) => ({
      limit,
      result,
      indicator: bundle.manifest.indicators.find(
        (i) => i.id === limit.indicator,
      ),
    }),
  );
  return {
    neighbourhood: neighbourhoodAt(bundle, cellIndex),
    score: result.score,
    lowCoverage: result.low_coverage,
    limits,
    excluded: limits.some((l) => l.result === "fail"),
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

/**
 * The scores that count for ranking: those of the cells that no hard limit leaves out. A cell that
 * is left out is not ranked, so it is NaN here.
 */
export function rankableScores(
  scores: Float64Array,
  excluded: Uint8Array,
): Float64Array {
  return scores.map((score, i) => (excluded[i] ? Number.NaN : score));
}

/** The finite scores of a region, sorted from lowest to highest, for `rankOf`. */
export function sortedScores(scores: Float64Array): Float64Array {
  return Float64Array.from(scores.filter((s) => !Number.isNaN(s))).sort();
}

import type { Bundle } from "../data/bundle";
import type {
  ManifestFactor,
  ManifestIndicator,
} from "../generated/manifest.schema";
import { curveScore } from "./curves";
import type { ScoreCase, ScoreNode } from "./engine";

/** What the user has chosen. A weight that is absent is the factor's default weight. */
export interface Profile {
  /** Weights from 0 to 5, keyed by the id of a factor or measured indicator. */
  weights: Record<string, number>;
  /** Ids of measured indicators whose direction the user has flipped (1 - score). */
  flipped?: readonly string[];
}

/** The id of the tree's root, which holds the top-level factors. */
export const ROOT_ID = "livability";

const weightIn = (profile: Profile, factor: ManifestFactor): number =>
  profile.weights[factor.id] ?? factor.default_weight;

const kidsOf = (factor: ManifestFactor): ManifestFactor[] =>
  factor.children ?? [];

/** A composite factor whose children all weigh 0 counts as weight 0 (scoring.md). */
function effectiveWeight(factor: ManifestFactor, profile: Profile): number {
  const kids = kidsOf(factor);
  if (kids.length > 0 && kids.every((k) => effectiveWeight(k, profile) === 0))
    return 0;
  return weightIn(profile, factor);
}

const indicatorOf = (
  bundle: Bundle,
  id: string | null | undefined,
): ManifestIndicator | undefined =>
  bundle.manifest.indicators.find((i) => i.id === id);

/** The values of a column that a percentile curve compares a cell with. */
function regionValues(bundle: Bundle, indicator: ManifestIndicator): number[] {
  return bundle.columns[indicator.column].filter((v) => v !== null).map(Number);
}

/**
 * The score of every cell on one measured indicator, from 0 to 1, with NaN where the cell has no
 * value or the curve cannot score it. It does not depend on the weights, so it is worked out once
 * and reused for every change of weights. A flipped direction becomes 1 - score.
 */
export function leafScores(
  bundle: Bundle,
  indicator: ManifestIndicator,
  flipped = false,
): Float64Array {
  const values = bundle.columns[indicator.column];
  const out = new Float64Array(values.length).fill(Number.NaN);
  const curve = indicator.curve;
  if (!curve) return out;

  // A percentile needs the rank of a value among all of the region's, so sort them once.
  let sorted: Float64Array | undefined;
  if (curve.shape === "percentile") {
    sorted = Float64Array.from(regionValues(bundle, indicator)).sort();
  }
  const below = (x: number): number => {
    // The number of values < x, by binary search in the ascending array.
    let lo = 0;
    let hi = sorted?.length ?? 0;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if ((sorted as Float64Array)[mid] < x) lo = mid + 1;
      else hi = mid;
    }
    return lo;
  };
  const notAbove = (x: number): number => {
    // The number of values <= x.
    let lo = 0;
    let hi = sorted?.length ?? 0;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if ((sorted as Float64Array)[mid] <= x) lo = mid + 1;
      else hi = mid;
    }
    return lo;
  };

  for (let i = 0; i < values.length; i++) {
    const value = values[i];
    if (value === null) continue;
    let score: number | null;
    if (curve.shape === "percentile" && sorted) {
      const n = sorted.length;
      if (n === 1) {
        score = 0.5;
      } else {
        const x = Number(value);
        const lower = below(x);
        const ties = notAbove(x) - lower;
        const worse = curve.better === "lower" ? n - lower - ties : lower;
        score = (worse + 0.5 * (ties - 1)) / (n - 1);
      }
    } else {
      score = curveScore(curve, value);
    }
    if (score !== null) out[i] = flipped ? 1 - score : score;
  }
  return out;
}

/** The leaf scores of every measured indicator of a bundle, with the given directions flipped. */
export function allLeafScores(
  bundle: Bundle,
  flippedIds: readonly string[] = [],
): Map<string, Float64Array> {
  const flipped = new Set(flippedIds);
  return new Map(
    bundle.manifest.indicators.map((i) => [
      i.id,
      leafScores(bundle, i, flipped.has(i.id)),
    ]),
  );
}

/**
 * The livability score of every cell, from 0 to 100, with NaN where no factor has data. It is the
 * weighted mean of the children that have data, down the factor tree, as `scoreCell` computes it
 * for one cell, but without building a tree for each cell, so a change of weights recolours the
 * whole region quickly.
 */
export function scoreRegion(
  bundle: Bundle,
  profile: Profile,
  leaves: ReadonlyMap<string, Float64Array>,
): Float64Array {
  const size = bundle.cells.length;

  const scoreOf = (factor: ManifestFactor): Float64Array => {
    const kids = kidsOf(factor);
    if (kids.length === 0) {
      return (
        leaves.get(factor.indicator ?? "") ??
        new Float64Array(size).fill(Number.NaN)
      );
    }
    const total = new Float64Array(size);
    const sum = new Float64Array(size);
    for (const kid of kids) {
      const weight = effectiveWeight(kid, profile);
      if (weight === 0) continue;
      const scores = scoreOf(kid);
      for (let i = 0; i < size; i++) {
        if (!Number.isNaN(scores[i])) {
          total[i] += weight;
          sum[i] += weight * scores[i];
        }
      }
    }
    const out = new Float64Array(size);
    for (let i = 0; i < size; i++) {
      out[i] = total[i] > 0 ? sum[i] / total[i] : Number.NaN;
    }
    return out;
  };

  const root: ManifestFactor = {
    id: ROOT_ID,
    name: ROOT_ID,
    default_weight: 1,
    children: bundle.manifest.factors,
  };
  const scores = scoreOf(root);
  for (let i = 0; i < size; i++) scores[i] *= 100;
  return scores;
}

/** The scoring case for one cell, to explain its score with `scoreCell`. */
export function scoreCaseFor(
  bundle: Bundle,
  profile: Profile,
  cellIndex: number,
): ScoreCase {
  const flipped = new Set(profile.flipped);
  const build = (factor: ManifestFactor): ScoreNode => {
    const weight = weightIn(profile, factor);
    const kids = kidsOf(factor);
    if (kids.length > 0) {
      return { id: factor.id, weight, children: kids.map(build) };
    }
    const indicator = indicatorOf(bundle, factor.indicator);
    return {
      id: factor.id,
      weight,
      curve: indicator?.curve ?? undefined,
      value: indicator ? bundle.columns[indicator.column][cellIndex] : null,
      region_values:
        indicator?.curve?.shape === "percentile"
          ? regionValues(bundle, indicator)
          : undefined,
      flipped: indicator ? flipped.has(indicator.id) : false,
    };
  };
  return {
    tree: {
      id: ROOT_ID,
      weight: 1,
      children: bundle.manifest.factors.map(build),
    },
  };
}

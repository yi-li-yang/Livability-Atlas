import type { Bundle, Value } from "../data/bundle";
import type {
  ManifestFactor,
  ManifestIndicator,
  ManifestOption,
} from "../generated/manifest.schema";
import { curveScore } from "./curves";
import type { ScoreCase, ScoreNode } from "./engine";

/** What the user has chosen. A weight that is absent is the factor's default weight. */
export interface Profile {
  /** Weights from 0 to 5, keyed by the id of a factor or measured indicator. */
  weights: Record<string, number>;
  /** Ids of measured indicators whose direction the user has flipped (1 - score). */
  flipped?: readonly string[];
  /**
   * For each choice indicator, the ids of the options the user has picked. These stay in this
   * browser and out of shared links (D08): they can say a faith or an ethnic group.
   */
  choices?: Readonly<Record<string, readonly string[]>>;
  /** The must-have rules: a cell that fails one is greyed out and not ranked. */
  limits?: readonly Limit[];
}

/**
 * A must-have rule on the raw value of a measured indicator (docs/methodology/scoring.md, section
 * 6): at most a number, at least a number, or one of a list of categories.
 */
export type Limit = { indicator: string } & (
  | { max: number }
  | { min: number }
  | { in: readonly string[] }
);

export type LimitResult = "pass" | "fail" | "could_not_check";

/** The id of the tree's root, which holds the top-level factors. */
export const ROOT_ID = "livability";

export const weightIn = (profile: Profile, factor: ManifestFactor): number =>
  profile.weights[factor.id] ?? factor.default_weight;

const kidsOf = (factor: ManifestFactor): ManifestFactor[] =>
  factor.children ?? [];

/** A composite factor whose children all weigh 0 counts as weight 0 (scoring.md). */
export function effectiveWeight(
  factor: ManifestFactor,
  profile: Profile,
): number {
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
function regionValues(bundle: Bundle, column: string): number[] {
  return bundle.columns[column].filter((v) => v !== null).map(Number);
}

/** The options of a choice indicator that the user has picked and the bundle has. */
function pickedOptions(
  indicator: ManifestIndicator,
  picked: readonly string[] = [],
): ManifestOption[] {
  return (indicator.options ?? []).filter((o) => picked.includes(o.id));
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
  picked: readonly string[] = [],
): Float64Array {
  if (!indicator.options) {
    return columnScores(bundle, indicator.column, indicator.curve, flipped);
  }
  // A choice indicator scores the best of the options picked, in a fixed direction. With none
  // picked it has no score.
  const out = new Float64Array(bundle.cells.length).fill(Number.NaN);
  for (const option of pickedOptions(indicator, picked)) {
    const scores = columnScores(bundle, option.column, indicator.curve, false);
    for (let i = 0; i < out.length; i++) {
      if (Number.isNaN(scores[i])) continue;
      if (Number.isNaN(out[i]) || scores[i] > out[i]) out[i] = scores[i];
    }
  }
  return out;
}

/** The score of every cell on one column of the bundle, with the given curve. */
function columnScores(
  bundle: Bundle,
  column: string,
  curve: ManifestIndicator["curve"],
  flipped: boolean,
): Float64Array {
  const values = bundle.columns[column];
  const out = new Float64Array(values.length).fill(Number.NaN);
  if (!curve) return out;

  // A percentile needs the rank of a value among all of the region's, so sort them once.
  let sorted: Float64Array | undefined;
  if (curve.shape === "percentile") {
    sorted = Float64Array.from(regionValues(bundle, column)).sort();
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
  choices: Profile["choices"] = {},
): Map<string, Float64Array> {
  const flipped = new Set(flippedIds);
  return new Map(
    bundle.manifest.indicators.map((i) => [
      i.id,
      leafScores(bundle, i, flipped.has(i.id), choices?.[i.id]),
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

/**
 * The picked option of a choice indicator that scores best in one cell, or null where none of the
 * picked options has a value there.
 */
export function bestPickedOption(
  bundle: Bundle,
  indicator: ManifestIndicator,
  picked: readonly string[] | undefined,
  cellIndex: number,
): { option: ManifestOption; score: number } | null {
  let best: { option: ManifestOption; score: number } | null = null;
  for (const option of pickedOptions(indicator, picked)) {
    const score = columnScores(bundle, option.column, indicator.curve, false)[
      cellIndex
    ];
    if (!Number.isNaN(score) && (best === null || score > best.score)) {
      best = { option, score };
    }
  }
  return best;
}

/** The scoring case for one cell, to explain its score with `scoreCell`. */
export function scoreCaseFor(
  bundle: Bundle,
  profile: Profile,
  cellIndex: number,
): ScoreCase {
  const flipped = new Set(profile.flipped);
  /** A choice indicator in this cell: the picked option that scores best, with its own value. */
  const buildChoice = (
    factor: ManifestFactor,
    weight: number,
    indicator: ManifestIndicator,
  ): ScoreNode => {
    const best = bestPickedOption(
      bundle,
      indicator,
      profile.choices?.[indicator.id],
      cellIndex,
    );
    return {
      id: factor.id,
      weight,
      curve: indicator.curve ?? undefined,
      value: best ? bundle.columns[best.option.column][cellIndex] : null,
      region_values:
        best && indicator.curve?.shape === "percentile"
          ? regionValues(bundle, best.option.column)
          : undefined,
    };
  };
  const build = (factor: ManifestFactor): ScoreNode => {
    const weight = weightIn(profile, factor);
    const kids = kidsOf(factor);
    if (kids.length > 0) {
      return { id: factor.id, weight, children: kids.map(build) };
    }
    const indicator = indicatorOf(bundle, factor.indicator);
    if (indicator?.options) return buildChoice(factor, weight, indicator);
    return {
      id: factor.id,
      weight,
      curve: indicator?.curve ?? undefined,
      value: indicator ? bundle.columns[indicator.column][cellIndex] : null,
      region_values:
        indicator?.curve?.shape === "percentile"
          ? regionValues(bundle, indicator.column)
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

/** Whether a raw value meets a limit: a value that meets a number exactly passes. */
function checkValue(limit: Limit, value: Value | undefined): LimitResult {
  if (value === undefined || value === null) return "could_not_check";
  if ("max" in limit) return Number(value) <= limit.max ? "pass" : "fail";
  if ("min" in limit) return Number(value) >= limit.min ? "pass" : "fail";
  return limit.in.includes(String(value)) ? "pass" : "fail";
}

/** The result of each limit in one cell, in the order of the limits. A limit on an indicator that
 * the bundle does not have could not be checked. */
export function limitResultsFor(
  bundle: Bundle,
  limits: readonly Limit[],
  cellIndex: number,
): { limit: Limit; result: LimitResult }[] {
  return limits.map((limit) => {
    const indicator = indicatorOf(bundle, limit.indicator);
    const value =
      indicator && !indicator.options
        ? bundle.columns[indicator.column][cellIndex]
        : undefined;
    return { limit, result: checkValue(limit, value) };
  });
}

/**
 * Which cells the limits leave out (1) and which they keep (0), over the whole region. A cell is
 * left out if it fails any one limit. A cell that lacks the data a limit needs is kept: only a
 * failed limit excludes. `unchecked` is 1 where a kept cell could not be checked against some limit.
 */
export function checkLimits(
  bundle: Bundle,
  limits: readonly Limit[],
): { excluded: Uint8Array; unchecked: Uint8Array } {
  const size = bundle.cells.length;
  const excluded = new Uint8Array(size);
  const unchecked = new Uint8Array(size);
  for (const limit of limits) {
    const indicator = indicatorOf(bundle, limit.indicator);
    const values =
      indicator && !indicator.options
        ? bundle.columns[indicator.column]
        : undefined;
    for (let i = 0; i < size; i++) {
      const result = checkValue(limit, values?.[i]);
      if (result === "fail") excluded[i] = 1;
      else if (result === "could_not_check") unchecked[i] = 1;
    }
  }
  for (let i = 0; i < size; i++) if (excluded[i]) unchecked[i] = 0;
  return { excluded, unchecked };
}

/** The cells that the limits leave out: 1 where excluded. */
export const excludedCells = (
  bundle: Bundle,
  limits: readonly Limit[],
): Uint8Array => checkLimits(bundle, limits).excluded;

import { curveScore, type SetCurve } from "./curves";

/**
 * The scoring engine for one hex cell, as docs/methodology/scoring.md defines it. It reproduces the
 * golden test cases in `shared/fixtures/scoring/`, as the Python reference scorer
 * (`pipeline/src/atlas/scoring/engine.py`) does: the two must give the same numbers.
 */

/** A node of the factor tree: a factor with children, or a measured indicator with a value. */
export interface ScoreNode {
  id: string;
  weight: number;
  children?: ScoreNode[];
  curve?: SetCurve;
  /** The raw value in this hex cell, or null where it has none. */
  value?: number | string | null;
  /** For a percentile curve: the value of every cell of the region. */
  region_values?: number[];
  /** A flipped user direction: the score s becomes 1 - s. */
  flipped?: boolean;
}

/** A hard limit on a measured indicator's raw value or category. */
export type HardLimit = { id: string; indicator: string } & (
  | { max: number }
  | { min: number }
  | { in: (number | string)[] }
  | { not_in: (number | string)[] }
);

export interface ScoreCase {
  tree: ScoreNode;
  hard_limits?: HardLimit[];
}

export interface NodeResult {
  score: number | null;
  /** The share of the whole tree's weight, from the weights alone. */
  share: number;
  /** The share it carries in this hex cell, once parts without data are skipped. */
  effective_share: number | null;
  /** The points of the livability score that it adds. */
  contribution: number | null;
}

export type LimitResult = "pass" | "fail" | "could_not_check";

export interface ScoreResult {
  /** The livability score, 0 to 100 and unrounded, or null where no factor is active. */
  score: number | null;
  /** The share of the total weight that has data. */
  coverage: number;
  low_coverage: boolean;
  /** Whether a failed hard limit excludes the hex cell. */
  excluded: boolean;
  limits: Record<string, LimitResult>;
  nodes: Record<string, NodeResult>;
}

/** Data coverage below this share of the total weight is flagged. */
export const LOW_COVERAGE = 0.7;

const children = (node: ScoreNode): ScoreNode[] => node.children ?? [];

/** A composite factor whose children all weigh 0 counts as weight 0. */
function weightOf(node: ScoreNode): number {
  const kids = children(node);
  if (kids.length > 0 && kids.every((kid) => weightOf(kid) === 0)) return 0;
  return node.weight;
}

function ownScore(leaf: ScoreNode): number | null {
  if (leaf.value === undefined || leaf.value === null || !leaf.curve)
    return null;
  const score = curveScore(leaf.curve, leaf.value, leaf.region_values);
  if (score === null) return null;
  return leaf.flipped ? 1 - score : score;
}

function scoreOf(
  node: ScoreNode,
  scores: Map<string, number | null>,
): number | null {
  const kids = children(node);
  if (kids.length === 0) {
    const score = ownScore(node);
    scores.set(node.id, score);
    return score;
  }
  let total = 0;
  let weighted = 0;
  for (const kid of kids) {
    const score = scoreOf(kid, scores);
    const weight = weightOf(kid);
    if (weight > 0 && score !== null) {
      total += weight;
      weighted += weight * score;
    }
  }
  const score = total > 0 ? weighted / total : null;
  scores.set(node.id, score);
  return score;
}

function sharesOf(
  node: ScoreNode,
  share: number,
  out: Map<string, number>,
): void {
  out.set(node.id, share);
  const kids = children(node);
  const total = kids.reduce((sum, kid) => sum + weightOf(kid), 0);
  for (const kid of kids) {
    sharesOf(kid, total > 0 ? (share * weightOf(kid)) / total : 0, out);
  }
}

function effectiveOf(
  node: ScoreNode,
  share: number | null,
  scores: Map<string, number | null>,
  out: Map<string, number | null>,
): void {
  out.set(node.id, share);
  const kids = children(node);
  const active = kids.filter(
    (kid) => weightOf(kid) > 0 && scores.get(kid.id) !== null,
  );
  const total = active.reduce((sum, kid) => sum + weightOf(kid), 0);
  for (const kid of kids) {
    const isActive = share !== null && active.includes(kid);
    effectiveOf(
      kid,
      isActive && share !== null ? (share * weightOf(kid)) / total : null,
      scores,
      out,
    );
  }
}

function leavesOf(node: ScoreNode): ScoreNode[] {
  const kids = children(node);
  return kids.length === 0 ? [node] : kids.flatMap(leavesOf);
}

function checkLimit(
  limit: HardLimit,
  leaves: Map<string, ScoreNode>,
): LimitResult {
  const value = leaves.get(limit.indicator)?.value;
  if (value === undefined || value === null) return "could_not_check";
  if ("max" in limit) return Number(value) <= limit.max ? "pass" : "fail";
  if ("min" in limit) return Number(value) >= limit.min ? "pass" : "fail";
  if ("not_in" in limit) return limit.not_in.includes(value) ? "fail" : "pass";
  return limit.in.includes(value) ? "pass" : "fail";
}

/** Scores one hex cell: the livability score, coverage, hard limits, and every node's numbers. */
export function scoreCell(input: ScoreCase): ScoreResult {
  const { tree } = input;
  const scores = new Map<string, number | null>();
  scoreOf(tree, scores);
  const shares = new Map<string, number>();
  sharesOf(tree, 1, shares);
  const effective = new Map<string, number | null>();
  effectiveOf(tree, 1, scores, effective);

  const leaves = leavesOf(tree);
  const coverage = leaves.reduce(
    (sum, leaf) =>
      sum + (scores.get(leaf.id) !== null ? (shares.get(leaf.id) ?? 0) : 0),
    0,
  );
  const byId = new Map(leaves.map((leaf) => [leaf.id, leaf]));
  const limits: Record<string, LimitResult> = {};
  for (const limit of input.hard_limits ?? [])
    limits[limit.id] = checkLimit(limit, byId);

  const nodes: Record<string, NodeResult> = {};
  for (const [id, score] of scores) {
    const e = effective.get(id) ?? null;
    nodes[id] = {
      score,
      share: shares.get(id) ?? 0,
      effective_share: e,
      contribution: e === null || score === null ? null : 100 * e * score,
    };
  }
  const root = scores.get(tree.id) ?? null;
  return {
    score: root === null ? null : 100 * root,
    coverage,
    low_coverage: coverage < LOW_COVERAGE,
    excluded: Object.values(limits).includes("fail"),
    limits,
    nodes,
  };
}

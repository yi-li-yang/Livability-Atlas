import type { Bundle } from "../../data/bundle";

/** A neighbourhood and how its cells score. */
export interface TopNeighbourhood {
  name: string;
  /** The local authority it is in. */
  area: string;
  /** The mean score of its cells that count, from 0 to 100. */
  score: number;
  /** The index of its best-scoring cell, which the map goes to. */
  bestCell: number;
}

/** A neighbourhood needs this many cells with a score to be ranked, so that one cell is not one. */
const MINIMUM_CELLS = 3;

/**
 * The best neighbourhoods by the mean score of their cells (interface layer 1). A cell with no
 * score, or that a hard limit leaves out, does not count, and a neighbourhood with fewer than
 * `minimumCells` cells that count is left out.
 */
export function topNeighbourhoods(
  bundle: Bundle,
  scores: Float64Array,
  excluded: Uint8Array,
  options: { count?: number; minimumCells?: number } = {},
): TopNeighbourhood[] {
  const { count = 10, minimumCells = MINIMUM_CELLS } = options;
  const list = bundle.manifest.neighbourhoods;
  const of = bundle.neighbourhoodOf;
  if (!list || !of) return [];
  const sum = new Float64Array(list.length);
  const cells = new Int32Array(list.length);
  const best = new Int32Array(list.length).fill(-1);
  for (let i = 0; i < of.length; i++) {
    const position = of[i];
    if (position === null || Number.isNaN(scores[i]) || excluded[i]) continue;
    sum[position] += scores[i];
    cells[position] += 1;
    if (best[position] < 0 || scores[i] > scores[best[position]]) {
      best[position] = i;
    }
  }
  const ranked: TopNeighbourhood[] = [];
  for (let position = 0; position < list.length; position++) {
    if (cells[position] < minimumCells || cells[position] === 0) continue;
    ranked.push({
      name: list[position].name,
      area: list[position].area,
      score: sum[position] / cells[position],
      bestCell: best[position],
    });
  }
  return ranked.sort((a, b) => b.score - a.score).slice(0, count);
}

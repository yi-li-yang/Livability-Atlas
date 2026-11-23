import type { Store } from "../../profile/storage";
import { EXCLUDED, FEW_HOMES, PALETTE, type Rgba, UNSCORED } from "./colour";

/**
 * How the map colours its cells (D24): by the score itself, from 0 to 100, or by its rank in the
 * region, in fifths. The score is the default; the rank spreads the colours over the whole scale
 * when the scores bunch in the middle, as London's do.
 */
export type ColourBy = "score" | "rank";

/** Where the browser keeps the choice between visits. It is how the user likes to see the map, not what they want, so it is not in the link. */
export const COLOUR_BY_KEY = "atlas.colour-by.v1";

export function loadColourBy(store: Store | null): ColourBy {
  try {
    return store?.getItem(COLOUR_BY_KEY) === "rank" ? "rank" : "score";
  } catch {
    return "score"; // Storage is blocked: the score shows.
  }
}

export function saveColourBy(colourBy: ColourBy, store: Store | null): void {
  try {
    store?.setItem(COLOUR_BY_KEY, colourBy);
  } catch {
    // Storage can be full or blocked, as in a private window: the app works without it.
  }
}

/** Whether a cell counts: it has a score, homes, and passes the hard limits. */
const counts = (
  score: number,
  i: number,
  excluded?: Uint8Array,
  few?: Uint8Array,
) => !Number.isNaN(score) && !excluded?.[i] && !few?.[i];

/**
 * The colour of each cell by the fifth of the region it falls in, among the cells that count: the
 * bottom fifth takes the scale's red stop, the top fifth its blue-green stop. Equal scores share a
 * fifth. A cell that does not count keeps its own look (no fill, grey or no score).
 */
export function fifthColours(
  scores: Float64Array,
  excluded?: Uint8Array,
  few?: Uint8Array,
): Rgba[] {
  const counted = Float64Array.from(
    Array.from(scores).filter((s, i) => counts(s, i, excluded, few)),
  ).sort();
  const n = counted.length;
  /** How many counted scores are lower than `score`: a binary search in the sorted scores. */
  const below = (score: number) => {
    let low = 0;
    let high = n;
    while (low < high) {
      const middle = (low + high) >> 1;
      if (counted[middle] < score) low = middle + 1;
      else high = middle;
    }
    return low;
  };
  return Array.from(scores, (score, i) => {
    if (few?.[i]) return FEW_HOMES;
    if (excluded?.[i]) return EXCLUDED;
    if (Number.isNaN(score)) return UNSCORED;
    const fifth = Math.min(4, Math.floor((5 * below(score)) / n));
    return [...PALETTE[fifth], 255] as Rgba;
  });
}

/**
 * How many cells that count fall in each of `bands` equal bands of the 0 to 100 scale, for the
 * legend to show where the region's scores lie.
 */
export function scoreSpread(
  scores: Float64Array,
  excluded?: Uint8Array,
  few?: Uint8Array,
  bands = 20,
): number[] {
  const spread = new Array<number>(bands).fill(0);
  scores.forEach((score, i) => {
    if (!counts(score, i, excluded, few)) return;
    const band = Math.min(
      bands - 1,
      Math.max(0, Math.floor((score / 100) * bands)),
    );
    spread[band]++;
  });
  return spread;
}

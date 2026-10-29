import { cellToBoundary } from "h3-js";
import type { Bundle } from "../../data/bundle";
import { EXCLUDED, type Rgba, scoreToColour } from "./colour";

/** A hex cell as the map draws it. */
export interface HexCell {
  cell: string;
  /** The hexagon's corners as [longitude, latitude]. */
  polygon: [number, number][];
}

/** The bundle's cells as hexagons. Their shapes never change, so work them out once per bundle. */
export function toHexCells(bundle: Bundle): HexCell[] {
  return bundle.cells.map((cell) => ({
    cell,
    polygon: cellToBoundary(cell, true) as [number, number][],
  }));
}

/**
 * The colour of each cell, in the order of the cells, from livability scores of 0 to 100 (NaN: no
 * score). A cell that a hard limit leaves out (`excluded` is 1) is grey, whatever its score.
 */
export function cellColours(
  scores: Float64Array,
  excluded?: Uint8Array,
): Rgba[] {
  return Array.from(scores, (score, i) =>
    excluded?.[i]
      ? EXCLUDED
      : scoreToColour(Number.isNaN(score) ? null : score / 100),
  );
}

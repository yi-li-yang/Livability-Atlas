import { cellToBoundary } from "h3-js";
import type { Bundle } from "../../data/bundle";
import {
  EXCLUDED,
  FEW_HOMES,
  FEW_HOMES_OUTLINE,
  type Rgba,
  scoreToColour,
} from "./colour";

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
 * score). A cell with few or no homes (`few` is 1) has no fill, so that the map shows through. A
 * cell that a hard limit leaves out (`excluded` is 1) is grey, whatever its score.
 */
export function cellColours(
  scores: Float64Array,
  excluded?: Uint8Array,
  few?: Uint8Array,
): Rgba[] {
  return Array.from(scores, (score, i) => {
    if (few?.[i]) return FEW_HOMES;
    if (excluded?.[i]) return EXCLUDED;
    return scoreToColour(Number.isNaN(score) ? null : score / 100);
  });
}

const NO_OUTLINE: Rgba = [0, 0, 0, 0];

/** The outline of each cell: thin for a cell with few or no homes, and none for any other. */
export function cellOutlines(few: Uint8Array): Rgba[] {
  return Array.from(few, (f) => (f ? FEW_HOMES_OUTLINE : NO_OUTLINE));
}

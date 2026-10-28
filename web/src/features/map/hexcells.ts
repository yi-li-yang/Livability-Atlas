import { cellToBoundary } from "h3-js";
import type { Bundle, Value } from "../../data/bundle";
import { curveScore } from "../../scoring/curves";
import { type Rgba, scoreToColour } from "./colour";

/** A hex cell as the map draws it. */
export interface HexCell {
  cell: string;
  /** The hexagon's corners as [longitude, latitude]. */
  polygon: [number, number][];
  value: Value;
  /** From 0 (worst) to 1 (best), or null where the cell has no value or the curve cannot score it. */
  score: number | null;
  colour: Rgba;
}

/** The cells of a bundle, coloured by the score that one indicator's curve gives each raw value. */
export function toHexCells(bundle: Bundle, indicatorId: string): HexCell[] {
  const indicator = bundle.manifest.indicators.find(
    (i) => i.id === indicatorId,
  );
  if (!indicator)
    throw new Error(`The bundle holds no indicator ${indicatorId}`);
  const values = bundle.columns[indicator.column];
  return bundle.cells.map((cell, i) => {
    const value = values[i];
    const score =
      value === null || !indicator.curve
        ? null
        : curveScore(indicator.curve, value);
    return {
      cell,
      polygon: cellToBoundary(cell, true) as [number, number][],
      value,
      score,
      colour: scoreToColour(score),
    };
  });
}

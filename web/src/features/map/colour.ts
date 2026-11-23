export type Rgba = [number, number, number, number];

/**
 * One scale for every score in the app, on the map and in the bars: red is worse, yellow is
 * middling, blue-green is better. The good end leans to blue, not pure green, so that the two
 * ends and the quarters (0.25 against 0.75) stay apart in the common kinds of colour blindness:
 * checked with the dataviz skill's validator, every pair of stops at ΔE 12 or more under
 * simulated deuteranopia, protanopia and tritanopia. Scores just either side of the middle
 * (0.4 against 0.6) look alike to a red-green colour-blind reader, as in any red-to-green scale,
 * so the bars also show the score as a length and a number.
 */
export const PALETTE: [number, number, number][] = [
  [178, 54, 30], // #B2361E
  [224, 123, 57], // #E07B39
  [237, 200, 74], // #EDC84A
  [131, 197, 166], // #83C5A6
  [42, 143, 148], // #2A8F94
];

/** The colour of a score from 0 (worst) to 1 (best) as CSS, for the legend and the bars. */
export function scoreToCss(score: number): string {
  const [r, g, b] = scoreToColour(score);
  return `rgb(${r} ${g} ${b})`;
}

/** How much of a cell's colour shows over the basemap, until the user changes it. */
export const CELL_OPACITY = 0.5;

/** A hex cell that has no score: transparent, so that the map shows through. */
export const UNSCORED: Rgba = [128, 128, 128, 60];

/** A hex cell that a hard limit leaves out: a darker grey than one with no score, and not ranked. */
export const EXCLUDED: Rgba = [70, 70, 70, 175];

/**
 * A hex cell with few or no homes, such as a park, an airport or an industrial estate (D22): no
 * fill, so that the map shows what is there, and a thin outline in `FEW_HOMES_OUTLINE`.
 */
export const FEW_HOMES: Rgba = [0, 0, 0, 0];
export const FEW_HOMES_OUTLINE: Rgba = [90, 90, 90, 200];

/** The colour of a score from 0 (worst) to 1 (best), blended between the palette's stops. */
export function scoreToColour(score: number | null): Rgba {
  if (score === null) return UNSCORED;
  const position = Math.min(1, Math.max(0, score)) * (PALETTE.length - 1);
  const low = Math.floor(position);
  const high = Math.min(PALETTE.length - 1, low + 1);
  const t = position - low;
  const [r, g, b] = PALETTE[low].map((from, i) =>
    Math.round(from + (PALETTE[high][i] - from) * t),
  );
  return [r, g, b, 255];
}

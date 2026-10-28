export type Rgba = [number, number, number, number];

// Viridis, which stays readable in the common kinds of colour blindness and in greyscale.
export const PALETTE: [number, number, number][] = [
  [68, 1, 84],
  [71, 45, 123],
  [59, 82, 139],
  [44, 114, 142],
  [33, 145, 140],
  [40, 174, 128],
  [94, 201, 98],
  [173, 220, 48],
  [253, 231, 37],
];

/** How much of a cell's colour shows over the basemap, until the user changes it. */
export const CELL_OPACITY = 0.5;

/** A hex cell that has no score: transparent, so that the map shows through. */
export const UNSCORED: Rgba = [128, 128, 128, 60];

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

import type { Curve } from "../generated/manifest.schema";

/** A curve that is set, as the manifest gives it (the generated type also allows null). */
export type SetCurve = NonNullable<Curve>;

const clip = (x: number): number => Math.min(1, Math.max(0, x));

/** A user's band for a user-range indicator: the lowest and highest values that score in full. */
export type Band = readonly [number, number];

/**
 * An ideal range with the user's band in place of `l1` and `u1` (scoring.md, section 4). The slopes
 * keep the widths of the catalogue's curve, so `l0` and `u0` move with the band. Any other curve,
 * or no band, is returned as it is. The Python reference scorer's `with_band` does the same.
 */
export function withBand(curve: SetCurve, band: Band | undefined): SetCurve {
  if (!band || curve.shape !== "ideal-range") return curve;
  const [lo, hi] = band;
  return {
    ...curve,
    l0: lo - (curve.l1 - curve.l0),
    l1: lo,
    u1: hi,
    u0: hi + (curve.u0 - curve.u1),
  };
}

/**
 * The score of a raw value, from 0 (worst) to 1 (best), as docs/methodology/scoring.md, section 3
 * defines it, or null where the curve cannot score it: a category it does not list, or a percentile
 * without the region's values. The Python reference scorer gives the same numbers.
 */
export function curveScore(
  curve: SetCurve,
  value: number | string,
  regionValues?: readonly number[],
): number | null {
  switch (curve.shape) {
    case "ramp":
      return clip((Number(value) - curve.t0) / (curve.t1 - curve.t0));
    case "ideal-range": {
      const x = Number(value);
      const rising = clip((x - curve.l0) / (curve.l1 - curve.l0));
      const falling = clip((x - curve.u0) / (curve.u1 - curve.u0));
      return Math.min(rising, falling);
    }
    case "lookup":
      return curve.scores[String(value)] ?? null;
    case "percentile": {
      if (!regionValues || regionValues.length === 0) return null;
      if (regionValues.length === 1) return 0.5;
      const x = Number(value);
      const worse = regionValues.filter((v) =>
        curve.better === "lower" ? v > x : v < x,
      ).length;
      const ties = regionValues.filter((v) => v === x).length;
      return (worse + 0.5 * (ties - 1)) / (regionValues.length - 1);
    }
  }
}

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
 * A ramp's score: linear between t0 and t1, or on ln(value + offset) with `log` (D25). On a log
 * scale a value at or below -offset has no logarithm, and scores as the low end of the values.
 */
function rampScore(
  curve: Extract<SetCurve, { shape: "ramp" }>,
  x: number,
): number {
  const { t0, t1 } = curve;
  if (!curve.log) return clip((x - t0) / (t1 - t0));
  const offset = curve.offset ?? 0;
  if (x + offset <= 0) return t0 < t1 ? 0 : 1;
  const ln = (v: number) => Math.log(v + offset);
  return clip((ln(x) - ln(t0)) / (ln(t1) - ln(t0)));
}

/**
 * The score of a raw value, from 0 (worst) to 1 (best), as docs/methodology/scoring.md, section 3
 * defines it, or null where the curve cannot score it: a category it does not list. The Python
 * reference scorer gives the same numbers.
 */
export function curveScore(
  curve: SetCurve,
  value: number | string,
): number | null {
  switch (curve.shape) {
    case "ramp":
      return rampScore(curve, Number(value));
    case "ideal-range": {
      const x = Number(value);
      const rising = clip((x - curve.l0) / (curve.l1 - curve.l0));
      const falling = clip((x - curve.u0) / (curve.u1 - curve.u0));
      return Math.min(rising, falling);
    }
    case "lookup":
      return curve.scores[String(value)] ?? null;
  }
}

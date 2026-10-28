import type { Curve } from "../generated/manifest.schema";

/** A curve that is set, as the manifest gives it (the generated type also allows null). */
export type SetCurve = NonNullable<Curve>;

const clip = (x: number): number => Math.min(1, Math.max(0, x));

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

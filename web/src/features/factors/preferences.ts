import type { ManifestIndicator } from "../../generated/manifest.schema";
import type { Band } from "../../scoring/curves";
import type { Profile } from "../../scoring/region";

/**
 * Whether a higher value scores better on the catalogue's curve, before the user flips it, or
 * null where the curve does not say (a lookup or an ideal range).
 */
export function startsHigherIsBetter(
  indicator: ManifestIndicator,
): boolean | null {
  const curve = indicator.curve;
  if (curve?.shape === "ramp") return curve.t1 > curve.t0;
  return null;
}

/** Whether a higher value scores better for this user: the catalogue's way, unless flipped. */
export function higherIsBetter(
  profile: Profile,
  indicator: ManifestIndicator,
): boolean | null {
  const start = startsHigherIsBetter(indicator);
  if (start === null) return null;
  return profile.flipped?.includes(indicator.id) ? !start : start;
}

/** The profile with a user-direction indicator set so that higher (or lower) values score better. */
export function withDirection(
  profile: Profile,
  indicator: ManifestIndicator,
  higher: boolean,
): Profile {
  const start = startsHigherIsBetter(indicator);
  if (start === null) return profile;
  const others = (profile.flipped ?? []).filter((id) => id !== indicator.id);
  const flipped = higher === start ? others : [...others, indicator.id];
  const { flipped: _, ...rest } = profile;
  return flipped.length > 0 ? { ...rest, flipped } : rest;
}

/** The catalogue's band of an ideal range: the values that score in full. */
function defaultBand(indicator: ManifestIndicator): Band | null {
  const curve = indicator.curve;
  return curve?.shape === "ideal-range" ? [curve.l1, curve.u1] : null;
}

/** The band of a user-range indicator that scores in full: the user's, or the catalogue's. */
export function bandOf(
  profile: Profile,
  indicator: ManifestIndicator,
): Band | null {
  return profile.ranges?.[indicator.id] ?? defaultBand(indicator);
}

/**
 * The profile with the band of a user-range indicator set, its ends in order. A band that is the
 * catalogue's own, or null, clears the user's.
 */
export function withRange(
  profile: Profile,
  indicator: ManifestIndicator,
  band: Band | null,
): Profile {
  const { [indicator.id]: _, ...others } = profile.ranges ?? {};
  const fallback = defaultBand(indicator);
  const ordered: Band | null = band
    ? [Math.min(...band), Math.max(...band)]
    : null;
  const isDefault =
    ordered === null ||
    (fallback !== null &&
      ordered[0] === fallback[0] &&
      ordered[1] === fallback[1]);
  const ranges = isDefault ? others : { ...others, [indicator.id]: ordered };
  const { ranges: __, ...rest } = profile;
  return Object.keys(ranges).length > 0 ? { ...rest, ranges } : rest;
}

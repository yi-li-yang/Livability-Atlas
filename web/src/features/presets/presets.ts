import type {
  ManifestLimit,
  ManifestPreset,
} from "../../generated/manifest.schema";
import { encodeProfile } from "../../profile/storage";
import type { Limit, Profile } from "../../scoring/region";

/** A preset's limit as the profile holds one, or null where it sets no bound. */
function toLimit(limit: ManifestLimit): Limit | null {
  const { indicator } = limit;
  if (typeof limit.max === "number") return { indicator, max: limit.max };
  if (typeof limit.min === "number") return { indicator, min: limit.min };
  if (limit.in) return { indicator, in: limit.in };
  return null;
}

/**
 * The profile that starts from a preset: its weights, directions and limits replace the user's,
 * and what it does not name is at its default. What is the user's own stays: the choices (a faith
 * or a group), the bands and the way scores combine.
 */
export function fromPreset(profile: Profile, preset: ManifestPreset): Profile {
  const { choices, ranges, mode } = profile;
  const limits = (preset.limits ?? [])
    .map(toLimit)
    .filter((l): l is Limit => l !== null);
  return {
    weights: { ...(preset.weights ?? {}) },
    ...(preset.flipped?.length ? { flipped: [...preset.flipped] } : {}),
    ...(limits.length > 0 ? { limits } : {}),
    ...(choices ? { choices } : {}),
    ...(ranges ? { ranges } : {}),
    ...(mode ? { mode } : {}),
  };
}

/**
 * The preset that the profile is still exactly at, or null: a change of any weight, direction or
 * limit leaves it. Choices, bands and the scoring mode do not count.
 */
export function matchingPreset(
  profile: Profile,
  presets: readonly ManifestPreset[],
): ManifestPreset | null {
  const ownParts = ({ weights, flipped, limits }: Profile) =>
    encodeProfile({ weights, flipped, limits });
  const now = ownParts(profile);
  return (
    presets.find((p) => ownParts(fromPreset({ weights: {} }, p)) === now) ??
    null
  );
}

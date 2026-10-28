import type { Profile } from "../scoring/region";

/** Where the browser keeps the profile between visits. */
export const STORAGE_KEY = "atlas.profile.v1";

const ID = /^[a-z0-9][a-z0-9-]*$/;
const MAX_WEIGHT = 5;

/** The profile as text for the URL's fragment: `w=transport:0,safety:5&f=crime`. */
export function encodeProfile(profile: Profile): string {
  const parts: string[] = [];
  const weights = Object.entries(profile.weights).map(
    ([id, weight]) => `${id}:${weight}`,
  );
  if (weights.length > 0) parts.push(`w=${weights.join(",")}`);
  if (profile.flipped && profile.flipped.length > 0) {
    parts.push(`f=${profile.flipped.join(",")}`);
  }
  return parts.join("&");
}

/**
 * The profile that text from the URL or the browser's storage holds. Anything malformed is left
 * out, never an error: the text comes from outside, and a bad link must not break the app.
 */
export function decodeProfile(text: string): Profile {
  const params = new URLSearchParams(text.replace(/^#/, ""));
  const weights: Record<string, number> = {};
  for (const entry of (params.get("w") ?? "").split(",")) {
    const [id, value, ...rest] = entry.split(":");
    const weight = Number(value);
    if (
      rest.length === 0 &&
      ID.test(id ?? "") &&
      value !== undefined &&
      value !== "" &&
      Number.isInteger(weight) &&
      weight >= 0 &&
      weight <= MAX_WEIGHT
    ) {
      weights[id] = weight;
    }
  }
  const flipped = (params.get("f") ?? "")
    .split(",")
    .filter((id) => ID.test(id));
  return flipped.length > 0 ? { weights, flipped } : { weights };
}

/** Keeps only the weights and directions of ids that the region's factor tree has. */
export function pruneProfile(
  profile: Profile,
  known: ReadonlySet<string>,
): Profile {
  const weights = Object.fromEntries(
    Object.entries(profile.weights).filter(([id]) => known.has(id)),
  );
  const flipped = (profile.flipped ?? []).filter((id) => known.has(id));
  return flipped.length > 0 ? { weights, flipped } : { weights };
}

/** The part of `Storage` that the profile uses, so that tests can stand in for it. */
export interface Store {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

/**
 * The profile to start with: the one in the link if it has one (so a shared link wins), else the
 * one saved in this browser, else none. Reading may throw where storage is blocked.
 */
export function loadProfile(fragment: string, store: Store | null): Profile {
  const fromLink = decodeProfile(fragment);
  if (encodeProfile(fromLink) !== "") return fromLink;
  try {
    return decodeProfile(store?.getItem(STORAGE_KEY) ?? "");
  } catch {
    return { weights: {} };
  }
}

/** Saves the profile in the browser. It stays there: nothing is sent anywhere (D08). */
export function saveProfile(profile: Profile, store: Store | null): void {
  try {
    store?.setItem(STORAGE_KEY, encodeProfile(profile));
  } catch {
    // Storage can be full or blocked, as in a private window: the app works without it.
  }
}

import type { Limit, Profile } from "../scoring/region";

/** Where the browser keeps the profile between visits. */
export const STORAGE_KEY = "atlas.profile.v1";

const ID = /^[a-z0-9][a-z0-9-]*$/;
const NUMBER = /^\d+(\.\d+)?$/;
const CATEGORY = /^[a-z0-9]+$/i;
const MAX_WEIGHT = 5;

/** A limit as `indicator:kind:value`, a list of categories joined by dots. */
function encodeLimit(limit: Limit): string {
  if ("max" in limit) return `${limit.indicator}:max:${limit.max}`;
  if ("min" in limit) return `${limit.indicator}:min:${limit.min}`;
  return `${limit.indicator}:in:${limit.in.join(".")}`;
}

/** The limit that a piece of text holds, or null where it is not well formed. */
function decodeLimit(text: string): Limit | null {
  const [indicator, kind, value, ...rest] = text.split(":");
  if (rest.length > 0 || !ID.test(indicator ?? "") || value === undefined) {
    return null;
  }
  if ((kind === "max" || kind === "min") && NUMBER.test(value)) {
    return kind === "max"
      ? { indicator, max: Number(value) }
      : { indicator, min: Number(value) };
  }
  const categories = value.split(".");
  if (kind === "in" && categories.every((c) => CATEGORY.test(c))) {
    return { indicator, in: categories };
  }
  return null;
}

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
  if (profile.limits && profile.limits.length > 0) {
    parts.push(`l=${profile.limits.map(encodeLimit).join(",")}`);
  }
  return parts.join("&");
}

/**
 * The profile as text for the browser's storage: the link's text and the choices, as
 * `c=faith:hindu.sikh,your-community:ethnic-indian`. Choices can say a faith or an ethnic group,
 * so they go no further than this browser (D08).
 */
export function encodeStored(profile: Profile): string {
  const choices = Object.entries(profile.choices ?? {})
    .filter(([, options]) => options.length > 0)
    .map(([id, options]) => `${id}:${options.join(".")}`);
  const link = encodeProfile(profile);
  return choices.length > 0
    ? `${link}${link ? "&" : ""}c=${choices.join(",")}`
    : link;
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
  const choices: Record<string, string[]> = {};
  for (const entry of (params.get("c") ?? "").split(",")) {
    const [id, list, ...rest] = entry.split(":");
    const options = (list ?? "").split(".");
    if (
      rest.length === 0 &&
      ID.test(id ?? "") &&
      options.length > 0 &&
      options.every((option) => ID.test(option))
    ) {
      choices[id] = options;
    }
  }
  const limits = (params.get("l") ?? "")
    .split(",")
    .map(decodeLimit)
    .filter((limit): limit is Limit => limit !== null);
  return {
    weights,
    ...(flipped.length > 0 ? { flipped } : {}),
    ...(Object.keys(choices).length > 0 ? { choices } : {}),
    ...(limits.length > 0 ? { limits } : {}),
  };
}

/**
 * Keeps only the weights, directions and choices of ids that the region's factor tree has. An
 * option is known as `indicator:option`.
 */
export function pruneProfile(
  profile: Profile,
  known: ReadonlySet<string>,
): Profile {
  const weights = Object.fromEntries(
    Object.entries(profile.weights).filter(([id]) => known.has(id)),
  );
  const flipped = (profile.flipped ?? []).filter((id) => known.has(id));
  const choices = Object.fromEntries(
    Object.entries(profile.choices ?? {})
      .filter(([id]) => known.has(id))
      .map(([id, options]) => [
        id,
        options.filter((option) => known.has(`${id}:${option}`)),
      ])
      .filter(([, options]) => options.length > 0),
  );
  const limits = (profile.limits ?? []).filter((limit) =>
    known.has(limit.indicator),
  );
  return {
    weights,
    ...(flipped.length > 0 ? { flipped } : {}),
    ...(Object.keys(choices).length > 0 ? { choices } : {}),
    ...(limits.length > 0 ? { limits } : {}),
  };
}

/** The profile without its choices. */
function withoutChoices({ choices: _, ...rest }: Profile): Profile {
  return rest;
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
  const fromLink = withoutChoices(decodeProfile(fragment));
  let saved: Profile = { weights: {} };
  try {
    saved = decodeProfile(store?.getItem(STORAGE_KEY) ?? "");
  } catch {
    // Storage is blocked: the link alone speaks.
  }
  // A link wins over what is saved, but only for the weights and directions. The choices are
  // this browser's own: a link never carries them.
  const base = encodeProfile(fromLink) !== "" ? fromLink : saved;
  return saved.choices ? { ...base, choices: saved.choices } : base;
}

/** Saves the profile in the browser. It stays there: nothing is sent anywhere (D08). */
export function saveProfile(profile: Profile, store: Store | null): void {
  try {
    store?.setItem(STORAGE_KEY, encodeStored(profile));
  } catch {
    // Storage can be full or blocked, as in a private window: the app works without it.
  }
}

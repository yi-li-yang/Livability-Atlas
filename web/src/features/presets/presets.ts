import type {
  ManifestFactor,
  ManifestLimit,
  ManifestPreset,
} from "../../generated/manifest.schema";
import { encodeProfile } from "../../profile/storage";
import { type Limit, type Profile, weightIn } from "../../scoring/region";
import { CHOSEN_WEIGHT } from "../factors/level";

/** A preset's limit as the profile holds one, or null where it sets no bound. */
function toLimit(limit: ManifestLimit): Limit | null {
  const { indicator } = limit;
  if (typeof limit.max === "number") return { indicator, max: limit.max };
  if (typeof limit.min === "number") return { indicator, min: limit.min };
  if (limit.in) return { indicator, in: limit.in };
  return null;
}

/** The factors from the top down to the one with this id, or null where the tree lacks it. */
function pathTo(
  factors: readonly ManifestFactor[],
  id: string,
): ManifestFactor[] | null {
  for (const factor of factors) {
    if (factor.id === id) return [factor];
    const inside = pathTo(factor.children ?? [], id);
    if (inside) return [factor, ...inside];
  }
  return null;
}

/** The ids of the factors that hold a picked choice, down to the choice itself. */
function choicePaths(
  profile: Profile,
  factors: readonly ManifestFactor[],
): Set<string> {
  const ids = new Set<string>();
  for (const [id, picks] of Object.entries(profile.choices ?? {})) {
    if (picks.length === 0) continue;
    for (const node of pathTo(factors, id) ?? []) ids.add(node.id);
  }
  return ids;
}

/**
 * The profile with every picked choice counting: a choice factor, or a factor that holds it, at
 * weight 0 takes the weight it had in `previous`, or the weight of a first pick. A pick that counts
 * for nothing would look kept and do nothing.
 */
function withChoiceWeights(
  profile: Profile,
  factors: readonly ManifestFactor[],
  previous: Profile,
): Profile {
  const weights = { ...profile.weights };
  for (const [id, picks] of Object.entries(profile.choices ?? {})) {
    if (picks.length === 0) continue;
    for (const node of pathTo(factors, id) ?? []) {
      if (weightIn({ ...profile, weights }, node) > 0) continue;
      const old = weightIn(previous, node);
      weights[node.id] = old > 0 ? old : CHOSEN_WEIGHT;
    }
  }
  return { ...profile, weights };
}

/** A profile from parts, leaving out the parts that are empty. */
function assemble(parts: Profile): Profile {
  const { weights, flipped, limits, choices, ranges, mode, everything } = parts;
  return {
    weights,
    ...(flipped?.length ? { flipped } : {}),
    ...(limits?.length ? { limits } : {}),
    ...(choices ? { choices } : {}),
    ...(ranges ? { ranges } : {}),
    ...(mode ? { mode } : {}),
    ...(everything ? { everything } : {}),
  };
}

/** A way to start: a preset of the catalogue, or one of the two starts, which may count everything. */
export type StartFrom = ManifestPreset & { everything?: true };

/** Names joined as a person lists them: "a, b and c". */
function listed(names: readonly string[]): string {
  return names.length < 2
    ? (names[0] ?? "")
    : `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}`;
}

/**
 * The two ways to start that come before the catalogue's presets (D14): a few essentials, which is
 * where a new user starts, and everything at its default weight. None where the tree holds no
 * essential, as then everything counts from the start.
 */
export function startEntries(factors: readonly ManifestFactor[]): StartFrom[] {
  const essentials: string[] = [];
  const walk = (nodes: readonly ManifestFactor[]) => {
    for (const node of nodes) {
      if (node.starts_counted) essentials.push(node.name);
      else walk(node.children ?? []);
    }
  };
  walk(factors);
  if (essentials.length === 0) return [];
  return [
    {
      id: "a-few-essentials",
      name: "A few essentials",
      description: `Only a few things count to start with: ${listed(essentials)}. Count anything else that matters to you from Not counted.`,
    },
    {
      id: "everything-equally",
      name: "Everything, equally",
      description:
        "Every factor counts, nearly all at the same weight. Set what does not matter to you to 0.",
      everything: true,
    },
  ];
}

/**
 * The profile that starts from a preset: its weights, directions and limits replace the user's,
 * and what it does not name is at its start weight (D14). What is the user's own stays: the choices (a faith
 * or a group, which keep counting), the bands and the way scores combine.
 */
export function fromPreset(
  profile: Profile,
  preset: StartFrom,
  factors: readonly ManifestFactor[],
): Profile {
  const limits = (preset.limits ?? [])
    .map(toLimit)
    .filter((l): l is Limit => l !== null);
  const base = assemble({
    weights: { ...(preset.weights ?? {}) },
    flipped: preset.flipped ? [...preset.flipped] : undefined,
    limits,
    choices: profile.choices,
    ranges: profile.ranges,
    mode: profile.mode,
    everything: preset.everything,
  });
  return withChoiceWeights(base, factors, profile);
}

/**
 * The profile before a preset, with what has changed since that is the user's own kept: the
 * weights, directions and limits come back, and the choices, bands and mode stay as they are now.
 */
export function undoPreset(
  now: Profile,
  before: Profile,
  factors: readonly ManifestFactor[],
): Profile {
  const base = assemble({
    weights: { ...before.weights },
    flipped: before.flipped,
    limits: before.limits,
    choices: now.choices,
    ranges: now.ranges,
    mode: now.mode,
    everything: before.everything,
  });
  return withChoiceWeights(base, factors, now);
}

/**
 * What a preset sets, in a form that two profiles with the same effect share: the weight of every
 * factor (default or not), and the directions and limits in a fixed order. The factors that hold a
 * picked choice are left out, since their weights are the user's own.
 */
function key(
  profile: Profile,
  factors: readonly ManifestFactor[],
  skip: ReadonlySet<string>,
): string {
  const weights: string[] = [];
  const walk = (nodes: readonly ManifestFactor[]) => {
    for (const node of nodes) {
      if (!skip.has(node.id)) {
        weights.push(`${node.id}:${weightIn(profile, node)}`);
      }
      walk(node.children ?? []);
    }
  };
  walk(factors);
  const limits = [...(profile.limits ?? [])].sort((a, b) =>
    a.indicator.localeCompare(b.indicator),
  );
  return `${weights.join(",")}|${encodeProfile({
    weights: {},
    flipped: [...(profile.flipped ?? [])].sort(),
    limits,
  })}`;
}

/**
 * The preset that the profile is still at, or null: a change of any weight, direction or limit
 * leaves it. Choices, bands and the scoring mode do not count.
 */
export function matchingPreset<P extends StartFrom>(
  profile: Profile,
  presets: readonly P[],
  factors: readonly ManifestFactor[],
): P | null {
  const skip = choicePaths(profile, factors);
  const now = key(profile, factors, skip);
  return (
    presets.find(
      (p) =>
        key(
          fromPreset({ weights: {}, choices: profile.choices }, p, factors),
          factors,
          skip,
        ) === now,
    ) ?? null
  );
}

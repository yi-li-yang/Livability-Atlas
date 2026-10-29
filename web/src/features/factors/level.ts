import type { ManifestFactor } from "../../generated/manifest.schema";
import { effectiveWeight, type Profile, weightIn } from "../../scoring/region";
import { type FactorColour, factorColour } from "./colours";

/** One factor, as the factor tree shows it at the level the user has opened. */
export interface FactorView {
  /** The factor in the manifest's tree. */
  factor: ManifestFactor;
  id: string;
  name: string;
  /** The weight the user has set, or the default weight where they have set none. */
  weight: number;
  defaultWeight: number;
  /** Its weight in the score: 0 where it, or everything inside it, is at weight 0. */
  effectiveWeight: number;
  /** Its share of the weight at this level, from 0 to 1: its weight over its siblings' total. */
  share: number;
  /** Whether it opens into sub-factors. */
  opens: boolean;
  /** Its colour: the top-level factor's own, or the tint of the top-level factor it is in. */
  colour: string;
  /** The text colour that reads on `colour`. */
  ink: string;
}

export interface Level {
  /** The factors opened to reach this level, outermost first. Empty at the top. */
  trail: { id: string; name: string; factor: ManifestFactor }[];
  /** The factors that count in the score, in the catalogue's order. */
  counted: FactorView[];
  /** The factors at weight 0, which the drawing leaves out. */
  notCounted: FactorView[];
}

const kidsOf = (factor: ManifestFactor): ManifestFactor[] =>
  factor.children ?? [];

/**
 * The factors at the level that `path` opens. `path` lists the ids of the factors opened from the
 * top; a path that leaves the tree stops where it does.
 */
export function levelAt(
  factors: readonly ManifestFactor[],
  profile: Profile,
  path: readonly string[],
): Level {
  const trail: Level["trail"] = [];
  let siblings = factors;
  let top: { factor: ManifestFactor; position: number } | null = null;
  for (const id of path) {
    const position = siblings.findIndex((f) => f.id === id);
    if (position < 0 || kidsOf(siblings[position]).length === 0) break;
    const factor = siblings[position];
    top ??= { factor, position };
    trail.push({ id: factor.id, name: factor.name, factor });
    siblings = kidsOf(factor);
  }

  const total = siblings.reduce(
    (sum, f) => sum + effectiveWeight(f, profile),
    0,
  );
  const views = siblings.map((factor, index): FactorView => {
    const own = top ?? { factor, position: index };
    const colour: FactorColour = factorColour(own.factor.id, own.position);
    const weight = effectiveWeight(factor, profile);
    return {
      factor,
      id: factor.id,
      name: factor.name,
      weight: weightIn(profile, factor),
      defaultWeight: factor.default_weight,
      effectiveWeight: weight,
      share: total > 0 ? weight / total : 0,
      opens: kidsOf(factor).length > 0,
      colour: top ? colour.tint : colour.base,
      ink: top ? "#1c1c1c" : "#ffffff",
    };
  });
  return {
    trail,
    counted: views.filter((v) => v.effectiveWeight > 0),
    notCounted: views.filter((v) => v.effectiveWeight === 0),
  };
}

/** The profile with one weight set. */
export function withWeight(
  profile: Profile,
  id: string,
  weight: number,
): Profile {
  return { ...profile, weights: { ...profile.weights, [id]: weight } };
}

/** The weight a choice factor gets when the user picks its first option: the middle of the scale. */
export const CHOSEN_WEIGHT = 3;

/**
 * The profile with one option of a choice indicator picked or cleared. A choice factor starts at
 * weight 0 (D18), so the first pick gives it a weight, and clearing the last option takes it back.
 * The factors opened to reach it (`ancestors`) that are at weight 0 get the same weight, or the
 * pick would count for nothing.
 */
export function withChoice(
  profile: Profile,
  factor: ManifestFactor,
  option: string,
  picked: boolean,
  ancestors: readonly ManifestFactor[] = [],
): Profile {
  const now = profile.choices?.[factor.id] ?? [];
  const next = picked
    ? [...new Set([...now, option])]
    : now.filter((o) => o !== option);
  const { [factor.id]: _, ...others } = profile.choices ?? {};
  const choices = next.length > 0 ? { ...others, [factor.id]: next } : others;
  const weights = { ...profile.weights };
  if (next.length === 0) weights[factor.id] = 0;
  else {
    for (const f of [factor, ...ancestors]) {
      if (weightIn(profile, f) === 0) weights[f.id] = CHOSEN_WEIGHT;
    }
  }
  const { choices: __, ...rest } = profile;
  return Object.keys(choices).length > 0
    ? { ...rest, weights, choices }
    : { ...rest, weights };
}

/**
 * The profile with a factor counted again: the weights set inside it are cleared, so that it and
 * everything in it return to their default weights, and a factor whose default is 0 gets 1.
 */
export function countAgain(profile: Profile, factor: ManifestFactor): Profile {
  const weights = { ...profile.weights };
  const clear = (f: ManifestFactor): void => {
    delete weights[f.id];
    for (const kid of kidsOf(f)) clear(kid);
  };
  clear(factor);
  const restored: Profile = { ...profile, weights };
  return effectiveWeight(factor, restored) > 0
    ? restored
    : withWeight(restored, factor.id, 1);
}

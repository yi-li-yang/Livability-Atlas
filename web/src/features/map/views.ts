import type { Manifest, ManifestFactor } from "../../generated/manifest.schema";
import { effectiveWeight, type Profile } from "../../scoring/region";

/** One thing the map can show in place of the livability score. */
export interface ViewOption {
  /** The id of the factor or measured indicator. */
  id: string;
  name: string;
  /** How far down the factor tree it is: 0 for a top-level factor. */
  depth: number;
  /** The id of the top-level factor it is in, which keys its group in the list. */
  groupId: string;
  /** That factor's name, which titles the group. */
  group: string;
}

/**
 * The factors and measured indicators that the map can show alone, in the order of the factor tree,
 * from the manifest alone. A choice indicator (a faith, a group) is left out, since it has no score
 * until the user picks an option, and so is a factor that holds nothing else.
 */
export function viewOptions(manifest: Manifest): ViewOption[] {
  const scored = new Set(
    manifest.indicators
      .filter((i) => i.preference_type !== "user-choice")
      .map((i) => i.id),
  );
  const visit = (
    factor: ManifestFactor,
    depth: number,
    top: ManifestFactor,
  ): ViewOption[] => {
    const inside = (factor.children ?? []).flatMap((kid) =>
      visit(kid, depth + 1, top),
    );
    const worth = factor.children
      ? inside.length > 0
      : scored.has(factor.indicator ?? "");
    return worth
      ? [
          {
            id: factor.id,
            name: factor.name,
            depth,
            groupId: top.id,
            group: top.name,
          },
          ...inside,
        ]
      : [];
  };
  return manifest.factors.flatMap((factor) => visit(factor, 0, factor));
}

/**
 * What the legend says where the map has no data for what it shows: that the user counts nothing
 * inside the factor, which they can mend, or else that the data is not there.
 */
export function noDataNote(
  name: string,
  node: ManifestFactor | undefined,
  profile: Profile,
): string {
  const kids = node?.children ?? [];
  const nothingCounted =
    kids.length > 0 && kids.every((kid) => effectiveWeight(kid, profile) === 0);
  return nothingCounted
    ? `Nothing inside ${name} counts: give a weight inside it above 0.`
    : `There is no data for ${name}.`;
}

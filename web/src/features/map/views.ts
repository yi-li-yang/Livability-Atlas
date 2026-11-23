import type {
  Manifest,
  ManifestFactor,
  ManifestIndicator,
} from "../../generated/manifest.schema";
import { effectiveWeight, type Profile } from "../../scoring/region";
import { formatValue } from "../factors/evidence";

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

/**
 * The measured indicator that the map shows alone, or null where it shows a factor that holds
 * others, or the livability score.
 */
export function viewedIndicator(
  manifest: Manifest,
  view: string | null,
): ManifestIndicator | null {
  if (view === null) return null;
  const find = (nodes: readonly ManifestFactor[]): ManifestFactor | null => {
    for (const node of nodes) {
      if (node.id === view) return node;
      const inside = find(node.children ?? []);
      if (inside) return inside;
    }
    return null;
  };
  const leaf = find(manifest.factors);
  if (!leaf?.indicator) return null;
  const indicator = manifest.indicators.find((i) => i.id === leaf.indicator);
  // A choice has no column of its own, and no one value: each option has its own.
  return indicator && !indicator.options ? indicator : null;
}

/** The longest value with its unit that fits at an end of the legend beside the other end. */
const LONGEST_END = 20;

/**
 * The values at the two ends of the legend's scale where the map shows one measured indicator that
 * a ramp scores: the value that scores 0 on the left and the one that scores 1 on the right, the
 * user's way round (`flipped`). A long unit is given once, as `unit`, to go under the bar, and the
 * ends keep only a pound sign or a per cent sign. Null for anything else, whose ends stay "Worse"
 * and "Better".
 */
export function legendEnds(
  indicator: ManifestIndicator | null,
  flipped: boolean,
): { low: string; high: string; unit: string | null } | null {
  const curve = indicator?.curve;
  if (!indicator || curve?.shape !== "ramp") return null;
  const [zero, full] = flipped ? [curve.t1, curve.t0] : [curve.t0, curve.t1];
  const { unit } = indicator;
  const low = formatValue(zero, unit);
  const high = formatValue(full, unit);
  if (Math.max(low.length, high.length) <= LONGEST_END) {
    return { low, high, unit: null };
  }
  const sign = unit.startsWith("£") ? "£" : unit.startsWith("%") ? "%" : "";
  return {
    low: formatValue(zero, sign),
    high: formatValue(full, sign),
    unit,
  };
}

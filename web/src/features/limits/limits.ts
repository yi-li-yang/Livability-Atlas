import type { Bundle, Value } from "../../data/bundle";
import type { ManifestIndicator } from "../../generated/manifest.schema";
import type { Limit, Profile } from "../../scoring/region";
import { formatValue } from "../factors/evidence";

/** A limit in words: "Renting cost: at most £2,000 a month". */
export function describeLimit(
  limit: Limit,
  indicator: ManifestIndicator | undefined,
): string {
  const name = indicator?.name ?? limit.indicator;
  const unit = indicator?.unit ?? "";
  if ("max" in limit) return `${name}: at most ${formatValue(limit.max, unit)}`;
  if ("min" in limit)
    return `${name}: at least ${formatValue(limit.min, unit)}`;
  const list = [...limit.in];
  const last = list.pop();
  const values = list.length > 0 ? `${list.join(", ")} or ${last}` : `${last}`;
  return `${name}: only ${unit ? `${unit} ` : ""}${values}`;
}

/** An indicator that a limit can be set on, and what kind of value it holds. */
export interface Limitable {
  indicator: ManifestIndicator;
  /** `number` for values that can be compared (at most, at least), else `category`. */
  kind: "number" | "category";
  /** For a category, its values in the data, sorted. */
  values: string[];
}

const isNumber = (value: Value): boolean =>
  value !== null && value !== "" && Number.isFinite(Number(value));

/**
 * The measured indicators that a limit can be set on: those with a column of their own (a choice
 * indicator has a column for each option, and no limit of its own), by name.
 */
export function limitableIndicators(bundle: Bundle): Limitable[] {
  const found: Limitable[] = [];
  for (const indicator of bundle.manifest.indicators) {
    if (indicator.options) continue;
    const present = (bundle.columns[indicator.column] ?? []).filter(
      (v) => v !== null,
    );
    if (present.length === 0) continue;
    const numeric = present.every(isNumber);
    const values = numeric
      ? []
      : [...new Set(present.map(String))].sort((a, b) =>
          a.localeCompare(b, "en-GB", { numeric: true }),
        );
    found.push({ indicator, kind: numeric ? "number" : "category", values });
  }
  return found.sort((a, b) =>
    a.indicator.name.localeCompare(b.indicator.name, "en-GB"),
  );
}

/** The lowest, middle and highest of the numbers in a column, or null where there are none. */
export function rangeOf(
  values: readonly Value[],
): { min: number; median: number; max: number } | null {
  const sorted = values
    .filter(isNumber)
    .map(Number)
    .sort((a, b) => a - b);
  if (sorted.length === 0) return null;
  const middle = sorted.length >> 1;
  const median =
    sorted.length % 2 === 0
      ? (sorted[middle - 1] + sorted[middle]) / 2
      : sorted[middle];
  return { min: sorted[0], median, max: sorted[sorted.length - 1] };
}

/** The profile with a limit set: it replaces the one on the same indicator. */
export function withLimit(profile: Profile, limit: Limit): Profile {
  const others = (profile.limits ?? []).filter(
    (l) => l.indicator !== limit.indicator,
  );
  return { ...profile, limits: [...others, limit] };
}

/** The profile without the limit on an indicator. */
export function withoutLimit(profile: Profile, indicator: string): Profile {
  const rest = (profile.limits ?? []).filter((l) => l.indicator !== indicator);
  const { limits: _, ...others } = profile;
  return rest.length > 0 ? { ...others, limits: rest } : others;
}

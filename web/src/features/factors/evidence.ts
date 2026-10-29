import type {
  EvidenceType,
  ManifestIndicator,
} from "../../generated/manifest.schema";

type Curve = ManifestIndicator["curve"];

/** A number with few enough figures to read: whole above 100, one decimal above 10, else two. */
function formatNumber(value: number): string {
  const size = Math.abs(value);
  const digits = size >= 100 ? 0 : size >= 10 ? 1 : 2;
  return new Intl.NumberFormat("en-GB", {
    maximumFractionDigits: digits,
  }).format(value);
}

/**
 * A raw value with its unit, as a person says it: "7.5 minutes on foot", "12.3% of residents",
 * "£6,102 per m²", "PTAL band 6b".
 */
export function formatValue(
  value: number | bigint | string | null | undefined,
  unit: string,
): string {
  if (value === null || value === undefined) return "No data here";
  if (typeof value === "string") return unit ? `${unit} ${value}` : value;
  const number = formatNumber(Number(value));
  if (unit.startsWith("%")) return `${number}%${unit.slice(1)}`;
  if (unit.startsWith("£")) return `£${number}${unit.slice(1)}`;
  return unit ? `${number} ${unit}` : number;
}

/** How a measured indicator's value becomes a score from 0 to 1, in words. */
export function describeCurve(curve: Curve | undefined, unit: string): string {
  if (!curve) return "It has no scoring curve yet.";
  switch (curve.shape) {
    case "ramp": {
      const better = formatValue(curve.t1, unit);
      const worse = formatNumber(curve.t0);
      return curve.t1 < curve.t0
        ? `Full marks at ${better} or less, none at ${worse} or more.`
        : `Full marks at ${better} or more, none at ${worse} or less.`;
    }
    case "ideal-range":
      return `Full marks from ${formatNumber(curve.l1)} to ${formatValue(curve.u0, unit)}, falling to none at ${formatNumber(curve.l0)} and at ${formatNumber(curve.u1)}.`;
    case "lookup": {
      const each = Object.entries(curve.scores).map(
        ([value, score]) => `${value} gives ${Math.round(score * 100)}%`,
      );
      return `Each value has its own score: ${each.join(", ")}.`;
    }
    case "percentile":
      return `Ranked against the region's other hex cells: the ${curve.better}, the better.`;
  }
}

const EVIDENCE_TEXT: Record<EvidenceType, string> = {
  direct: "Measured directly",
  estimate: "An estimate, worked out approximately",
  indirect: "Indirect: a sign of the thing, not the thing",
  perception: "How people see the place",
  ranking: "From a published ranking",
};

/** What kind of evidence a measured indicator is, in plain words (the glossary's evidence types). */
export function evidenceTypeText(type: EvidenceType): string {
  return EVIDENCE_TEXT[type];
}

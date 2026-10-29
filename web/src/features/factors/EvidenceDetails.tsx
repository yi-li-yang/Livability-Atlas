import type { Evidence } from "../../scoring/explain";
import { describeCurve, evidenceTypeText, formatValue } from "./evidence";

/**
 * The evidence behind one measured indicator in one hex cell (interface layer 5): the raw value
 * and its unit, how the value becomes a score, what kind of evidence it is, and the datasets with
 * their dates and licences. It opens from a "Details" link and shows nothing until asked.
 */
export function EvidenceDetails({ evidence }: { evidence: Evidence }) {
  const { indicator, value, option, datasets } = evidence;
  const here = indicator.options
    ? option === null
      ? "Nothing picked has a value here"
      : `${formatValue(value, indicator.unit)}, for ${option}`
    : formatValue(value, indicator.unit);
  return (
    <details className="mt-1 text-xs" data-testid={`evidence-${indicator.id}`}>
      <summary className="cursor-pointer underline">
        Details<span className="sr-only"> of {indicator.name}</span>
      </summary>
      <dl className="mt-1 space-y-1 border-l border-neutral-300 pl-2">
        <div>
          <dt className="font-medium">Value here</dt>
          <dd>{here}</dd>
        </div>
        <div>
          <dt className="font-medium">How it scores</dt>
          <dd>{describeCurve(indicator.curve, indicator.unit)}</dd>
        </div>
        <div>
          <dt className="font-medium">Kind of evidence</dt>
          <dd>{evidenceTypeText(indicator.evidence_type)}</dd>
        </div>
        <div>
          <dt className="font-medium">
            {datasets.length === 1 ? "Source" : "Sources"}
          </dt>
          {datasets.map((dataset) => (
            <dd key={dataset.id}>
              <a
                href={dataset.url}
                className="underline"
                target="_blank"
                rel="noreferrer noopener"
              >
                {dataset.name}
              </a>
              , {dataset.publisher}, {dataset.date}. Licence {dataset.licence}.
            </dd>
          ))}
        </div>
      </dl>
    </details>
  );
}

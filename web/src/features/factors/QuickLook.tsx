import type { Explanation } from "../../scoring/explain";
import { OnTheMap } from "../map/OnTheMap";

const wholeNumber = new Intl.NumberFormat("en-GB");

/** What a hex cell scores, and what drives it, at a glance. */
export function QuickLook({
  explanation,
  rank,
  total,
  onMap,
}: {
  explanation: Explanation;
  rank: number | null;
  total: number;
  /** What the map shows in place of the livability score, and the cell's score on it. */
  onMap?: { name: string; score: number | null } | null;
}) {
  const { score, strengths, weakness, neighbourhood } = explanation;
  return (
    <div role="status" aria-label="Quick look" className="text-sm">
      {neighbourhood && (
        <p className="font-medium">
          {neighbourhood.name}
          {neighbourhood.area && (
            <span className="font-normal text-neutral-600">
              , {neighbourhood.area}
            </span>
          )}
        </p>
      )}
      {onMap && <OnTheMap {...onMap} />}
      {score === null ? (
        <p className="font-medium">No score here: there is no data for it.</p>
      ) : (
        <>
          {onMap && (
            <p className="mt-1 text-xs text-neutral-600">Livability score</p>
          )}
          <p>
            <span className="text-2xl font-semibold tabular-nums">
              {Math.round(score)}
            </span>{" "}
            <span className="text-neutral-600">out of 100</span>
          </p>
          {explanation.excluded && (
            <p className="font-medium">Left out by your hard limits</p>
          )}
          {rank !== null && (
            <p className="text-neutral-600">
              Rank {wholeNumber.format(rank)} of {wholeNumber.format(total)}
            </p>
          )}
          <ul className="mt-1">
            {strengths.map((f) => (
              <li key={f.id}>+ {f.name}</li>
            ))}
            {weakness && <li>− {weakness.name}</li>}
          </ul>
          <p className="mt-1 text-xs text-neutral-600">
            Click for the reasons.
          </p>
        </>
      )}
    </div>
  );
}

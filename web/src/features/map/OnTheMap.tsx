import { scoreToCss } from "./colour";

/** What the map shows in place of the livability score, and what the hex cell scores on it. */
export function OnTheMap({
  name,
  score,
  value = null,
}: {
  name: string;
  /** From 0 to 100, or null where the cell has no data for it. */
  score: number | null;
  /** For a measured indicator, its value here with its unit, such as "£2,834 a month". */
  value?: string | null;
}) {
  return (
    <p data-testid="on-the-map" className="text-sm">
      <span className="text-neutral-600">On the map: </span>
      <span className="font-medium">{name}</span>
      {score === null ? (
        ", no data here"
      ) : (
        <>
          {value && <span data-testid="value-here">{`, ${value}`}</span>}
          {", "}
          {/* The colour the score has on the map, so that a name such as Crime reads as good or bad. */}
          <span
            data-testid="score-chip"
            data-score={score / 100}
            aria-hidden="true"
            className="mr-1 inline-block size-3 rounded-sm align-[-1px] ring-1 ring-inset ring-black/20"
            style={{ background: scoreToCss(score / 100) }}
          />
          {`${Math.round(score)} out of 100`}
        </>
      )}
    </p>
  );
}

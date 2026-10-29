import { useEffect } from "react";
import type { Explanation, FactorLine } from "../../scoring/explain";
import { factorColour } from "./colours";
import { EvidenceDetails } from "./EvidenceDetails";

const wholeNumber = new Intl.NumberFormat("en-GB");
const points = (value: number): string => String(Math.round(value));

/**
 * One bar for a factor. The track is the most the factor could add, from its share of the weight,
 * and the filled part is what it adds in this hex cell, so a short fill in a long track is a
 * factor that matters to the user and scores badly here.
 */
function Bar({
  line,
  widest,
  colour,
}: {
  line: FactorLine;
  widest: number;
  colour: string;
}) {
  if (line.share === null || line.score === null) {
    return <p className="text-xs text-neutral-600">No data here</p>;
  }
  return (
    <div
      className="h-2 rounded-sm bg-neutral-200"
      style={{ width: `${(line.share / widest) * 100}%` }}
      aria-hidden="true"
    >
      <div
        className="h-full rounded-sm"
        style={{ width: `${line.score * 100}%`, background: colour }}
      />
    </div>
  );
}

function Line({
  line,
  widest,
  colour,
}: {
  line: FactorLine;
  widest: number;
  colour: string;
}) {
  const opens = line.children.length > 0;
  const summary = (
    <div className="space-y-1">
      <div className="flex justify-between gap-2">
        <span className="flex gap-1">
          <span
            aria-hidden="true"
            className="inline-block w-3 text-neutral-500 transition-transform group-open:rotate-90"
          >
            {opens ? "›" : ""}
          </span>
          {line.name}
        </span>
        <span className="tabular-nums text-neutral-600">
          {line.contribution !== null &&
            line.share !== null &&
            `${points(line.contribution)} of ${points(line.share * 100)} points`}
        </span>
      </div>
      <Bar line={line} widest={widest} colour={colour} />
    </div>
  );
  if (line.children.length === 0) {
    return (
      <li>
        {summary}
        {line.evidence && <EvidenceDetails evidence={line.evidence} />}
      </li>
    );
  }
  const widestInside = Math.max(
    ...line.children.map((c) => c.share ?? 0),
    Number.MIN_VALUE,
  );
  return (
    <li>
      <details className="group">
        <summary className="cursor-pointer list-none [&::-webkit-details-marker]:hidden">
          {summary}
        </summary>
        <ul className="mt-2 space-y-2 border-l border-neutral-300 pl-3">
          {line.children.map((child) => (
            <Line
              key={child.id}
              line={child}
              widest={widestInside}
              colour={colour}
            />
          ))}
        </ul>
      </details>
    </li>
  );
}

/** Why a hex cell has its score: what each factor adds, with each factor opening into its parts. */
export function WhyPanel({
  explanation,
  rank,
  total,
  onClose,
}: {
  explanation: Explanation;
  rank: number | null;
  total: number;
  onClose: () => void;
}) {
  useEffect(() => {
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, [onClose]);

  const widest = Math.max(
    ...explanation.factors.map((f) => f.share ?? 0),
    Number.MIN_VALUE,
  );
  return (
    <aside
      aria-label="Why this score"
      className="absolute right-4 top-4 z-10 max-h-[calc(100%-9rem)] w-80 max-w-[calc(100%-2rem)] overflow-y-auto rounded bg-white/95 p-3 text-sm shadow"
    >
      <div className="flex items-start justify-between gap-2">
        <h2 className="font-medium">Why this score</h2>
        <button type="button" className="underline" onClick={onClose}>
          Close
        </button>
      </div>
      {explanation.score === null ? (
        <p className="mt-2">There is no data here for the factors you count.</p>
      ) : (
        <p className="mt-1">
          <span className="text-2xl font-semibold tabular-nums">
            {Math.round(explanation.score)}
          </span>{" "}
          out of 100
          {rank !== null && (
            <span className="text-neutral-600">
              , rank {wholeNumber.format(rank)} of {wholeNumber.format(total)}
            </span>
          )}
        </p>
      )}
      {explanation.lowCoverage && explanation.score !== null && (
        <p role="note" className="mt-2 rounded bg-amber-100 p-2 text-xs">
          This score rests on thin data: less than 70% of the weight you gave
          has data here.
        </p>
      )}
      <ul className="mt-3 space-y-3">
        {explanation.factors.map((factor, position) => (
          <Line
            key={factor.id}
            line={factor}
            widest={widest}
            colour={factorColour(factor.id, position).base}
          />
        ))}
      </ul>
    </aside>
  );
}

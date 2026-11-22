import { useEffect, useState } from "react";
import type { Sensitivity } from "../../scoring/sensitivity";
import type { TopNeighbourhood } from "./top";

/** How long the weights must stay still before the stability is worked out. */
const WAIT_MS = 300;

/**
 * The best neighbourhoods by name and score (interface layer 1), a short list that opens from a
 * link. Choosing one takes the map to its best hex cell. Once open, it says how many of them stay
 * when a weight moves by a fifth (the stability of the top), and marks those that always stay.
 */
export function TopNeighbourhoods({
  top,
  stability,
  onChoose,
}: {
  top: TopNeighbourhood[];
  /**
   * The steps that work out the stability of the list. It is costly, so it runs only while the
   * list is open, one step at a time, with the page free to respond in between.
   */
  stability?: () => Generator<void, Sensitivity> | null;
  onChoose: (neighbourhood: TopNeighbourhood) => void;
}) {
  const [open, setOpen] = useState(false);
  // With nothing to list the list is not drawn, and it comes back shut: so is the state.
  const empty = top.length === 0;
  useEffect(() => {
    if (empty) setOpen(false);
  }, [empty]);
  const [result, setResult] = useState<Sensitivity | null>(null);
  // It rescores the region dozens of times, so it waits until the weights stop moving.
  useEffect(() => {
    setResult(null);
    if (!open || !stability) return;
    let timer: ReturnType<typeof setTimeout>;
    let steps: Generator<void, Sensitivity> | null = null;
    const next = () => {
      steps ??= stability();
      if (!steps) return;
      const step = steps.next();
      if (step.done) setResult(step.value);
      else timer = setTimeout(next, 0);
    };
    timer = setTimeout(next, WAIT_MS);
    return () => clearTimeout(timer);
  }, [open, stability]);
  if (top.length === 0) return null;
  const stay = result
    ? Math.round(result.stability * result.baseline.length)
    : null;
  return (
    <details
      className="mb-3 text-sm"
      data-testid="top-neighbourhoods"
      open={open}
      onToggle={(event) => setOpen(event.currentTarget.open)}
    >
      <summary className="cursor-pointer underline">Top neighbourhoods</summary>
      <ol className="mt-1 space-y-1">
        {top.map((n) => {
          const steady = result?.staysIn[String(n.position)] === 1;
          return (
            <li key={n.position} className="flex justify-between gap-2">
              <button
                type="button"
                className="text-left underline"
                onClick={() => onChoose(n)}
              >
                {n.name}
                {n.area && <span className="text-neutral-600">, {n.area}</span>}
              </button>
              <span className="flex shrink-0 gap-1">
                {steady && (
                  <span title="Stays in the list whichever weight moves">
                    <span aria-hidden="true">●</span>
                    <span className="sr-only">Steady,</span>
                  </span>
                )}
                <span className="tabular-nums">{Math.round(n.score)}</span>
              </span>
            </li>
          );
        })}
      </ol>
      {result && stay !== null && (
        <p className="mt-2 text-xs text-neutral-600" data-testid="stability">
          {stay} of these {result.baseline.length} stay, on average, when a
          weight moves by a fifth. ● marks those that stay whichever weight
          moves.
        </p>
      )}
    </details>
  );
}

import type { TopNeighbourhood } from "./top";

/**
 * The best neighbourhoods by name and score (interface layer 1), a short list that opens from a
 * link. Choosing one takes the map to its best hex cell.
 */
export function TopNeighbourhoods({
  top,
  onChoose,
}: {
  top: TopNeighbourhood[];
  onChoose: (neighbourhood: TopNeighbourhood) => void;
}) {
  if (top.length === 0) return null;
  return (
    <details className="mb-3 text-sm" data-testid="top-neighbourhoods">
      <summary className="cursor-pointer underline">Top neighbourhoods</summary>
      <ol className="mt-1 space-y-1">
        {top.map((n) => (
          <li
            key={`${n.name}-${n.area}`}
            className="flex justify-between gap-2"
          >
            <button
              type="button"
              className="text-left underline"
              onClick={() => onChoose(n)}
            >
              {n.name}
              {n.area && <span className="text-neutral-600">, {n.area}</span>}
            </button>
            <span className="tabular-nums">{Math.round(n.score)}</span>
          </li>
        ))}
      </ol>
    </details>
  );
}

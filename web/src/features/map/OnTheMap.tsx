/** What the map shows in place of the livability score, and what the hex cell scores on it. */
export function OnTheMap({
  name,
  score,
}: {
  name: string;
  /** From 0 to 100, or null where the cell has no data for it. */
  score: number | null;
}) {
  return (
    <p data-testid="on-the-map" className="text-sm">
      <span className="text-neutral-600">On the map: </span>
      <span className="font-medium">{name}</span>
      {score === null ? ", no data here" : `, ${Math.round(score)} out of 100`}
    </p>
  );
}

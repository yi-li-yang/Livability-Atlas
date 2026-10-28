import { scoreToColour } from "./colour";

const css = (score: number): string => {
  const [r, g, b] = scoreToColour(score);
  return `rgb(${r} ${g} ${b})`;
};

/** What the colours mean: a bar from the worst score to the best, with a label at each end. */
export function Legend({
  title,
  low,
  high,
}: {
  title: string;
  low: string;
  high: string;
}) {
  const gradient = `linear-gradient(to right, ${[0, 0.25, 0.5, 0.75, 1].map(css).join(", ")})`;
  return (
    <section
      aria-label="Legend"
      className="absolute bottom-6 left-4 w-56 rounded bg-white/90 p-3 text-sm shadow"
    >
      <h2 className="mb-1 font-medium">{title}</h2>
      <div
        data-testid="legend-bar"
        className="h-3 rounded"
        style={{ background: gradient }}
      />
      <div className="mt-1 flex justify-between text-xs text-neutral-600">
        <span>{low}</span>
        <span>{high}</span>
      </div>
    </section>
  );
}

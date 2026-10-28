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
  opacity,
  onOpacity,
}: {
  title: string;
  low: string;
  high: string;
  /** How strongly the cells show over the map, from 0 to 1. */
  opacity: number;
  onOpacity: (opacity: number) => void;
}) {
  const gradient = `linear-gradient(to right, ${[0, 0.25, 0.5, 0.75, 1].map(css).join(", ")})`;
  return (
    <section
      aria-label="Legend"
      className="absolute bottom-6 left-4 z-10 w-56 rounded bg-white/90 p-3 text-sm shadow"
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
      <label className="mt-2 block text-xs text-neutral-600">
        Cell opacity
        <input
          type="range"
          min={0}
          max={100}
          step={5}
          value={Math.round(opacity * 100)}
          aria-label="Cell opacity"
          aria-valuetext={`${Math.round(opacity * 100)}%`}
          className="block w-full"
          onChange={(event) => onOpacity(Number(event.target.value) / 100)}
        />
        <span className="flex justify-between">
          <span>Map</span>
          <span>Cells</span>
        </span>
      </label>
    </section>
  );
}

import { FEW_HOMES_OUTLINE, LAND_COLOURS, scoreToCss } from "./colour";
import type { ViewOption } from "./views";

/** What the colours mean: a bar from the worst score to the best, with a label at each end. */
export function Legend({
  title,
  low,
  high,
  options,
  view,
  note,
  fewHomes = false,
  phone = false,
  onView,
  opacity,
  onOpacity,
}: {
  title: string;
  low: string;
  high: string;
  /** What the map can show in place of the livability score, grouped by top-level factor. */
  options: readonly ViewOption[];
  /** The id of the factor or indicator the map shows, or null for the livability score. */
  view: string | null;
  /** Something to say about what is shown, such as that it has no data. */
  note?: string | null;
  /** Whether the map leaves the cells with few or no homes clear, which the legend then explains. */
  fewHomes?: boolean;
  /** Whether to lay it out for a phone: across the top of the map, with the opacity tucked away. */
  phone?: boolean;
  onView: (view: string | null) => void;
  /** How strongly the cells show over the map, from 0 to 1. */
  opacity: number;
  onOpacity: (opacity: number) => void;
}) {
  const gradient = `linear-gradient(to right, ${[0, 0.25, 0.5, 0.75, 1].map(scoreToCss).join(", ")})`;
  const groups = new Map<string, { name: string; items: ViewOption[] }>();
  for (const option of options) {
    const group = groups.get(option.groupId) ?? {
      name: option.group,
      items: [],
    };
    groups.set(option.groupId, { ...group, items: [...group.items, option] });
  }
  // A hex cell with few or no homes is left clear with an outline, and the land use shows in it:
  // the key shows one, half park and half industry.
  const fewHomesKey = fewHomes && (
    <span className="flex items-center gap-1.5">
      <span
        aria-hidden="true"
        data-testid="few-homes-key"
        className="inline-block h-3 w-4 shrink-0 rounded-sm border"
        style={{
          borderColor: `rgb(${FEW_HOMES_OUTLINE.slice(0, 3).join(" ")})`,
          background: `linear-gradient(to right, ${LAND_COLOURS.green} 50%, ${LAND_COLOURS.industry} 50%)`,
        }}
      />
      Few or no homes: no score
    </span>
  );
  const opacityControl = (
    <>
      <input
        id="cell-opacity"
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
    </>
  );
  return (
    <section
      aria-label="Legend"
      className={
        phone
          ? "absolute left-2 right-2 top-2 z-10 rounded bg-white/90 p-2 text-sm shadow"
          : "absolute bottom-6 left-4 z-10 w-56 rounded bg-white/90 p-3 text-sm shadow"
      }
    >
      <label className="mb-2 block text-xs text-neutral-600">
        <span className={phone ? "sr-only" : undefined}>Show on the map</span>
        <select
          aria-label="Show on the map"
          value={view ?? ""}
          className="mt-0.5 block w-full rounded border border-neutral-400 bg-white p-1 text-sm text-neutral-900"
          onChange={(event) => onView(event.target.value || null)}
        >
          <option value="">Livability score</option>
          {[...groups].map(([id, { name, items }]) => (
            <optgroup key={id} label={name}>
              {items.map((option) => (
                <option key={option.id} value={option.id}>
                  {/* Two non-breaking spaces for each level, which an option keeps and a space loses. */}
                  {"  ".repeat(option.depth)}
                  {option.name}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
      </label>
      <h2 className={phone ? "sr-only" : "mb-1 font-medium"}>{title}</h2>
      <div
        data-testid="legend-bar"
        className="h-3 rounded"
        style={{ background: gradient }}
      />
      <div className="mt-1 flex justify-between gap-2 text-xs text-neutral-600">
        <span>{low}</span>
        {phone && fewHomesKey}
        <span>{high}</span>
      </div>
      {fewHomesKey && !phone && (
        <p className="mt-1 text-xs text-neutral-600">{fewHomesKey}</p>
      )}
      {note && (
        <p role="note" className="mt-1 text-xs text-neutral-600">
          {note}
        </p>
      )}
      {phone ? (
        <details className="mt-1 text-xs text-neutral-600">
          <summary className="cursor-pointer">Cell opacity</summary>
          {opacityControl}
        </details>
      ) : (
        <label
          htmlFor="cell-opacity"
          className="mt-2 block text-xs text-neutral-600"
        >
          Cell opacity
          {opacityControl}
        </label>
      )}
    </section>
  );
}

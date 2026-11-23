import {
  EXCLUDED,
  FEW_HOMES_OUTLINE,
  LAND_COLOURS,
  PALETTE,
  type Rgba,
  scoreToCss,
} from "./colour";
import type { ColourBy } from "./rank";
import type { ViewOption } from "./views";

const css = ([r, g, b, a]: Rgba) => `rgb(${r} ${g} ${b} / ${a / 255})`;

/** A small hexagon for a key in the legend, filled and outlined as the map draws the cells it names. */
function HexKey({
  fill,
  stroke,
  testId,
}: {
  fill: string;
  stroke?: string;
  testId: string;
}) {
  return (
    <svg
      aria-hidden="true"
      data-testid={testId}
      viewBox="0 0 20 22"
      className="h-4 w-4 shrink-0"
    >
      <polygon
        points="10,1 19,6 19,16 10,21 1,16 1,6"
        fill={fill}
        stroke={stroke ?? "none"}
        strokeWidth={1.5}
      />
    </svg>
  );
}

/**
 * The scores between which most of the region lies (the middle 80%), read off the spread's bands,
 * as whole numbers: the bands' edges, so they never claim more precision than the bands have.
 */
export function middleOf(spread: readonly number[]): [number, number] | null {
  const total = spread.reduce((a, b) => a + b, 0);
  if (total === 0) return null;
  const width = 100 / spread.length;
  let seen = 0;
  let low = 0;
  let high = 100;
  let lowFound = false;
  for (let band = 0; band < spread.length; band++) {
    seen += spread[band];
    if (!lowFound && seen > total * 0.1) {
      low = band * width;
      lowFound = true;
    }
    if (seen >= total * 0.9) {
      high = (band + 1) * width;
      break;
    }
  }
  return [Math.round(low), Math.round(high)];
}

/** What the colours mean: a bar from the worst score to the best, with a label at each end. */
export function Legend({
  title,
  low,
  high,
  unit = null,
  options,
  view,
  note,
  fewHomes = false,
  phone = false,
  onView,
  opacity,
  onOpacity,
  colourBy = "score",
  onColourBy,
  region = "the region",
  spread = null,
  topMarked = false,
  leftOut = null,
}: {
  title: string;
  low: string;
  high: string;
  /** The unit of the values at the ends, where it is too long to give at each end. */
  unit?: string | null;
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
  /** Whether the map colours its cells by their score or by their rank in the region (D24). */
  colourBy?: ColourBy;
  onColourBy?: (colourBy: ColourBy) => void;
  /** The region's name, as in "Rank in London". */
  region?: string;
  /** How many cells that count fall in each band of the scale, to show where the scores lie. */
  spread?: readonly number[] | null;
  /** Whether the map marks the top neighbourhoods with their places in the list. */
  topMarked?: boolean;
  /** With hard limits: how many hex cells with homes and a score they leave out, of how many. */
  leftOut?: { count: number; of: number } | null;
}) {
  const byRank = colourBy === "rank";
  const fifths = `linear-gradient(to right, ${PALETTE.map(
    ([r, g, b], i) => `rgb(${r} ${g} ${b}) ${i * 20}% ${(i + 1) * 20}%`,
  ).join(", ")})`;
  const tallest = spread ? Math.max(...spread, 1) : 1;
  const middle = spread && !byRank ? middleOf(spread) : null;
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
      <HexKey
        testId="few-homes-key"
        fill={LAND_COLOURS.green}
        stroke={css(FEW_HOMES_OUTLINE)}
      />
      Few or no homes: no score
    </span>
  );
  const wholeNumber = new Intl.NumberFormat("en-GB");
  const leftOutKey = leftOut && leftOut.count > 0 && (
    <p className="mt-1 flex items-center gap-1.5 text-xs text-neutral-600">
      <HexKey testId="left-out-key" fill={css(EXCLUDED)} />
      Left out by your hard limits: {wholeNumber.format(leftOut.count)} of{" "}
      {wholeNumber.format(leftOut.of)}
    </p>
  );
  const topMark = topMarked && (
    <p className="mt-1 flex items-center gap-1.5 text-xs text-neutral-600">
      <span
        aria-hidden="true"
        className="inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full border-2 border-neutral-800 bg-white text-[9px] font-semibold text-neutral-900"
      >
        1
      </span>
      Top neighbourhoods, numbered by rank
    </p>
  );
  // What the colours say about the region, and the marks: under the bar on a desktop, and behind
  // "Colours" on a phone, where the legend must stay small.
  const about = (
    <>
      {middle && (
        <p className="mt-1 text-xs text-neutral-600">
          Most of {region} scores {middle[0]} to {middle[1]}.
        </p>
      )}
      {byRank && (
        <p className="mt-1 text-xs text-neutral-600">
          Each colour is a fifth of {region}'s hex cells, from its lowest scores
          to its highest.
        </p>
      )}
      {topMark}
    </>
  );
  const colourSwitch = onColourBy && (
    <fieldset
      className={`m-0 flex w-fit overflow-hidden rounded border border-neutral-400 p-0 text-xs ${phone ? "mt-2" : ""}`}
    >
      <legend className="sr-only">Colour the map by</legend>
      {(
        [
          ["score", "Score"],
          ["rank", `Rank in ${region}`],
        ] as const
      ).map(([option, name]) => (
        <button
          key={option}
          type="button"
          aria-pressed={colourBy === option}
          className={
            colourBy === option
              ? "bg-neutral-800 px-2 py-0.5 text-white"
              : "bg-white px-2 py-0.5 hover:bg-neutral-100"
          }
          onClick={() => onColourBy(option)}
        >
          {name}
        </button>
      ))}
    </fieldset>
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
        aria-label="Colour strength"
        aria-valuetext={`${Math.round(opacity * 100)}%`}
        className="block w-full accent-neutral-700"
        onChange={(event) => onOpacity(Number(event.target.value) / 100)}
      />
      <span className="flex justify-between">
        <span>Map</span>
        <span>Colours</span>
      </span>
    </>
  );
  return (
    <section
      aria-label="Legend"
      data-covers-map
      className={
        phone
          ? "absolute left-2 right-2 top-2 z-10 rounded bg-white/90 p-2 text-sm shadow"
          : "absolute bottom-6 left-4 z-10 w-72 rounded bg-white/90 p-3 text-sm shadow"
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
      {phone ? (
        <h2 className="sr-only">{title}</h2>
      ) : (
        <div className="mb-1 flex flex-wrap items-center justify-between gap-x-2">
          <h2 className="font-medium">{title}</h2>
          {colourSwitch}
        </div>
      )}
      {spread && !byRank && !phone && (
        // Where the region's scores lie on the scale: a bar for each band, as tall as its count.
        <svg
          aria-hidden="true"
          data-testid="score-spread"
          viewBox={`0 0 ${spread.length} 10`}
          preserveAspectRatio="none"
          className="block h-4 w-full"
        >
          {spread.map((count, band) => (
            <rect
              // biome-ignore lint/suspicious/noArrayIndexKey: the bands are fixed and in order
              key={band}
              x={band + 0.1}
              width={0.8}
              y={10 - (10 * count) / tallest}
              height={(10 * count) / tallest}
              fill="rgb(115 115 115)"
            />
          ))}
        </svg>
      )}
      <div
        data-testid="legend-bar"
        className="h-3 rounded"
        style={{ background: byRank ? fifths : gradient }}
      />
      {!byRank && !phone && (
        <div
          aria-hidden="true"
          className="flex justify-between text-[10px] text-neutral-500 tabular-nums"
        >
          <span>0</span>
          <span>50</span>
          <span>100</span>
        </div>
      )}
      <div className="mt-0.5 flex justify-between gap-2 text-xs text-neutral-600">
        <span>{byRank ? "Bottom fifth" : low}</span>
        {phone && fewHomesKey}
        <span>{byRank ? "Top fifth" : high}</span>
      </div>
      {unit && !byRank && (
        <p data-testid="legend-unit" className="text-xs text-neutral-600">
          In {unit}
        </p>
      )}
      {!phone && about}
      {fewHomesKey && !phone && (
        <p className="mt-1 text-xs text-neutral-600">{fewHomesKey}</p>
      )}
      {leftOutKey}
      {note && (
        <p role="note" className="mt-1 text-xs text-neutral-600">
          {note}
        </p>
      )}
      {phone ? (
        <details className="mt-1 text-xs text-neutral-600">
          <summary className="cursor-pointer">Colours</summary>
          {about}
          {colourSwitch}
          <label htmlFor="cell-opacity" className="mt-2 block">
            Colour strength
            {opacityControl}
          </label>
        </details>
      ) : (
        <label
          htmlFor="cell-opacity"
          className="mt-2 block text-xs text-neutral-600"
        >
          Colour strength
          {opacityControl}
        </label>
      )}
    </section>
  );
}

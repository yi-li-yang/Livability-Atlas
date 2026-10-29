import { useState } from "react";
import { arcPath, slices, wrapName } from "./arcs";
import type { FactorView } from "./level";

// The rings are drawn in a box of 100 by 100 units, centred on 0, 0: the centre, the factors at
// this level, and outside them the sub-factors of each.
const CENTRE = 16;
const MIDDLE = 33;
const OUTSIDE = 49;
const GAP = 0.6;
/** The least angle, in radians, of an arc that has room to write its share in. */
const ROOM_FOR_A_SHARE = 0.45;

const percent = (share: number): string => `${Math.round(share * 100)}%`;

/**
 * One arc of the rings. The drawing is hidden from assistive technology, and the rows beside it
 * are the keyboard route to the same actions, so an arc answers the pointer only.
 */
function Arc({
  d,
  fill,
  fillOpacity,
  label,
  data,
  onClick,
  onPoint,
}: {
  d: string;
  fill: string;
  fillOpacity?: number;
  /** What a tooltip says of it. */
  label: string;
  /** Its `data-` attributes, which the tests read. */
  data: Record<string, string>;
  onClick?: () => void;
  /** Called when the pointer comes over it. */
  onPoint: () => void;
}) {
  return (
    // biome-ignore lint/a11y/noStaticElementInteractions: see above
    <path
      {...data}
      d={d}
      fill={fill}
      fillOpacity={fillOpacity}
      stroke="#ffffff"
      strokeWidth={GAP}
      className={onClick ? "cursor-pointer" : undefined}
      onClick={onClick}
      onMouseEnter={onPoint}
    >
      <title>{label}</title>
    </path>
  );
}

/**
 * The factors at the level the user has opened, drawn as rings: each factor is an arc of the inner
 * ring as wide as its share of the weight, and its counted sub-factors are the arcs outside it,
 * sharing its angle. Pointing at an arc names it below the rings; clicking one opens the factor,
 * and clicking the centre goes back up a level.
 */
export function Rings({
  title,
  counted,
  parts,
  onOpen,
  onBack,
}: {
  /** What the centre says: the factor opened, or "All factors" at the top. */
  title: string;
  counted: readonly FactorView[];
  /** The counted sub-factors of each factor that opens, by the factor's id. */
  parts: ReadonlyMap<string, readonly FactorView[]>;
  /** Opens a factor of this level, or a sub-factor of one: their ids from this level down. */
  onOpen: (ids: string[]) => void;
  /** Goes up a level. Absent at the top. */
  onBack?: () => void;
}) {
  const [pointed, setPointed] = useState<string | null>(null);
  const factors = slices(counted.map((f) => ({ ...f, value: f.share })));
  const radius = (CENTRE + MIDDLE) / 2;

  return (
    <div>
      <svg
        data-testid="factor-rings"
        viewBox="-50 -50 100 100"
        aria-hidden="true"
        className="mx-auto block w-full max-w-60"
        onMouseLeave={() => setPointed(null)}
      >
        {factors.map(({ item, start, end }) => {
          const middle = (start + end) / 2;
          const inside = slices(
            (parts.get(item.id) ?? []).map((part) => ({
              ...part,
              value: part.share,
            })),
            start,
            end,
          );
          return (
            <g key={item.id}>
              <Arc
                d={arcPath(CENTRE + GAP, MIDDLE, start, end)}
                fill={item.colour}
                label={`${item.name}, ${percent(item.share)}`}
                data={{
                  "data-testid": "factor-tile",
                  "data-factor": item.id,
                  "data-share": item.share.toFixed(4),
                }}
                onClick={item.opens ? () => onOpen([item.id]) : undefined}
                onPoint={() =>
                  setPointed(`${item.name}: ${percent(item.share)}`)
                }
              />
              {end - start >= ROOM_FOR_A_SHARE && (
                <text
                  x={radius * Math.sin(middle)}
                  y={-radius * Math.cos(middle)}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fontSize={5}
                  fill={item.ink}
                  pointerEvents="none"
                >
                  {percent(item.share)}
                </text>
              )}
              {inside.map(({ item: part, start: from, end: to }) => (
                <Arc
                  key={part.id}
                  d={arcPath(MIDDLE + GAP, OUTSIDE, from, to)}
                  fill={part.colour}
                  fillOpacity={0.75}
                  label={`${item.name} › ${part.name}, ${percent(part.share)} of ${item.name}`}
                  data={{
                    "data-testid": "factor-part",
                    "data-factor": part.id,
                    "data-parent": item.id,
                    "data-share": part.share.toFixed(4),
                  }}
                  onClick={() =>
                    onOpen(part.opens ? [item.id, part.id] : [item.id])
                  }
                  onPoint={() =>
                    setPointed(
                      `${item.name} › ${part.name}: ${percent(part.share)}`,
                    )
                  }
                />
              ))}
            </g>
          );
        })}
        <Centre title={title} onBack={onBack} />
      </svg>
      <p className="mt-1 min-h-4 text-center text-xs text-neutral-600">
        {pointed ?? ""}
      </p>
    </div>
  );
}

/** The middle disc, which names the level and, below the top, goes back up when clicked. */
function Centre({ title, onBack }: { title: string; onBack?: () => void }) {
  const wrapped = wrapName(title, 10);
  const lines = wrapped.map((text, index) => ({
    text,
    y: (index - (wrapped.length - 1) / 2) * 5.2,
  }));
  return (
    <>
      {/* biome-ignore lint/a11y/noStaticElementInteractions: see Arc */}
      <circle
        data-testid="factor-centre"
        r={CENTRE}
        fill="#ffffff"
        stroke="#d4d4d4"
        strokeWidth={GAP}
        className={onBack ? "cursor-pointer" : undefined}
        onClick={onBack}
      >
        {onBack && <title>Back up a level</title>}
      </circle>
      <text
        data-testid="factor-title"
        data-title={title}
        textAnchor="middle"
        fontSize={4.4}
        fill="#262626"
        pointerEvents="none"
      >
        {lines.map(({ text, y }) => (
          // Each line is at its own height, so the height names it, and two alike lines are not
          // mistaken for one.
          <tspan key={y} x={0} y={y} dominantBaseline="central">
            {text}
          </tspan>
        ))}
      </text>
    </>
  );
}

import { useMemo, useState } from "react";
import type {
  ManifestFactor,
  ManifestIndicator,
} from "../../generated/manifest.schema";
import type { Profile } from "../../scoring/region";
import { formatNumber } from "./evidence";
import type { Layout } from "./layout";
import {
  atStart,
  countFactor,
  type FactorView,
  holding,
  levelAt,
  withChoice,
  withWeight,
} from "./level";
import {
  bandOf,
  higherIsBetter,
  withDirection,
  withRange,
} from "./preferences";
import { Rings } from "./Rings";
import { squarify } from "./treemap";

// The treemap is laid out in a strip of 100 by 26 units, and drawn in percentages of its container:
// short, so that the sliders, which are the controls, come first (the critique of 2026-11-25).
const BOX = { x: 0, y: 0, w: 100, h: 26 };

const percent = (share: number): string => `${Math.round(share * 100)}%`;

const LAYOUTS: { layout: Layout; name: string }[] = [
  { layout: "boxes", name: "Boxes" },
  { layout: "rings", name: "Rings" },
];

/**
 * The factors the user can weigh, drawn as boxes (a treemap) or as rings (a sunburst) whose sizes
 * are the factors' shares of the weight, with a slider for each. Opening a factor shows its
 * sub-factors; a factor at weight 0 leaves the drawing and waits in the list of those not counted.
 */
export function FactorTree({
  factors,
  indicators = [],
  extents = {},
  profile,
  layout,
  heading = true,
  onChange,
  onLayout,
  onReset,
  onUndoReset,
}: {
  factors: readonly ManifestFactor[];
  /** The measured indicators, to find the ones that offer a choice. */
  indicators?: readonly ManifestIndicator[];
  /** The region's lowest and highest value of each user-range indicator, for its band's slider. */
  extents?: Readonly<Record<string, { min: number; max: number }>>;
  profile: Profile;
  /** How the factors are drawn. */
  layout: Layout;
  /** Whether to show the heading, which a phone's sheet shows on its own handle. */
  heading?: boolean;
  onChange: (profile: Profile) => void;
  onLayout: (layout: Layout) => void;
  /**
   * Goes back to the start (D14): a few essentials, with no directions, bands, limits or way of
   * combining set.
   */
  onReset: () => void;
  /** Brings back the profile from before "Start again", while there is one to bring back. */
  onUndoReset?: () => void;
}) {
  const [path, setPath] = useState<string[]>([]);
  // A picker is drawn in the list of counted factors or in the list of those not counted, and a
  // first pick moves it from one to the other, so which is open is kept here, not in the element.
  const [openPicker, setOpenPicker] = useState<string | null>(null);
  // The factor whose slider is in use: moved to 0, it keeps its row until the slider is let go.
  const [held, setHeld] = useState<string | null>(null);
  const optionsOf = (view: FactorView): ManifestIndicator | undefined =>
    indicators.find((i) => i.id === view.factor.indicator && i.options);
  /** The switch or the band a measured indicator offers, by its preference type. */
  const preference = (view: FactorView) => {
    const indicator = indicators.find((i) => i.id === view.factor.indicator);
    if (indicator?.preference_type === "user-direction") {
      const higher = higherIsBetter(profile, indicator);
      return higher === null ? null : (
        <Direction
          name={view.name}
          higher={higher}
          onSet={(more) => onChange(withDirection(profile, indicator, more))}
        />
      );
    }
    const band = indicator ? bandOf(profile, indicator) : null;
    if (indicator?.preference_type === "user-range" && band) {
      const extent = extents[indicator.id];
      return (
        <BandSlider
          name={view.name}
          band={band}
          min={Math.min(extent?.min ?? band[0], band[0])}
          max={Math.max(extent?.max ?? band[1], band[1])}
          unit={indicator.unit}
          onSet={(next) => onChange(withRange(profile, indicator, next))}
        />
      );
    }
    return null;
  };
  const picker = (view: FactorView) => {
    const indicator = optionsOf(view);
    return indicator ? (
      <Picker
        indicator={indicator}
        picked={profile.choices?.[indicator.id] ?? []}
        open={openPicker === indicator.id}
        onToggle={(open) => setOpenPicker(open ? indicator.id : null)}
        onPick={(option, on) =>
          onChange(
            withChoice(
              profile,
              view.factor,
              option,
              on,
              level.trail.map((step) => step.factor),
            ),
          )
        }
      />
    ) : null;
  };
  const level = useMemo(
    () => levelAt(factors, profile, path),
    [factors, profile, path],
  );
  // The path may name factors that a new bundle no longer has: the level is what it reaches.
  const opened = level.trail.map((step) => step.id);
  const { rows, notCounted } = holding(level, held);
  // A picture of one share (100%) says nothing, so it is drawn only for two or more rows. A row held
  // at 0 still counts here, so that the picture does not vanish mid-drag and move the slider.
  const drawn = rows.length > 1 && level.counted.length > 0;
  const letGo = rows.find((f) => f.id === held && f.effectiveWeight === 0);
  const tiles = useMemo(
    () =>
      squarify(
        level.counted.map((f) => ({ ...f, value: f.share })),
        BOX,
      ),
    [level],
  );
  // The rings also draw the counted sub-factors of each factor, outside it. The boxes do not.
  const parts = useMemo(
    () =>
      new Map(
        layout === "rings"
          ? level.counted
              .filter((f) => f.opens)
              .map((f) => [
                f.id,
                levelAt(factors, profile, [...opened, f.id]).counted,
              ])
          : [],
      ),
    [layout, factors, profile, level, opened],
  );

  return (
    <section aria-label="What matters to you" className="space-y-3 text-sm">
      <div className="flex items-center justify-between gap-2">
        <h2 className={heading ? "font-medium" : "sr-only"}>
          What matters to you
        </h2>
        <fieldset className="m-0 flex min-w-0 overflow-hidden rounded border border-neutral-400 p-0 text-xs">
          <legend className="sr-only">Draw the factors as</legend>
          {LAYOUTS.map(({ layout: option, name }) => (
            <button
              key={option}
              type="button"
              aria-pressed={layout === option}
              className={
                layout === option
                  ? "bg-neutral-800 px-2 py-0.5 text-white"
                  : "bg-white px-2 py-0.5 hover:bg-neutral-100"
              }
              onClick={() => onLayout(option)}
            >
              {name}
            </button>
          ))}
        </fieldset>
      </div>

      <nav
        aria-label="Where you are in the factors"
        className="flex flex-wrap gap-x-1"
      >
        <button
          type="button"
          className="underline"
          onClick={() => setPath([])}
          disabled={opened.length === 0}
        >
          All factors
        </button>
        {level.trail.map((step, index) => (
          <span key={step.id}>
            <span aria-hidden="true">› </span>
            <button
              type="button"
              className="underline"
              onClick={() => setPath(opened.slice(0, index + 1))}
              disabled={index === opened.length - 1}
            >
              {step.name}
            </button>
          </span>
        ))}
      </nav>

      {level.uncounted && (
        <p role="note" className="text-xs text-neutral-600">
          {level.uncounted.name} is not counted, so nothing in it changes the
          map yet.{" "}
          <button
            type="button"
            className="underline"
            onClick={() =>
              level.uncounted && onChange(countFactor(profile, level.uncounted))
            }
          >
            Count {level.uncounted.name}
          </button>
        </p>
      )}

      <div
        data-testid="factor-tree"
        className="relative w-full overflow-hidden rounded"
        style={
          layout === "boxes" && drawn
            ? { aspectRatio: `${BOX.w} / ${BOX.h}` }
            : undefined
        }
      >
        {layout === "rings" && drawn && (
          <Rings
            key={opened.join("/")}
            title={level.trail.at(-1)?.name ?? "All factors"}
            counted={level.counted}
            parts={parts}
            onOpen={(ids) => setPath([...opened, ...ids])}
            onBack={
              opened.length > 0 ? () => setPath(opened.slice(0, -1)) : undefined
            }
          />
        )}
        {layout === "boxes" &&
          drawn &&
          tiles.map(({ item, x, y, w, h }) => (
            // A box opens its factor, as the rings' arcs do; the row's name is the way in for a
            // keyboard, so the box stays out of the tab order and the accessibility tree.
            <div
              key={item.id}
              data-testid="factor-tile"
              data-factor={item.id}
              data-share={item.share.toFixed(4)}
              aria-hidden="true"
              onClick={
                item.opens ? () => setPath([...opened, item.id]) : undefined
              }
              className={`absolute overflow-hidden border border-white p-1 text-xs leading-tight${item.opens ? " cursor-pointer" : ""}`}
              style={{
                left: `${(x / BOX.w) * 100}%`,
                top: `${(y / BOX.h) * 100}%`,
                width: `${(w / BOX.w) * 100}%`,
                height: `${(h / BOX.h) * 100}%`,
                background: item.colour,
                color: item.ink,
              }}
            >
              {/* The strip is short: a name that does not fit ends in "…", and the row below has it
                  whole, beside the same colour. */}
              <span className="block truncate font-medium">{item.name}</span>
              <span className="block">{percent(item.share)}</span>
            </div>
          ))}
        {level.counted.length === 0 && (
          <p className="p-2 text-neutral-600">
            Nothing here counts. Give a factor a weight above 0.
          </p>
        )}
      </div>

      <p role="status" className="sr-only">
        {letGo ? `${letGo.name} is not counted now.` : ""}
      </p>
      <ul className="space-y-2">
        {rows.map((f) => (
          <li key={f.id}>
            <Row
              view={f}
              onOpen={f.opens ? () => setPath([...opened, f.id]) : undefined}
              onWeight={(w) => onChange(withWeight(profile, f.id, w))}
              onHold={(on) =>
                setHeld((now) => (on ? f.id : now === f.id ? null : now))
              }
            />
            {preference(f)}
            {picker(f)}
          </li>
        ))}
      </ul>

      {!atStart(profile) ? (
        <button type="button" className="underline" onClick={onReset}>
          Start again
        </button>
      ) : (
        onUndoReset && (
          <p className="text-xs text-neutral-600">
            Started again from a few essentials.{" "}
            <button
              type="button"
              className="underline"
              aria-label="Undo starting again"
              onClick={onUndoReset}
            >
              Undo
            </button>
          </p>
        )
      )}

      {notCounted.length > 0 && (
        <div>
          <h3 className="font-medium">Not counted</h3>
          <ul className="space-y-1">
            {notCounted.map((f) => (
              <li key={f.id}>
                <div className="flex items-center gap-2">
                  <Swatch colour={f.colour} />
                  <span className="flex-1">{f.name}</span>
                  {f.opens && (
                    <button
                      type="button"
                      className="underline"
                      aria-label={`Open ${f.name}`}
                      onClick={() => setPath([...opened, f.id])}
                    >
                      Open
                    </button>
                  )}
                  {/* A choice counts once something is picked, so it offers no "Count". */}
                  {!optionsOf(f) && (
                    <button
                      type="button"
                      className="underline"
                      aria-label={`Count ${f.name}`}
                      onClick={() => onChange(countFactor(profile, f.factor))}
                    >
                      Count
                    </button>
                  )}
                </div>
                {preference(f)}
                {picker(f)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

function Swatch({ colour }: { colour: string }) {
  return (
    <span
      aria-hidden="true"
      className="inline-block size-3 shrink-0 rounded-sm"
      style={{ background: colour }}
    />
  );
}

function Row({
  view,
  onOpen,
  onWeight,
  onHold,
}: {
  view: FactorView;
  onOpen?: () => void;
  onWeight: (weight: number) => void;
  /**
   * Called with true when the slider is taken (the focus or the pointer), and false when it is let
   * go. Safari gives a range input no focus on a click or a touch, so the pointer counts too.
   */
  onHold: (on: boolean) => void;
}) {
  const off = view.weight === 0;
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <Swatch colour={view.colour} />
        {onOpen ? (
          <button
            type="button"
            className="flex-1 text-left underline"
            aria-label={`Open ${view.name}`}
            onClick={onOpen}
          >
            {view.name} ›
          </button>
        ) : (
          <span className="flex-1">{view.name}</span>
        )}
        <span className="tabular-nums text-neutral-600">
          {percent(view.share)}
        </span>
      </div>
      <input
        type="range"
        min={0}
        max={5}
        step={1}
        value={view.weight}
        aria-label={`Weight of ${view.name}`}
        aria-valuetext={`${view.weight} out of 5`}
        className="w-full"
        onChange={(event) => onWeight(Number(event.target.value))}
        onFocus={() => onHold(true)}
        onBlur={() => onHold(false)}
        onPointerDown={() => onHold(true)}
        onPointerUp={(event) => {
          if (document.activeElement !== event.currentTarget) onHold(false);
        }}
      />
      {off && (
        <p className="text-xs text-neutral-600">
          Not counted now. Move it up to count it.
        </p>
      )}
    </div>
  );
}

/** The "more or less" switch of a user-direction indicator: which way scores better. */
function Direction({
  name,
  higher,
  onSet,
}: {
  name: string;
  higher: boolean;
  onSet: (higher: boolean) => void;
}) {
  const options = [
    { more: true, label: "More is better" },
    { more: false, label: "Less is better" },
  ];
  return (
    <fieldset className="m-0 mt-1 flex w-fit overflow-hidden rounded border border-neutral-400 p-0 text-xs">
      <legend className="sr-only">Which is better for {name}</legend>
      {options.map(({ more, label }) => (
        <button
          key={label}
          type="button"
          aria-pressed={higher === more}
          className={
            higher === more
              ? "bg-neutral-800 px-2 py-0.5 text-white"
              : "bg-white px-2 py-0.5 hover:bg-neutral-100"
          }
          onClick={() => onSet(more)}
        >
          {label}
        </button>
      ))}
    </fieldset>
  );
}

/** The ideal-range band of a user-range indicator: two sliders for the ends of full marks. */
function BandSlider({
  name,
  band,
  min,
  max,
  onSet,
  unit,
}: {
  name: string;
  band: readonly [number, number];
  min: number;
  max: number;
  /** The indicator's unit, which says how to write its numbers. */
  unit: string;
  onSet: (band: [number, number]) => void;
}) {
  const [lo, hi] = band;
  // Whole steps over a wide span such as years; a hundredth of the span over a narrow one.
  const span = max - min;
  const step = span > 50 ? 1 : span > 0 ? span / 100 : 1;
  const plain = (x: number) => formatNumber(x, unit);
  return (
    <div className="mt-1 space-y-1 text-xs" data-testid="band">
      <p>
        Full marks from {plain(lo)} to {plain(hi)}
      </p>
      <label className="flex items-center gap-2">
        <span className="w-8">From</span>
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={lo}
          aria-label={`${name}: lowest for full marks`}
          aria-valuetext={plain(lo)}
          className="flex-1"
          onChange={(event) =>
            onSet([Math.min(Number(event.target.value), hi), hi])
          }
        />
      </label>
      <label className="flex items-center gap-2">
        <span className="w-8">To</span>
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={hi}
          aria-label={`${name}: highest for full marks`}
          aria-valuetext={plain(hi)}
          className="flex-1"
          onChange={(event) =>
            onSet([lo, Math.max(Number(event.target.value), lo)])
          }
        />
      </label>
    </div>
  );
}

/**
 * The options of a choice indicator as check boxes under the titles of their groups. What is
 * picked stays in this browser (D08).
 */
function Picker({
  indicator,
  picked,
  open,
  onToggle,
  onPick,
}: {
  indicator: ManifestIndicator;
  picked: readonly string[];
  open: boolean;
  onToggle: (open: boolean) => void;
  onPick: (option: string, on: boolean) => void;
}) {
  const groups = new Map<string, NonNullable<ManifestIndicator["options"]>>();
  for (const option of indicator.options ?? []) {
    const title = option.group ?? "Options";
    groups.set(title, [...(groups.get(title) ?? []), option]);
  }
  return (
    <details
      className="mt-1"
      data-testid={`picker-${indicator.id}`}
      open={open}
      onToggle={(event) => onToggle(event.currentTarget.open)}
    >
      <summary className="cursor-pointer underline">
        {picked.length > 0 ? `Chosen: ${picked.length}` : "Choose"}
        <span className="sr-only"> for {indicator.name}</span>
      </summary>
      <p className="text-xs text-neutral-600">
        Your choices stay in this browser. Links do not carry them.
      </p>
      {[...groups].map(([title, options]) => (
        <fieldset key={title} className="mt-1">
          <legend className="font-medium">{title}</legend>
          {options.map((option) => (
            <label key={option.id} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={picked.includes(option.id)}
                onChange={(event) => onPick(option.id, event.target.checked)}
              />
              {option.name}
            </label>
          ))}
        </fieldset>
      ))}
    </details>
  );
}

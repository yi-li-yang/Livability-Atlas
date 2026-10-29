import { useMemo, useState } from "react";
import type {
  ManifestFactor,
  ManifestIndicator,
} from "../../generated/manifest.schema";
import type { Profile } from "../../scoring/region";
import {
  countAgain,
  type FactorView,
  levelAt,
  withChoice,
  withWeight,
} from "./level";
import { squarify } from "./treemap";

// The treemap is laid out in a box of 100 by 62 units, and drawn in percentages of its container.
const BOX = { x: 0, y: 0, w: 100, h: 62 };

const percent = (share: number): string => `${Math.round(share * 100)}%`;

/**
 * The factors the user can weigh, drawn as a treemap whose areas are the factors' shares of the
 * weight, with a slider for each. Opening a factor shows its sub-factors; a factor at weight 0
 * leaves the drawing and waits in the list of those not counted.
 */
export function FactorTree({
  factors,
  indicators = [],
  profile,
  onChange,
  onReset,
}: {
  factors: readonly ManifestFactor[];
  /** The measured indicators, to find the ones that offer a choice. */
  indicators?: readonly ManifestIndicator[];
  profile: Profile;
  onChange: (profile: Profile) => void;
  /** Returns every weight to its default. */
  onReset: () => void;
}) {
  const [path, setPath] = useState<string[]>([]);
  // A picker is drawn in the list of counted factors or in the list of those not counted, and a
  // first pick moves it from one to the other, so which is open is kept here, not in the element.
  const [openPicker, setOpenPicker] = useState<string | null>(null);
  const optionsOf = (view: FactorView): ManifestIndicator | undefined =>
    indicators.find((i) => i.id === view.factor.indicator && i.options);
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
  const tiles = useMemo(
    () =>
      squarify(
        level.counted.map((f) => ({ ...f, value: f.share })),
        BOX,
      ),
    [level],
  );

  return (
    <section aria-label="What matters to you" className="space-y-3 text-sm">
      <h2 className="font-medium">What matters to you</h2>

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

      <div
        data-testid="factor-tree"
        className="relative w-full overflow-hidden rounded"
        style={{ aspectRatio: `${BOX.w} / ${BOX.h}` }}
      >
        {tiles.map(({ item, x, y, w, h }) => (
          <div
            key={item.id}
            data-testid="factor-tile"
            data-factor={item.id}
            data-share={item.share.toFixed(4)}
            aria-hidden="true"
            className="absolute overflow-hidden border border-white p-1 text-xs leading-tight"
            style={{
              left: `${(x / BOX.w) * 100}%`,
              top: `${(y / BOX.h) * 100}%`,
              width: `${(w / BOX.w) * 100}%`,
              height: `${(h / BOX.h) * 100}%`,
              background: item.colour,
              color: item.ink,
            }}
          >
            <span className="font-medium">{item.name}</span>{" "}
            <span>{percent(item.share)}</span>
          </div>
        ))}
        {tiles.length === 0 && (
          <p className="p-2 text-neutral-600">
            Nothing here counts. Give a factor a weight above 0.
          </p>
        )}
      </div>

      <ul className="space-y-2">
        {level.counted.map((f) => (
          <li key={f.id}>
            <Row
              view={f}
              onOpen={f.opens ? () => setPath([...opened, f.id]) : undefined}
              onWeight={(w) => onChange(withWeight(profile, f.id, w))}
            />
            {picker(f)}
          </li>
        ))}
      </ul>

      {(Object.keys(profile.weights).length > 0 ||
        (profile.flipped?.length ?? 0) > 0) && (
        <button type="button" className="underline" onClick={onReset}>
          Reset to defaults
        </button>
      )}

      {level.notCounted.length > 0 && (
        <div>
          <h3 className="font-medium">Not counted</h3>
          <ul className="space-y-1">
            {level.notCounted.map((f) => (
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
                  {/* A choice counts once something is picked, so it offers no "again". */}
                  {!optionsOf(f) && (
                    <button
                      type="button"
                      className="underline"
                      aria-label={`Count ${f.name} again`}
                      onClick={() => onChange(countAgain(profile, f.factor))}
                    >
                      Count again
                    </button>
                  )}
                </div>
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
}: {
  view: FactorView;
  onOpen?: () => void;
  onWeight: (weight: number) => void;
}) {
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
      />
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

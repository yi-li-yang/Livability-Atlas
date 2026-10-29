import { useId, useMemo, useState } from "react";
import type { Bundle } from "../../data/bundle";
import type { Limit, Profile } from "../../scoring/region";
import { formatValue } from "../factors/evidence";
import {
  describeLimit,
  type Limitable,
  limitableIndicators,
  rangeOf,
  withLimit,
  withoutLimit,
} from "./limits";

/**
 * The hard limits: must-have rules on a measured indicator. A hex cell that fails one is greyed out
 * and not ranked. The user adds a rule by choosing an indicator and what it must be: at most or at
 * least a number, or one of a list of categories.
 */
export function LimitsPanel({
  bundle,
  profile,
  onChange,
}: {
  bundle: Bundle;
  profile: Profile;
  onChange: (profile: Profile) => void;
}) {
  const choices = useMemo(() => limitableIndicators(bundle), [bundle]);
  const [adding, setAdding] = useState(false);
  const limits = profile.limits ?? [];
  const named = (limit: Limit) =>
    bundle.manifest.indicators.find((i) => i.id === limit.indicator);

  return (
    <section aria-label="Hard limits" className="space-y-2 text-sm">
      <h2 className="font-medium">Hard limits</h2>
      <p className="text-xs text-neutral-600">
        Hex cells that fail a limit are greyed out and not ranked.
      </p>
      {limits.length > 0 && (
        <ul className="space-y-1">
          {limits.map((limit) => (
            <li
              key={limit.indicator}
              className="flex items-start justify-between gap-2"
            >
              <span>{describeLimit(limit, named(limit))}</span>
              <button
                type="button"
                className="shrink-0 underline"
                aria-label={`Remove the limit on ${named(limit)?.name ?? limit.indicator}`}
                onClick={() => onChange(withoutLimit(profile, limit.indicator))}
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
      {adding ? (
        <AddLimit
          bundle={bundle}
          choices={choices}
          onAdd={(limit) => {
            onChange(withLimit(profile, limit));
            setAdding(false);
          }}
          onCancel={() => setAdding(false)}
        />
      ) : (
        <button
          type="button"
          className="underline"
          onClick={() => setAdding(true)}
        >
          Add a hard limit
        </button>
      )}
    </section>
  );
}

function AddLimit({
  bundle,
  choices,
  onAdd,
  onCancel,
}: {
  bundle: Bundle;
  choices: Limitable[];
  onAdd: (limit: Limit) => void;
  onCancel: () => void;
}) {
  const field = useId();
  const [id, setId] = useState(choices[0]?.indicator.id ?? "");
  const [kind, setKind] = useState<"max" | "min">("max");
  const [text, setText] = useState("");
  const [picked, setPicked] = useState<string[]>([]);
  const chosen = choices.find((c) => c.indicator.id === id);
  const range = useMemo(
    () => (chosen ? rangeOf(bundle.columns[chosen.indicator.column]) : null),
    [bundle, chosen],
  );
  if (!chosen) return null;

  const number = Number(text);
  const valid =
    chosen.kind === "number"
      ? text.trim() !== "" && Number.isFinite(number)
      : picked.length > 0;
  const unit = chosen.indicator.unit;
  const submit = () => {
    if (!valid) return;
    const indicator = chosen.indicator.id;
    if (chosen.kind === "category") onAdd({ indicator, in: picked });
    else
      onAdd(
        kind === "max"
          ? { indicator, max: number }
          : { indicator, min: number },
      );
  };

  return (
    <form
      className="space-y-2 rounded border border-neutral-300 p-2"
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
    >
      <label className="block" htmlFor={`${field}-indicator`}>
        Measure
        <select
          id={`${field}-indicator`}
          className="mt-1 w-full rounded border border-neutral-300 p-1"
          value={id}
          onChange={(event) => {
            setId(event.target.value);
            setPicked([]);
            setText("");
          }}
        >
          {choices.map((c) => (
            <option key={c.indicator.id} value={c.indicator.id}>
              {c.indicator.name}
            </option>
          ))}
        </select>
      </label>
      {chosen.kind === "number" ? (
        <>
          <fieldset className="flex gap-3">
            <legend className="sr-only">It must be</legend>
            {(["max", "min"] as const).map((k) => (
              <label key={k} className="flex items-center gap-1">
                <input
                  type="radio"
                  name={`${field}-kind`}
                  checked={kind === k}
                  onChange={() => setKind(k)}
                />
                {k === "max" ? "At most" : "At least"}
              </label>
            ))}
          </fieldset>
          <label className="block" htmlFor={`${field}-number`}>
            Value{unit ? ` (${unit})` : ""}
            <input
              id={`${field}-number`}
              inputMode="decimal"
              className="mt-1 w-full rounded border border-neutral-300 p-1"
              value={text}
              onChange={(event) => setText(event.target.value)}
            />
          </label>
          {range && (
            <p className="text-xs text-neutral-600">
              Across the region: {formatValue(range.min, unit)} to{" "}
              {formatValue(range.max, unit)}, middle{" "}
              {formatValue(range.median, unit)}.
            </p>
          )}
        </>
      ) : (
        <fieldset>
          <legend>Only these{unit ? ` (${unit})` : ""}</legend>
          {chosen.values.map((value) => (
            <label key={value} className="mr-3 inline-flex items-center gap-1">
              <input
                type="checkbox"
                checked={picked.includes(value)}
                onChange={(event) =>
                  setPicked(
                    event.target.checked
                      ? [...picked, value]
                      : picked.filter((p) => p !== value),
                  )
                }
              />
              {value}
            </label>
          ))}
        </fieldset>
      )}
      <div className="flex gap-3">
        <button type="submit" className="underline" disabled={!valid}>
          Add limit
        </button>
        <button type="button" className="underline" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}

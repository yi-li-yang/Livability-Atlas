import type { ScoringMode } from "../../scoring/engine";

const MODES: { mode: ScoringMode; name: string; help: string }[] = [
  {
    mode: "mean",
    name: "Add up",
    help: "Each factor adds its share: a strong one can make up for a weak one.",
  },
  {
    mode: "balanced",
    name: "No weak spots",
    help: "A weak factor pulls the score down harder, so strong ones cannot make up for it.",
  },
];

/** How the factors' scores combine into the livability score: added up, or with no weak spots. */
export function ModeSwitch({
  mode,
  onMode,
}: {
  mode: ScoringMode;
  onMode: (mode: ScoringMode) => void;
}) {
  const help = MODES.find((m) => m.mode === mode)?.help;
  return (
    <section aria-label="How the factors combine" className="space-y-1 text-sm">
      <div className="flex items-center justify-between gap-2">
        <h3 className="font-medium">How the factors combine</h3>
        <fieldset className="m-0 flex min-w-0 overflow-hidden rounded border border-neutral-400 p-0 text-xs">
          <legend className="sr-only">How the factors combine</legend>
          {MODES.map(({ mode: option, name }) => (
            <button
              key={option}
              type="button"
              aria-pressed={mode === option}
              className={
                mode === option
                  ? "bg-neutral-800 px-2 py-0.5 text-white"
                  : "bg-white px-2 py-0.5 hover:bg-neutral-100"
              }
              onClick={() => onMode(option)}
            >
              {name}
            </button>
          ))}
        </fieldset>
      </div>
      <p className="text-xs text-neutral-600">{help}</p>
    </section>
  );
}

import type { StartFrom } from "./presets";

/**
 * "Start from": a list of ready-made preference profiles (presets). Choosing one sets the weights,
 * directions and limits; the choices the user has picked stay. While the profile is still the
 * preset's, it says so, with its description and a way back to what the user had.
 */
export function PresetPicker({
  presets,
  current,
  onChoose,
  onUndo,
}: {
  presets: readonly StartFrom[];
  /** The preset the profile is still exactly at, if any. */
  current: StartFrom | null;
  onChoose: (preset: StartFrom) => void;
  /** Goes back to the profile before the preset, where there is one to go back to. */
  onUndo?: () => void;
}) {
  if (presets.length === 0) return null;
  return (
    <div className="mb-3 space-y-1 text-sm" data-testid="presets">
      <label className="flex items-center gap-2">
        <span className="shrink-0">Start from</span>
        <select
          className="min-w-0 flex-1 border border-edge bg-raised px-1 py-0.5"
          value={current?.id ?? ""}
          onChange={(event) => {
            const preset = presets.find((p) => p.id === event.target.value);
            if (preset) onChoose(preset);
          }}
        >
          <option value="" disabled>
            {current ? "" : "Your own weights"}
          </option>
          {presets.map((preset) => (
            <option key={preset.id} value={preset.id}>
              {preset.name}
            </option>
          ))}
        </select>
      </label>
      {current && (
        <p className="text-xs text-muted">
          {current.description}{" "}
          {onUndo && (
            <button type="button" className="underline" onClick={onUndo}>
              Undo
            </button>
          )}
        </p>
      )}
    </div>
  );
}

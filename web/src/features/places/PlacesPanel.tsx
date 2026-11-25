import { useState } from "react";
import { freeName, MAX_PLACES, type Place } from "./places";

/** What came of looking up a postcode: added, not in the region, or the table did not load. */
export type PostcodeResult = "added" | "not found" | "failed";

/**
 * "Your places": up to three places the user travels to often (work, family). With one or more,
 * the travel time on the map is the time to them, estimated in this browser. A place is found by
 * its postcode, in a table the app loads, or by a click on the map; either way it stays here.
 */
export function PlacesPanel({
  places,
  picking,
  status,
  onFindPostcode,
  onPick,
  onRemove,
}: {
  places: readonly Place[];
  /** Whether the next click on the map adds the place being named. */
  picking: boolean;
  /** A line on how the estimate is going, such as "Working out travel times…". */
  status: string | null;
  /** Adds the named place at a postcode, and says what came of it. */
  onFindPostcode: (name: string, postcode: string) => Promise<PostcodeResult>;
  /** Starts (with a name) or stops (null) waiting for a click on the map. */
  onPick: (name: string | null) => void;
  onRemove: (index: number) => void;
}) {
  const [name, setName] = useState("");
  const [postcode, setPostcode] = useState("");
  const [problem, setProblem] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const label = name.trim() || freeName(places);
  const full = places.length >= MAX_PLACES;
  return (
    <section aria-label="Your places" className="space-y-2 text-sm">
      <h3 className="group-label">Your places</h3>
      <p className="text-xs text-muted">
        Add up to {MAX_PLACES} places you travel to often. Travel time then
        means the time to them, estimated by public transport. They stay in this
        browser; links do not carry them.
      </p>
      {places.length > 0 && (
        <ul className="space-y-1">
          {places.map((place, index) => (
            <li
              key={`${place.name}-${place.lat}-${place.lng}`}
              className="flex justify-between gap-2"
            >
              <span>{place.name}</span>
              <button
                type="button"
                className="underline"
                aria-label={`Remove ${place.name}`}
                onClick={() => onRemove(index)}
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
      {status && <p className="text-xs text-muted">{status}</p>}
      {!full && (
        <form
          className="space-y-1"
          onSubmit={async (event) => {
            event.preventDefault();
            if (busy) return;
            setProblem(null);
            if (!postcode.trim()) {
              setProblem("Type a postcode, or choose the place on the map.");
              return;
            }
            setBusy(true);
            const result = await onFindPostcode(label, postcode).finally(() =>
              setBusy(false),
            );
            if (result === "added") {
              setName("");
              setPostcode("");
            } else if (result === "not found") {
              setProblem("That postcode is not in this region.");
            } else {
              setProblem("The postcodes could not be loaded. Try again.");
            }
          }}
        >
          <label className="flex items-center gap-2">
            <span className="w-16 shrink-0">Name</span>
            <input
              className="min-w-0 flex-1 border border-edge px-1"
              value={name}
              placeholder={freeName(places)}
              onChange={(event) => setName(event.target.value)}
            />
          </label>
          <label className="flex items-center gap-2">
            <span className="w-16 shrink-0">Postcode</span>
            <input
              className="min-w-0 flex-1 border border-edge px-1"
              value={postcode}
              autoComplete="postal-code"
              onChange={(event) => setPostcode(event.target.value)}
            />
          </label>
          <div className="flex flex-wrap gap-x-3">
            <button type="submit" className="underline" disabled={busy}>
              Add by postcode
            </button>
            {picking ? (
              <button
                type="button"
                className="underline"
                onClick={() => onPick(null)}
              >
                Stop choosing on the map
              </button>
            ) : (
              <button
                type="button"
                className="underline"
                onClick={() => onPick(label)}
              >
                Choose on the map
              </button>
            )}
          </div>
          {picking && (
            <p role="status" className="text-xs">
              Click the map where {label} is.
            </p>
          )}
          {problem && (
            <p role="alert" className="text-xs font-medium text-ink">
              {problem}
            </p>
          )}
        </form>
      )}
    </section>
  );
}

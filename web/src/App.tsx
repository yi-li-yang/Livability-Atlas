import { useEffect, useMemo, useState } from "react";
import { type Bundle, loadBundle } from "./data/bundle";
import { HexMap } from "./features/map/HexMap";
import { toHexCells } from "./features/map/hexcells";
import { Legend } from "./features/map/Legend";

const BUNDLES_URL = import.meta.env.VITE_BUNDLES_URL ?? "/bundles";
const REGION = "london";
// The walking skeleton draws one measured indicator: the service level (PTAL).
const INDICATOR = "service-level";

type State =
  | { status: "loading" }
  | { status: "ready"; bundle: Bundle }
  | { status: "failed" };

export function App() {
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    loadBundle(BUNDLES_URL, REGION).then(
      (bundle) => setState({ status: "ready", bundle }),
      (error) => {
        console.error(error);
        setState({ status: "failed" });
      },
    );
  }, []);

  const cells = useMemo(
    () => (state.status === "ready" ? toHexCells(state.bundle, INDICATOR) : []),
    [state],
  );

  return (
    <div className="flex h-screen flex-col">
      <header className="px-4 py-2">
        <h1 className="text-2xl font-semibold">Livability Atlas</h1>
        {state.status === "failed" && (
          <p role="alert" className="text-sm text-red-700">
            The map data could not be loaded. Try again in a moment.
          </p>
        )}
      </header>
      <main className="relative min-h-0 flex-1">
        <HexMap cells={cells} />
        {state.status === "loading" && (
          <p
            role="status"
            className="absolute left-4 top-4 rounded bg-white/90 px-3 py-1 text-sm shadow"
          >
            Loading the map data…
          </p>
        )}
        {state.status === "ready" && (
          <Legend
            title="Public transport service level"
            low="Worse"
            high="Better"
          />
        )}
      </main>
      {state.status === "ready" && (
        <section
          aria-label="Data sources"
          className="px-4 py-1 text-xs text-neutral-600"
        >
          {state.bundle.manifest.datasets.map((dataset) => (
            <p key={dataset.id}>{dataset.attribution}</p>
          ))}
        </section>
      )}
    </div>
  );
}

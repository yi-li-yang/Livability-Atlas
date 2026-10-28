import { useEffect, useMemo, useState } from "react";
import { type Bundle, loadBundle } from "./data/bundle";
import { FactorTree } from "./features/factors/FactorTree";
import { HexMap } from "./features/map/HexMap";
import { cellColours, toHexCells } from "./features/map/hexcells";
import { Legend } from "./features/map/Legend";
import { allLeafScores, type Profile, scoreRegion } from "./scoring/region";

const BUNDLES_URL = import.meta.env.VITE_BUNDLES_URL ?? "/bundles";
const REGION = "london";

type State =
  | { status: "loading" }
  | { status: "ready"; bundle: Bundle }
  | { status: "failed" };

// The weights the user has set. None yet: every factor starts at its default weight.
const DEFAULT_PROFILE: Profile = { weights: {} };

export function App() {
  const [state, setState] = useState<State>({ status: "loading" });
  const [profile, setProfile] = useState<Profile>(DEFAULT_PROFILE);

  useEffect(() => {
    loadBundle(BUNDLES_URL, REGION).then(
      (bundle) => setState({ status: "ready", bundle }),
      (error) => {
        console.error(error);
        setState({ status: "failed" });
      },
    );
  }, []);

  const flipped = profile.flipped;
  const bundle = state.status === "ready" ? state.bundle : null;
  const cells = useMemo(() => (bundle ? toHexCells(bundle) : []), [bundle]);
  // What a cell scores on each indicator depends on the data and the user's directions, not on
  // the weights, so a change of weights only repeats the cheaper weighted sum below.
  const leaves = useMemo(
    () => (bundle ? allLeafScores(bundle, flipped) : null),
    [bundle, flipped],
  );
  const colours = useMemo(
    () =>
      bundle && leaves ? cellColours(scoreRegion(bundle, profile, leaves)) : [],
    [bundle, leaves, profile],
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
        <HexMap cells={cells} colours={colours} />
        {state.status === "loading" && (
          <p
            role="status"
            className="absolute left-4 top-4 rounded bg-white/90 px-3 py-1 text-sm shadow"
          >
            Loading the map data…
          </p>
        )}
        {state.status === "ready" && (
          <aside
            aria-label="Your preferences"
            className="absolute left-4 top-4 max-h-[calc(100%-9rem)] w-80 max-w-[calc(100%-2rem)] overflow-y-auto rounded bg-white/95 p-3 shadow"
          >
            <FactorTree
              factors={state.bundle.manifest.factors}
              profile={profile}
              onChange={setProfile}
            />
          </aside>
        )}
        {state.status === "ready" && (
          <Legend title="Livability score" low="Worse" high="Better" />
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

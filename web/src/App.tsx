import { useEffect, useMemo, useState } from "react";
import { type Bundle, loadBundle } from "./data/bundle";
import { FactorTree } from "./features/factors/FactorTree";
import { QuickLook } from "./features/factors/QuickLook";
import { WhyPanel } from "./features/factors/WhyPanel";
import { CELL_OPACITY } from "./features/map/colour";
import { HexMap, type Hover } from "./features/map/HexMap";
import { cellColours, toHexCells } from "./features/map/hexcells";
import { Legend } from "./features/map/Legend";
import type { ManifestFactor } from "./generated/manifest.schema";
import {
  encodeProfile,
  loadProfile,
  pruneProfile,
  saveProfile,
} from "./profile/storage";
import { explainCell, rankOf, sortedScores } from "./scoring/explain";
import { allLeafScores, type Profile, scoreRegion } from "./scoring/region";

const BUNDLES_URL = import.meta.env.VITE_BUNDLES_URL ?? "/bundles";
const REGION = "london";

type State =
  | { status: "loading" }
  | { status: "ready"; bundle: Bundle }
  | { status: "failed" };

/** The browser's storage, or null where it is blocked, as in some private windows. */
function browserStorage(): Storage | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

/** The ids of every factor and measured indicator in a factor tree. */
function idsIn(factors: readonly ManifestFactor[]): Set<string> {
  const ids = new Set<string>();
  const visit = (factor: ManifestFactor) => {
    ids.add(factor.id);
    if (factor.indicator) ids.add(factor.indicator);
    for (const child of factor.children ?? []) visit(child);
  };
  for (const factor of factors) visit(factor);
  return ids;
}

export function App() {
  const [state, setState] = useState<State>({ status: "loading" });
  const [profile, setProfile] = useState<Profile>(() =>
    loadProfile(window.location.hash, browserStorage()),
  );
  const [hover, setHover] = useState<Hover | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [opacity, setOpacity] = useState(CELL_OPACITY);

  useEffect(() => {
    loadBundle(BUNDLES_URL, REGION).then(
      (bundle) => setState({ status: "ready", bundle }),
      (error) => {
        console.error(error);
        setState({ status: "failed" });
      },
    );
  }, []);

  // The weights stay in this browser: in its storage, and in the link's fragment, which is never
  // sent to a server, so that a link carries them to a friend (D08).
  const loaded = state.status === "ready";
  useEffect(() => {
    if (!loaded) return;
    saveProfile(profile, browserStorage());
    const text = encodeProfile(profile);
    const { pathname, search } = window.location;
    window.history.replaceState(
      null,
      "",
      text ? `#${text}` : `${pathname}${search}`,
    );
  }, [loaded, profile]);
  // A saved profile or link may name factors that this bundle does not have.
  useEffect(() => {
    if (state.status !== "ready") return;
    const known = idsIn(state.bundle.manifest.factors);
    setProfile((current) => {
      const pruned = pruneProfile(current, known);
      return encodeProfile(pruned) === encodeProfile(current)
        ? current
        : pruned;
    });
  }, [state]);

  const flipped = profile.flipped;
  const bundle = state.status === "ready" ? state.bundle : null;
  const cells = useMemo(() => (bundle ? toHexCells(bundle) : []), [bundle]);
  // What a cell scores on each indicator depends on the data and the user's directions, not on
  // the weights, so a change of weights only repeats the cheaper weighted sum below.
  const leaves = useMemo(
    () => (bundle ? allLeafScores(bundle, flipped) : null),
    [bundle, flipped],
  );
  const scores = useMemo(
    () => (bundle && leaves ? scoreRegion(bundle, profile, leaves) : null),
    [bundle, leaves, profile],
  );
  const colours = useMemo(() => (scores ? cellColours(scores) : []), [scores]);
  const ranked = useMemo(
    () => (scores ? sortedScores(scores) : null),
    [scores],
  );

  /** What one cell scores and why, for the quick look and the panel of reasons. */
  const explained = (index: number | null) => {
    if (index === null || !bundle || !scores || !ranked) return null;
    const score = scores[index];
    return {
      explanation: explainCell(bundle, profile, index),
      rank: Number.isNaN(score) ? null : rankOf(ranked, score),
      total: ranked.length,
    };
  };
  const hovered =
    hover && hover.index !== selected ? explained(hover.index) : null;
  const chosen = explained(selected);

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
        <HexMap
          cells={cells}
          colours={colours}
          opacity={opacity}
          selected={selected}
          onHover={setHover}
          onSelect={setSelected}
        />
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
            className="absolute left-4 top-4 z-10 max-h-[calc(100%-9rem)] w-80 max-w-[calc(100%-2rem)] overflow-y-auto rounded bg-white/95 p-3 shadow"
          >
            <FactorTree
              factors={state.bundle.manifest.factors}
              profile={profile}
              onChange={setProfile}
              onReset={() => setProfile({ weights: {} })}
            />
          </aside>
        )}
        {hover && hovered && (
          <div
            data-testid="quick-look"
            className="pointer-events-none absolute z-10 w-52 rounded bg-white/95 p-3 shadow"
            style={{
              left:
                hover.x > window.innerWidth - 280
                  ? hover.x - 220
                  : hover.x + 14,
              top:
                hover.y > window.innerHeight - 260
                  ? hover.y - 150
                  : hover.y + 14,
            }}
          >
            <QuickLook {...hovered} />
          </div>
        )}
        {chosen && <WhyPanel {...chosen} onClose={() => setSelected(null)} />}
        {state.status === "ready" && (
          <Legend
            title="Livability score"
            low="Worse"
            high="Better"
            opacity={opacity}
            onOpacity={setOpacity}
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

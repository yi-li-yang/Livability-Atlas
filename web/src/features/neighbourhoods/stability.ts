import type { Bundle } from "../../data/bundle";
import {
  allLeafScores,
  effectiveWeight,
  excludedCells,
  type Profile,
  scoreRegion,
} from "../../scoring/region";
import { type Sensitivity, sensitivity } from "../../scoring/sensitivity";
import { topNeighbourhoods } from "./top";

/**
 * How stable the top neighbourhoods are when the weights of the top-level factors shift by 20%
 * (scoring.md, section 12). It ranks the neighbourhoods as the app does: by the mean score of the
 * cells that count, leaving out the cells that a hard limit excludes. The leaf scores do not
 * depend on the weights, so they are worked out once for all the scenarios.
 *
 * The places are keyed by their position in the manifest's list of neighbourhoods, as text,
 * because two neighbourhoods can have the same name: `bundle.manifest.neighbourhoods` names them.
 * A factor that counts for nothing (everything inside it at weight 0) gets no scenarios.
 */
export function neighbourhoodStability(
  bundle: Bundle,
  profile: Profile,
  options: { count?: number; change?: number } = {},
): Sensitivity {
  const { count = 10, change } = options;
  const leaves = allLeafScores(
    bundle,
    profile.flipped,
    profile.choices,
    profile.ranges,
  );
  const excluded = excludedCells(bundle, profile.limits ?? []);
  const rank = (p: Profile): string[] =>
    topNeighbourhoods(bundle, scoreRegion(bundle, p, leaves), excluded, {
      count,
    }).map((n) => String(n.position));
  const factors = Object.fromEntries(
    bundle.manifest.factors.map((f) => [f.id, effectiveWeight(f, profile)]),
  );
  return sensitivity(rank, profile, factors, { change });
}

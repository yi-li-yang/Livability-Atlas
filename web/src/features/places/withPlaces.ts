import type { Bundle, Value } from "../../data/bundle";
import {
  meanMinutes,
  placeMinutes,
  type TravelData,
} from "../../travel/estimate";
import type { Place } from "./places";

/** The minutes from every cell to each of the user's places, in their order. */
export function minutesToPlaces(
  travel: TravelData,
  places: readonly Place[],
): Float64Array[] {
  return places.map((place) => placeMinutes(travel, place));
}

/**
 * The bundle as the user's places make it: the travel indicator that the manifest's `travel`
 * names holds the mean of the estimated minutes to the user's places, in place of the minutes to
 * the region's default places. Everything else, and the bundle itself, stays as it was.
 */
export function withPlaces(
  bundle: Bundle,
  perPlace: readonly Float64Array[],
): Bundle {
  const id = bundle.manifest.travel?.indicator;
  const indicator = bundle.manifest.indicators.find((i) => i.id === id);
  if (!indicator || perPlace.length === 0) return bundle;
  const mean = meanMinutes(perPlace);
  const values: Value[] = Array.from(mean, (m) =>
    Number.isNaN(m) ? null : Math.round(m * 10) / 10,
  );
  return {
    ...bundle,
    columns: { ...bundle.columns, [indicator.column]: values },
  };
}

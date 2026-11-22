/**
 * The user's own places (up to 3): a name and a point each. They stay in this browser's storage
 * and never go in a link or anywhere else (D08, D10).
 */

export interface Place {
  name: string;
  lat: number;
  lng: number;
}

/** Where the browser keeps the places. */
export const PLACES_KEY = "atlas.places.v1";

/** How many places a user can add (D10). */
export const MAX_PLACES = 3;

/** The part of `Storage` that the places use, so that tests can stand in for it. */
interface Store {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

const isPlace = (value: unknown): value is Place => {
  const p = value as Place;
  return (
    typeof p === "object" &&
    p !== null &&
    typeof p.name === "string" &&
    p.name.trim() !== "" &&
    Number.isFinite(p.lat) &&
    Number.isFinite(p.lng) &&
    Math.abs(p.lat) <= 90 &&
    Math.abs(p.lng) <= 180
  );
};

/** The places kept in this browser, or none. A broken entry is dropped, not an error. */
export function loadPlaces(store: Store | null): Place[] {
  try {
    const parsed: unknown = JSON.parse(store?.getItem(PLACES_KEY) ?? "[]");
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter(isPlace)
      .slice(0, MAX_PLACES)
      .map(({ name, lat, lng }) => ({ name: name.trim(), lat, lng }));
  } catch {
    return [];
  }
}

/** Keeps the places in this browser. Nothing is sent anywhere. */
export function savePlaces(
  places: readonly Place[],
  store: Store | null,
): void {
  try {
    store?.setItem(PLACES_KEY, JSON.stringify(places));
  } catch {
    // Storage can be full or blocked: the places last until the page closes.
  }
}

/** The places with one more, while there is room for it. A name that another place has already
 * gets a number ("Work 2"), so each place's name is its own and can key a list. */
export function withPlace(places: readonly Place[], place: Place): Place[] {
  if (places.length >= MAX_PLACES) return [...places];
  const taken = new Set(places.map((p) => p.name));
  let name = place.name;
  for (let n = 2; taken.has(name); n += 1) name = `${place.name} ${n}`;
  return [...places, { ...place, name }];
}

/** The places without the one at `index`. */
export function withoutPlace(places: readonly Place[], index: number): Place[] {
  return places.filter((_, i) => i !== index);
}

/** A postcode as the table holds it: no spaces, in capitals. */
export function normalisePostcode(text: string): string {
  return text.replace(/\s+/g, "").toUpperCase();
}

/** The region's postcodes, sorted, with the latitude and longitude of each. */
export interface PostcodeTable {
  postcodes: string[];
  lat: Float64Array;
  lng: Float64Array;
}

/** The point of a postcode in the region's table, or null where it is not there. */
export function findPostcode(
  table: PostcodeTable,
  text: string,
): { lat: number; lng: number } | null {
  const wanted = normalisePostcode(text);
  if (!wanted) return null;
  let lo = 0;
  let hi = table.postcodes.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (table.postcodes[mid] < wanted) lo = mid + 1;
    else hi = mid;
  }
  return table.postcodes[lo] === wanted
    ? { lat: table.lat[lo], lng: table.lng[lo] }
    : null;
}

/** "Place 1", "Place 2", …: the first such name no place has yet. */
export function freeName(places: readonly Place[]): string {
  const taken = new Set(places.map((place) => place.name));
  let n = 1;
  while (taken.has(`Place ${n}`)) n += 1;
  return `Place ${n}`;
}

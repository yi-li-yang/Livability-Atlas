/**
 * The travel estimate to a user's own place (D10), in the browser: the place never leaves it. A
 * cell's time is the quickest of walking straight there (within reach), or walking along the
 * streets to one of its stations, riding the station matrix, and walking from a station near the
 * place. The Python reference (`pipeline/src/atlas/scoring/travel.py`) gives the same numbers on
 * the golden cases of `shared/fixtures/travel/`.
 */

/** The mean radius of the Earth, in metres, as the Python reference uses. */
const EARTH_RADIUS = 6_371_008.8;

export interface TravelConstants {
  reach_minutes: number;
  walk_metres_a_minute: number;
  street_factor: number;
  unreachable: number;
}

export interface Point {
  lat: number;
  lng: number;
}

/** One golden case: a cell, a place, the stations and the matrix, and the expected minutes. */
export interface TravelCase {
  id: string;
  constants: TravelConstants;
  stations: [number, number][];
  matrix: number[][];
  cell: Point & { stations: [number, number][] };
  place: Point;
  expected: number | null;
}

/** The great-circle distance between two points, by the haversine formula. */
export function straightMetres(
  lat1: number,
  lng1: number,
  lat2: number,
  lng2: number,
): number {
  const rad = Math.PI / 180;
  const p1 = lat1 * rad;
  const p2 = lat2 * rad;
  const dp = p2 - p1;
  const dl = (lng2 - lng1) * rad;
  const a =
    Math.sin(dp / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2;
  return 2 * EARTH_RADIUS * Math.asin(Math.sqrt(a));
}

/** The minutes of one golden case, or null where there is no way within reach. */
export function estimateCase(c: TravelCase): number | null {
  const [got] = placeMinutes(
    {
      stations: c.stations.map(([lat, lng]) => ({ lat, lng })),
      matrix: Uint16Array.from(c.matrix.flat()),
      cellStart: Int32Array.from([0, c.cell.stations.length]),
      cellStation: Int32Array.from(c.cell.stations.map(([s]) => s)),
      cellMinutes: Float64Array.from(c.cell.stations.map(([, m]) => m)),
      centres: [{ lat: c.cell.lat, lng: c.cell.lng }],
      constants: c.constants,
    },
    c.place,
  );
  return Number.isNaN(got) ? null : got;
}

/** What the estimate needs for a whole region, from the bundle's travel files. */
export interface TravelData {
  stations: Point[];
  /** Minutes from each station to each, row by row. */
  matrix: Uint16Array;
  /** Cell i's stations are positions cellStart[i] to cellStart[i + 1] of the next two arrays. */
  cellStart: Int32Array;
  cellStation: Int32Array;
  /** The minutes on foot, along the streets, from the cell's centre to that station. */
  cellMinutes: Float64Array;
  /** The centre of each cell. */
  centres: Point[];
  constants: TravelConstants;
}

/**
 * The minutes from every cell to one place, with NaN where there is no way within reach. It works
 * out once the best time from each station to the place, so it takes about as long as the matrix
 * has entries plus the cells' links, a few milliseconds for London.
 */
export function placeMinutes(data: TravelData, place: Point): Float64Array {
  const { reach_minutes, walk_metres_a_minute, street_factor, unreachable } =
    data.constants;
  const walk = (from: Point): number =>
    (straightMetres(from.lat, from.lng, place.lat, place.lng) * street_factor) /
    walk_metres_a_minute;
  const n = data.stations.length;
  const near: { q: number; minutes: number }[] = [];
  data.stations.forEach((station, q) => {
    const minutes = walk(station);
    if (minutes <= reach_minutes) near.push({ q, minutes });
  });
  // The best time from each station: the ride to a station near the place, then the walk.
  const fromStation = new Float64Array(n).fill(Number.POSITIVE_INFINITY);
  for (let s = 0; s < n; s++) {
    const row = s * n;
    let best = Number.POSITIVE_INFINITY;
    for (const { q, minutes } of near) {
      const ride = data.matrix[row + q];
      if (ride !== unreachable && ride + minutes < best) best = ride + minutes;
    }
    fromStation[s] = best;
  }
  const cells = data.centres.length;
  const out = new Float64Array(cells);
  for (let i = 0; i < cells; i++) {
    const direct = walk(data.centres[i]);
    let best = direct <= reach_minutes ? direct : Number.POSITIVE_INFINITY;
    for (let k = data.cellStart[i]; k < data.cellStart[i + 1]; k++) {
      const total = data.cellMinutes[k] + fromStation[data.cellStation[k]];
      if (total < best) best = total;
    }
    out[i] = Number.isFinite(best) ? best : Number.NaN;
  }
  return out;
}

/**
 * The mean of the minutes to each place, cell by cell, with NaN where any place cannot be reached:
 * the value of the travel time indicator once the user has places of their own.
 */
export function meanMinutes(perPlace: readonly Float64Array[]): Float64Array {
  const cells = perPlace[0]?.length ?? 0;
  const out = new Float64Array(cells);
  for (let i = 0; i < cells; i++) {
    let sum = 0;
    for (const minutes of perPlace) sum += minutes[i];
    out[i] = sum / perPlace.length;
  }
  return out;
}

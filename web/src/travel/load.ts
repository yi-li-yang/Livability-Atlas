import { cellToLatLng } from "h3-js";
import { parquetReadObjects } from "hyparquet";
import type { Bundle, Fetcher } from "../data/bundle";
import type { PostcodeTable } from "../features/places/places";
import type { TravelData } from "./estimate";

async function rows(
  fetcher: Fetcher,
  url: string,
): Promise<Record<string, unknown>[]> {
  const reply = await fetcher(url);
  if (!reply.ok) throw new Error(`Could not load ${url} (${reply.status})`);
  return (await parquetReadObjects({
    file: await reply.arrayBuffer(),
  })) as Record<string, unknown>[];
}

const num = (value: unknown): number => Number(value);

/**
 * Loads what the travel estimate needs from the bundle's travel files, or null where the bundle
 * has none. The app asks for them only once the user adds a place, since the matrix is large.
 */
export async function loadTravel(
  bundle: Bundle,
  fetcher: Fetcher = (url) => fetch(url),
): Promise<TravelData | null> {
  const travel = bundle.manifest.travel;
  if (!travel || !bundle.folder) return null;
  const [stations, links, matrix] = await Promise.all([
    rows(fetcher, `${bundle.folder}/${travel.stations}`),
    rows(fetcher, `${bundle.folder}/${travel.cell_stations}`),
    rows(fetcher, `${bundle.folder}/${travel.matrix}`),
  ]);
  // The links are sorted by cell, so each cell's run starts where the previous one ends.
  const cellStart = new Int32Array(bundle.cells.length + 1);
  for (const link of links) cellStart[num(link.cell) + 1] += 1;
  for (let i = 0; i < bundle.cells.length; i++)
    cellStart[i + 1] += cellStart[i];
  return {
    stations: stations.map((s) => ({ lat: num(s.lat), lng: num(s.lng) })),
    matrix: Uint16Array.from(matrix, (row) => num(row.minutes)),
    cellStart,
    cellStation: Int32Array.from(links, (link) => num(link.station)),
    cellMinutes: Float64Array.from(links, (link) => num(link.minutes)),
    centres: bundle.cells.map((cell) => {
      const [lat, lng] = cellToLatLng(cell);
      return { lat, lng };
    }),
    constants: {
      reach_minutes: travel.reach_minutes,
      walk_metres_a_minute: travel.walk_metres_a_minute,
      street_factor: travel.street_factor,
      unreachable: travel.unreachable,
    },
  };
}

/**
 * Loads the region's table of postcodes, or null where the bundle has none. It is read whole, so
 * that the postcode a user types is looked up here and sent nowhere.
 */
export async function loadPostcodes(
  bundle: Bundle,
  fetcher: Fetcher = (url) => fetch(url),
): Promise<PostcodeTable | null> {
  const file = bundle.manifest.travel?.postcodes;
  if (!file || !bundle.folder) return null;
  const table = await rows(fetcher, `${bundle.folder}/${file}`);
  return {
    postcodes: table.map((row) => String(row.postcode)),
    lat: Float64Array.from(table, (row) => num(row.lat)),
    lng: Float64Array.from(table, (row) => num(row.lng)),
  };
}

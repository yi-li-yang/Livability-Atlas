import { parquetReadObjects } from "hyparquet";
import type { Manifest } from "../generated/manifest.schema";

export type Cell = string;
export type Value = string | number | null;

/** A region's data bundle, read: its manifest, its hex cells, and one column of values for each indicator. */
export interface Bundle {
  manifest: Manifest;
  /** H3 cell indexes, sorted. */
  cells: Cell[];
  /** Each indicator's raw values, keyed by the manifest's column name, in the order of `cells`. */
  columns: Record<string, Value[]>;
}

type Fetcher = (url: string) => Promise<Response>;

async function get(fetcher: Fetcher, url: string): Promise<Response> {
  const reply = await fetcher(url);
  if (!reply.ok) throw new Error(`Could not load ${url} (${reply.status})`);
  return reply;
}

/**
 * Loads the newest bundle of a region from `${baseUrl}/${region}/`: `latest.json` names the version,
 * and the version's folder holds `manifest.json` and `cells.parquet`. Everything stays in the
 * browser: the app only reads these static files.
 */
export async function loadBundle(
  baseUrl: string,
  region: string,
  fetcher: Fetcher = (url) => fetch(url),
): Promise<Bundle> {
  const root = `${baseUrl}/${region}`;
  const { version } = (await (
    await get(fetcher, `${root}/latest.json`)
  ).json()) as { version: string };
  const manifest = (await (
    await get(fetcher, `${root}/${version}/manifest.json`)
  ).json()) as Manifest;
  if (manifest.format_version !== 1) {
    throw new Error(
      `The bundle's format is ${manifest.format_version}, which this app cannot read`,
    );
  }
  const file = await (
    await get(fetcher, `${root}/${version}/cells.parquet`)
  ).arrayBuffer();
  const rows = (await parquetReadObjects({ file })) as Record<string, Value>[];

  const cells = rows.map((row) => row.cell as Cell);
  const columns: Record<string, Value[]> = {};
  for (const indicator of manifest.indicators) {
    // A choice indicator has a column for each option, and none of its own.
    const named = indicator.options?.map((o) => o.column) ?? [indicator.column];
    for (const column of named) {
      columns[column] = rows.map((row) => row[column] ?? null);
    }
  }
  return { manifest, cells, columns };
}

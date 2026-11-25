import type { LayerSpecification } from "maplibre-gl";
import { LAND_COLOURS, WATER } from "./colour";
import type { Basemap } from "./theme";

/**
 * Where the hex cells sit among the basemap's layers (D23). From the bottom up: the land (the
 * background, land use, parks, buildings), the cells, then the water, roads, railways and place
 * names, so that the map's lines and names stay sharp over the colours.
 */

/** The basemap's source-layers that are land: they go under the cells. */
const LAND = new Set(["landuse", "landcover", "park", "building", "aeroway"]);

function isLand(layer: LayerSpecification): boolean {
  if (layer.type === "background" || layer.type === "raster") return true;
  return (
    layer.type === "fill" &&
    "source-layer" in layer &&
    LAND.has(layer["source-layer"] ?? "")
  );
}

export interface Stack {
  /** The land layers that sit above `cellsBefore` in the style, to move under it, in order. */
  move: string[];
  /** The id of the layer the cells go under: the first that is not land. */
  cellsBefore: string | undefined;
  /** The id of the first label layer, which the selected cell and the user's places go under. */
  labelsBefore: string | undefined;
}

/**
 * Works out the stack from the style's layers, by their type and source-layer rather than by id,
 * so that it still holds if the basemap's style changes.
 */
export function stackCells(layers: readonly LayerSpecification[]): Stack {
  const first = layers.find((layer) => !isLand(layer));
  const firstIndex = first ? layers.indexOf(first) : layers.length;
  return {
    move: layers
      .slice(firstIndex)
      .filter(isLand)
      .map((layer) => layer.id),
    cellsBefore: first?.id,
    labelsBefore: layers.find((layer) => layer.type === "symbol")?.id,
  };
}

/**
 * Land use, drawn from the basemap's own OpenMapTiles source so that a cell with few or no homes
 * shows what is there: parks and woods, industrial and business land, railways. The tints are pale
 * and greyed, so that they never pass for a score colour (colour.ts).
 */
export function landUse(land: Basemap["land"]): LayerSpecification[] {
  return [
    {
      id: "atlas-green",
      type: "fill",
      source: "openmaptiles",
      "source-layer": "landcover",
      filter: [
        "match",
        ["get", "class"],
        ["grass", "wood", "farmland", "wetland"],
        true,
        false,
      ],
      paint: { "fill-color": land.green },
    },
    {
      id: "atlas-park",
      type: "fill",
      source: "openmaptiles",
      "source-layer": "park",
      paint: { "fill-color": land.green },
    },
    {
      id: "atlas-landuse",
      type: "fill",
      source: "openmaptiles",
      "source-layer": "landuse",
      filter: [
        "match",
        ["get", "class"],
        [
          "industrial",
          "commercial",
          "retail",
          "garages",
          "quarry",
          "railway",
          "cemetery",
        ],
        true,
        false,
      ],
      paint: {
        "fill-color": [
          "match",
          ["get", "class"],
          "railway",
          land.railway,
          "cemetery",
          land.green,
          land.industry,
        ],
      },
    },
  ];
}

/** The land use in the light theme. */
export const LAND_USE = landUse(LAND_COLOURS);

/** The basemap's layers that the stack hides: Positron's grey wash over homes only muddies the cells. */
const HIDE = ["landuse_residential"];

/** What `restack` needs of a MapLibre map (methods, so that MapLibre's own types fit). */
export interface Restackable {
  getStyle(): { layers: LayerSpecification[] };
  getLayer(id: string): unknown;
  moveLayer(id: string, before?: string): unknown;
  addLayer(layer: LayerSpecification, before?: string): unknown;
  setLayoutProperty(id: string, name: "visibility", value: "none"): unknown;
  setPaintProperty(id: string, name: string, value: unknown): unknown;
}

/**
 * The colours of the dark theme's basemap (DESIGN.md). `ground`, `boundary` and `name` are the
 * visual system's ground, edge and muted grey, read from the page; the others are the basemap's own,
 * a step either side of the ground. Roads and railways are a step lighter than the ground, so that
 * they still cross the cells as Positron's white roads do.
 */
export interface DarkPaint {
  ground: string;
  boundary: string;
  name: string;
  building: string;
  road: string;
  roadCasing: string;
  waterName: string;
}

export const DARK_BASEMAP_OWN = {
  building: "#1b1b1a",
  road: "#2c2d2a",
  roadCasing: "#1c1c1b",
  waterName: "#8a9aa3",
} as const;

/** Positron repainted, layer by layer by its type and source-layer, in the stone of the dark ground. */
function paintDark(
  map: Restackable,
  basemap: Basemap,
  colours: DarkPaint,
): void {
  const paint = (id: string, name: string, value: unknown) =>
    map.setPaintProperty(id, name, value);
  for (const layer of map.getStyle().layers) {
    const part = "source-layer" in layer ? layer["source-layer"] : undefined;
    const id = layer.id;
    if (layer.type === "background") {
      paint(id, "background-color", colours.ground);
    } else if (layer.type === "fill") {
      if (part === "water") paint(id, "fill-color", basemap.water);
      else if (part === "building") {
        paint(id, "fill-color", colours.building);
        paint(id, "fill-outline-color", colours.building);
      } else if (part === "park" || part === "landcover")
        paint(id, "fill-color", basemap.land.green);
      else paint(id, "fill-color", colours.ground);
    } else if (layer.type === "line") {
      if (part === "waterway") paint(id, "line-color", basemap.water);
      else if (part === "boundary") paint(id, "line-color", colours.boundary);
      else if (id.includes("dashline")) paint(id, "line-color", colours.ground);
      else if (id.includes("casing"))
        paint(id, "line-color", colours.roadCasing);
      else paint(id, "line-color", colours.road);
      // Over the cells a dark road is a stronger line than a white one over the light map, so the
      // roads are half seen: they still say where the streets are without netting the scores.
      if (part === "transportation") paint(id, "line-opacity", 0.5);
    } else if (layer.type === "symbol") {
      const water = part === "water_name" || part === "waterway";
      paint(id, "text-color", water ? colours.waterName : colours.name);
      paint(id, "text-halo-color", colours.ground);
    }
  }
}

/**
 * Restacks a loaded basemap, adds the land use, and says where the cells go. In the dark theme it
 * repaints the basemap first.
 */
export function restack(
  map: Restackable,
  basemap?: Basemap,
  dark?: DarkPaint,
): Stack {
  if (dark && basemap) paintDark(map, basemap, dark);
  const stack = stackCells(map.getStyle().layers);
  for (const id of stack.move) map.moveLayer(id, stack.cellsBefore);
  for (const id of HIDE) {
    if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", "none");
  }
  for (const layer of basemap ? landUse(basemap.land) : LAND_USE)
    map.addLayer(layer, stack.cellsBefore);
  if (map.getLayer("water"))
    map.setPaintProperty("water", "fill-color", basemap?.water ?? WATER);
  return stack;
}

import type { LayerSpecification } from "maplibre-gl";
import { LAND_COLOURS, WATER } from "./colour";

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
export const LAND_USE: LayerSpecification[] = [
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
    paint: { "fill-color": LAND_COLOURS.green },
  },
  {
    id: "atlas-park",
    type: "fill",
    source: "openmaptiles",
    "source-layer": "park",
    paint: { "fill-color": LAND_COLOURS.green },
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
        LAND_COLOURS.railway,
        "cemetery",
        LAND_COLOURS.green,
        LAND_COLOURS.industry,
      ],
    },
  },
];

/** The basemap's layers that the stack hides: Positron's grey wash over homes only muddies the cells. */
const HIDE = ["landuse_residential"];

/** What `restack` needs of a MapLibre map (methods, so that MapLibre's own types fit). */
export interface Restackable {
  getStyle(): { layers: LayerSpecification[] };
  getLayer(id: string): unknown;
  moveLayer(id: string, before?: string): unknown;
  addLayer(layer: LayerSpecification, before?: string): unknown;
  setLayoutProperty(id: string, name: "visibility", value: "none"): unknown;
  setPaintProperty(id: string, name: "fill-color", value: string): unknown;
}

/** Restacks a loaded basemap, adds the land use, and says where the cells go. */
export function restack(map: Restackable): Stack {
  const stack = stackCells(map.getStyle().layers);
  for (const id of stack.move) map.moveLayer(id, stack.cellsBefore);
  for (const id of HIDE) {
    if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", "none");
  }
  for (const layer of LAND_USE) map.addLayer(layer, stack.cellsBefore);
  if (map.getLayer("water")) map.setPaintProperty("water", "fill-color", WATER);
  return stack;
}

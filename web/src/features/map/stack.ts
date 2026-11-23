import type { LayerSpecification, StyleSpecification } from "maplibre-gl";

/**
 * SPIKE: the map styles compared in spike/map-layers, chosen with `?mapstyle=`.
 * - now: the cells over the whole basemap, as today.
 * - a: the cells under the water, roads and labels, with land use drawn under them.
 * - b: as a, but the basemap stays neutral grey: only the cells carry colour.
 * - c: as a, but each cell is a ring in its score colour, with the map visible inside.
 */
export type MapStyle = "now" | "a" | "b" | "c";

export function mapStyleFromUrl(search: string): MapStyle {
  const value = new URLSearchParams(search).get("mapstyle");
  return value === "a" || value === "b" || value === "c" ? value : "now";
}

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

/**
 * Where the cells go in the basemap's stack: the land layers move under the first layer that is
 * not land (water, roads, labels), keeping their order, and the cells go just under that layer.
 */
export function stackCells(layers: readonly LayerSpecification[]): {
  /** The land layers that sit above `cellsBefore` in the style, to move under it. */
  move: string[];
  /** The id of the layer the cells go under. */
  cellsBefore: string | undefined;
  /** The id of the first label layer, which the outlines and places go under. */
  labelsBefore: string | undefined;
} {
  const first = layers.find((layer) => !isLand(layer));
  const firstIndex = first ? layers.indexOf(first) : layers.length;
  const move = layers
    .slice(firstIndex)
    .filter(isLand)
    .map((layer) => layer.id);
  return {
    move,
    cellsBefore: first?.id,
    labelsBefore: layers.find((layer) => layer.type === "symbol")?.id,
  };
}

const GREEN = "#D3E4C3";

/** Land use, drawn from the basemap's own tiles so that a cell with few homes shows what is there. */
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
    paint: { "fill-color": GREEN },
  },
  {
    id: "atlas-park",
    type: "fill",
    source: "openmaptiles",
    "source-layer": "park",
    paint: { "fill-color": GREEN },
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
        "hospital",
        "school",
        "university",
        "college",
        "stadium",
        "pitch",
      ],
      true,
      false,
    ],
    paint: {
      "fill-color": [
        "match",
        ["get", "class"],
        ["industrial", "commercial", "retail", "garages", "quarry"],
        "#DCD6E6",
        "railway",
        "#E3DCD0",
        "cemetery",
        GREEN,
        "#E8E3D8",
      ],
    },
  },
];

/** Restacks a loaded basemap for a map style. */
export function restack(
  map: {
    getStyle: () => StyleSpecification;
    moveLayer: (id: string, before?: string) => void;
    addLayer: (layer: LayerSpecification, before?: string) => void;
    setLayoutProperty: (id: string, name: string, value: unknown) => void;
    setPaintProperty: (id: string, name: string, value: unknown) => void;
    getLayer: (id: string) => unknown;
  },
  style: MapStyle,
): { cellsBefore?: string; labelsBefore?: string } {
  const { move, cellsBefore, labelsBefore } = stackCells(map.getStyle().layers);
  if (style === "now") return {};
  for (const id of move) map.moveLayer(id, cellsBefore);
  const hide = (id: string) => {
    if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", "none");
  };
  // Positron's grey wash over homes only muddies the cells.
  hide("landuse_residential");
  if (style === "b") {
    hide("park");
    hide("landcover_wood");
  } else {
    for (const layer of LAND_USE) map.addLayer(layer, cellsBefore);
    if (map.getLayer("water"))
      map.setPaintProperty("water", "fill-color", "#BCD4E0");
  }
  return { cellsBefore, labelsBefore };
}

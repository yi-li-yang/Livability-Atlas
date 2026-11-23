import type { LayerSpecification } from "maplibre-gl";
import { describe, expect, it } from "vitest";
import { LAND_USE, type Restackable, restack, stackCells } from "./stack";

const fill = (id: string, sourceLayer: string): LayerSpecification => ({
  id,
  type: "fill",
  source: "openmaptiles",
  "source-layer": sourceLayer,
});
const line = (id: string, sourceLayer: string): LayerSpecification => ({
  id,
  type: "line",
  source: "openmaptiles",
  "source-layer": sourceLayer,
});
const symbol = (id: string): LayerSpecification => ({
  id,
  type: "symbol",
  source: "openmaptiles",
  "source-layer": "place",
});

// The shape of OpenFreeMap's Positron: a land layer after the water, and buildings among the roads.
const POSITRON: LayerSpecification[] = [
  { id: "background", type: "background" },
  fill("park", "park"),
  fill("water", "water"),
  fill("landuse_residential", "landuse"),
  fill("landcover_wood", "landcover"),
  line("waterway", "waterway"),
  fill("building", "building"),
  line("highway_minor", "transportation"),
  symbol("label_town"),
  symbol("label_city"),
];

describe("stackCells", () => {
  it("puts the cells under the first layer that is not land", () => {
    expect(stackCells(POSITRON).cellsBefore).toBe("water");
  });

  it("moves the land layers that sit higher down under the cells, in their order", () => {
    expect(stackCells(POSITRON).move).toEqual([
      "landuse_residential",
      "landcover_wood",
      "building",
    ]);
  });

  it("puts the selected cell and the user's places under the first label", () => {
    expect(stackCells(POSITRON).labelsBefore).toBe("label_town");
  });

  it("draws the cells on top when the style is all land", () => {
    const stack = stackCells([{ id: "background", type: "background" }]);
    expect(stack).toEqual({
      move: [],
      cellsBefore: undefined,
      labelsBefore: undefined,
    });
  });
});

/** A stand-in for a MapLibre map, which keeps its layers in a list. */
function fakeMap(layers: LayerSpecification[]): Restackable & {
  order: () => string[];
  hidden: Set<string>;
} {
  let list = [...layers];
  const hidden = new Set<string>();
  const insert = (layer: LayerSpecification, before?: string) => {
    const at = before ? list.findIndex((l) => l.id === before) : list.length;
    list.splice(at < 0 ? list.length : at, 0, layer);
  };
  return {
    getStyle: () => ({ layers: list }),
    getLayer: (id) => list.find((layer) => layer.id === id),
    moveLayer: (id, before) => {
      const layer = list.find((l) => l.id === id);
      if (!layer) return;
      list = list.filter((l) => l.id !== id);
      insert(layer, before);
    },
    addLayer: insert,
    setLayoutProperty: (id, name, value) => {
      if (name === "visibility" && value === "none") hidden.add(id);
    },
    setPaintProperty: () => {},
    order: () => list.map((layer) => layer.id),
    hidden,
  };
}

describe("restack", () => {
  it("leaves only land under the cells, with the land use on top of it", () => {
    const map = fakeMap(POSITRON);
    const stack = restack(map);
    const order = map.order();
    const cells = order.indexOf(stack.cellsBefore ?? "");
    expect(order.slice(0, cells)).toEqual([
      "background",
      "park",
      "landuse_residential",
      "landcover_wood",
      "building",
      ...LAND_USE.map((layer) => layer.id),
    ]);
    expect(order.slice(cells)).toEqual([
      "water",
      "waterway",
      "highway_minor",
      "label_town",
      "label_city",
    ]);
  });

  it("hides Positron's grey wash over homes", () => {
    const map = fakeMap(POSITRON);
    restack(map);
    expect(map.hidden).toEqual(new Set(["landuse_residential"]));
  });
});

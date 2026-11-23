import { PolygonLayer, ScatterplotLayer } from "@deck.gl/layers";
import { MapLibreOverlay } from "@deck.gl/maplibre";
import { Map as MapLibreMap, setWorkerUrl } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import { useEffect, useRef, useState } from "react";
import type { Rgba } from "./colour";
import type { HexCell } from "./hexcells";
import { LONDON_BOUNDS, LONDON_CENTRE } from "./london";
import { restack, type Stack } from "./stack";

// MapLibre 6 looks for its worker script beside the bundle, where Vite does not
// put it. Importing it with ?url makes Vite emit it, and this points MapLibre there.
setWorkerUrl(workerUrl);

// OpenFreeMap needs no key (docs/tech-stack.md). Positron is its light grey style, made to sit
// under data: its own colours stay out of the way of the cells'. stack.ts adds the land use.
const STYLE_URL = "https://tiles.openfreemap.org/styles/positron";

/** The prop `@deck.gl/maplibre` reads to put a layer under one of the basemap's (it declares no type for it). */
type InMap = { beforeId?: string };

/** Where the pointer is over a cell, in pixels from the map's top left corner. */
export interface Hover {
  index: number;
  x: number;
  y: number;
}

/**
 * A basemap of London with the hex cells drawn inside it, coloured by their score (D23): over the
 * land, under the water, roads and place names, which stay sharp. A cell with few or no homes has
 * no fill, so the land use under it shows. The user sets how solid the cells are.
 *
 * The cells are deck.gl layers interleaved with MapLibre's (`@deck.gl/maplibre`). deck.gl adds
 * them to the map only while the style is fully loaded, and MapLibre counts the style as loading
 * while any tile loads, so the layers are given to deck.gl once the map is first idle.
 */
export function HexMap({
  cells,
  colours,
  outlines,
  opacity,
  selected,
  focus,
  places = [],
  onHover,
  onSelect,
}: {
  cells: HexCell[];
  /** The colour of each cell, in the order of `cells`. */
  colours: Rgba[];
  /** The colour of each cell's outline, such as that of a cell with few or no homes. */
  outlines?: Rgba[];
  /** How much of a cell's colour shows over the basemap, from 0 to 1. */
  opacity: number;
  /** The index of the cell the user has clicked, outlined on the map. */
  selected: number | null;
  /** Where to take the map: a new `request` number makes it fly there, as a repeated choice must. */
  focus: { lng: number; lat: number; request: number } | null;
  /** The user's own places, marked on the map. */
  places?: readonly { name: string; lat: number; lng: number }[];
  onHover: (hover: Hover | null) => void;
  /** Called with the cell that was clicked, or null for a click on no cell. */
  onSelect: (index: number | null) => void;
}) {
  const container = useRef<HTMLDivElement>(null);
  const overlay = useRef<MapLibreOverlay | null>(null);
  const [stack, setStack] = useState<Stack | null>(null);
  const map = useRef<MapLibreMap | null>(null);

  useEffect(() => {
    if (!container.current) return;
    const basemap = new MapLibreMap({
      container: container.current,
      style: STYLE_URL,
      center: LONDON_CENTRE,
      zoom: 10,
      maxBounds: [
        [LONDON_BOUNDS[0] - 0.5, LONDON_BOUNDS[1] - 0.3],
        [LONDON_BOUNDS[2] + 0.5, LONDON_BOUNDS[3] + 0.3],
      ],
    });
    const layers = new MapLibreOverlay({ interleaved: true, layers: [] });
    basemap.addControl(layers);
    basemap.once("style.load", () => {
      const stacked = restack(basemap);
      basemap.once("idle", () => setStack(stacked));
    });
    overlay.current = layers;
    map.current = basemap;
    return () => {
      overlay.current = null;
      map.current = null;
      basemap.remove();
    };
  }, []);

  useEffect(() => {
    if (focus) {
      map.current?.flyTo({
        center: [focus.lng, focus.lat],
        zoom: 13,
        duration: 900,
      });
    }
  }, [focus]);

  useEffect(() => {
    if (!stack) return;
    overlay.current?.setProps({
      layers: [
        new PolygonLayer<HexCell, InMap>({
          id: "hex-cells",
          beforeId: stack.cellsBefore,
          data: cells,
          getPolygon: (cell) => cell.polygon,
          // Read by index, so that a new score only re-evaluates the colours, not the shapes.
          getFillColor: (_cell, { index }) => colours[index],
          getLineColor: (_cell, { index }) => outlines?.[index] ?? [0, 0, 0, 0],
          updateTriggers: { getFillColor: colours, getLineColor: outlines },
          filled: true,
          stroked: outlines !== undefined,
          lineWidthUnits: "pixels",
          getLineWidth: 1,
          opacity,
          pickable: true,
          autoHighlight: true,
          highlightColor: [255, 255, 255, 110],
          onHover: ({ index, x, y }) =>
            onHover(index >= 0 ? { index, x, y } : null),
          onClick: ({ index }) => onSelect(index >= 0 ? index : null),
        }),
        new PolygonLayer<HexCell, InMap>({
          id: "selected-cell",
          beforeId: stack.labelsBefore,
          data: selected === null ? [] : [cells[selected]],
          getPolygon: (cell) => cell.polygon,
          filled: false,
          stroked: true,
          getLineColor: [20, 20, 20, 255],
          lineWidthMinPixels: 3,
        }),
        new ScatterplotLayer<{ name: string; lat: number; lng: number }, InMap>(
          {
            id: "your-places",
            beforeId: stack.labelsBefore,
            data: places,
            getPosition: (place) => [place.lng, place.lat],
            getRadius: 7,
            radiusUnits: "pixels",
            getFillColor: [255, 255, 255, 255],
            getLineColor: [20, 20, 20, 255],
            lineWidthMinPixels: 3,
            stroked: true,
          },
        ),
      ],
    });
  }, [
    stack,
    cells,
    colours,
    outlines,
    opacity,
    selected,
    places,
    onHover,
    onSelect,
  ]);

  return (
    <div
      ref={container}
      data-testid="map"
      data-cells={cells.length}
      className="h-full w-full"
    />
  );
}

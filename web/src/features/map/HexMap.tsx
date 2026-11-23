import { PolygonLayer, ScatterplotLayer } from "@deck.gl/layers";
import { MapLibreOverlay } from "@deck.gl/maplibre";
import { Map as MapLibreMap, setWorkerUrl } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import { useEffect, useRef, useState } from "react";
import type { Rgba } from "./colour";
import type { HexCell } from "./hexcells";
import { LONDON_BOUNDS, LONDON_CENTRE } from "./london";
import { mapStyleFromUrl, restack } from "./stack";

// SPIKE: which map style to draw, from `?mapstyle=` (see stack.ts).
const MAP_STYLE = mapStyleFromUrl(window.location.search);

/** SPIKE (style c): a hexagon shrunk towards its centre, so that each ring sits inside its cell. */
function inset(polygon: [number, number][], by = 0.86): [number, number][] {
  const n = polygon.length;
  const cx = polygon.reduce((sum, [x]) => sum + x, 0) / n;
  const cy = polygon.reduce((sum, [, y]) => sum + y, 0) / n;
  return polygon.map(([x, y]) => [cx + (x - cx) * by, cy + (y - cy) * by]);
}

// MapLibre 6 looks for its worker script beside the bundle, where Vite does not
// put it. Importing it with ?url makes Vite emit it, and this points MapLibre there.
setWorkerUrl(workerUrl);

// OpenFreeMap needs no key (docs/tech-stack.md). Positron is its light grey style, made to sit
// under data: its own colours stay out of the way of the cells'.
const STYLE_URL = "https://tiles.openfreemap.org/styles/positron";

/** Where the pointer is over a cell, in pixels from the map's top left corner. */
export interface Hover {
  index: number;
  x: number;
  y: number;
}

/**
 * A basemap of London with the hex cells drawn over it, coloured by their score. The cells are
 * translucent so that the streets show through; the user sets how much.
 *
 * deck.gl's interleaved mode would draw the cells beneath the basemap's place names, but deck.gl
 * 9.4 fails against MapLibre 6 there (its `getViewport` reads a transform that has changed), so
 * the cells go in a canvas of their own over the map.
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
  const [stack, setStack] = useState<{
    cellsBefore?: string;
    labelsBefore?: string;
  } | null>(MAP_STYLE === "now" ? {} : null);
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
    const layers = new MapLibreOverlay({
      interleaved: MAP_STYLE !== "now",
      layers: [],
    });
    basemap.addControl(layers);
    if (MAP_STYLE !== "now") {
      // deck.gl adds its layers to the map only while the style is fully loaded, which it is not
      // while tiles load, so wait for the map to settle once.
      basemap.once("style.load", () => {
        const stacked = restack(basemap, MAP_STYLE);
        basemap.once("idle", () => setStack(stacked));
      });
    }
    overlay.current = layers;
    map.current = basemap;
    // SPIKE: lets the screenshot script move the map.
    (window as unknown as { atlasMap?: MapLibreMap }).atlasMap = basemap;
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
    const rings = MAP_STYLE === "c";
    overlay.current?.setProps({
      layers: [
        new PolygonLayer<HexCell>({
          id: "hex-cells",
          beforeId: stack.cellsBefore,
          data: cells,
          getPolygon: (cell) => cell.polygon,
          // Read by index, so that a new score only re-evaluates the colours, not the shapes.
          getFillColor: (_cell, { index }) =>
            rings
              ? [
                  colours[index][0],
                  colours[index][1],
                  colours[index][2],
                  Math.min(colours[index][3], 50),
                ]
              : colours[index],
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
        ...(rings
          ? [
              new PolygonLayer<HexCell>({
                id: "hex-rings",
                beforeId: stack.cellsBefore,
                data: cells,
                getPolygon: (cell) => inset(cell.polygon),
                filled: false,
                stroked: true,
                getLineColor: (_cell, { index }) => colours[index],
                updateTriggers: { getLineColor: colours },
                lineWidthUnits: "meters",
                getLineWidth: 30,
                lineWidthMinPixels: 1,
                opacity,
              }),
            ]
          : []),
        new PolygonLayer<HexCell>({
          id: "selected-cell",
          beforeId: stack.labelsBefore,
          data: selected === null ? [] : [cells[selected]],
          getPolygon: (cell) => cell.polygon,
          filled: false,
          stroked: true,
          getLineColor: [20, 20, 20, 255],
          lineWidthMinPixels: 3,
        }),
        new ScatterplotLayer<{ name: string; lat: number; lng: number }>({
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
        }),
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

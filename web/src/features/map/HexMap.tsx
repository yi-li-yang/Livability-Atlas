import { PolygonLayer } from "@deck.gl/layers";
import { MapboxOverlay } from "@deck.gl/mapbox";
import { Map as MapLibreMap, setWorkerUrl } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import { useEffect, useRef } from "react";
import type { Rgba } from "./colour";
import type { HexCell } from "./hexcells";
import { LONDON_BOUNDS, LONDON_CENTRE } from "./london";

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
  opacity,
  selected,
  focus,
  onHover,
  onSelect,
}: {
  cells: HexCell[];
  /** The colour of each cell, in the order of `cells`. */
  colours: Rgba[];
  /** How much of a cell's colour shows over the basemap, from 0 to 1. */
  opacity: number;
  /** The index of the cell the user has clicked, outlined on the map. */
  selected: number | null;
  /** Where to take the map: a new `request` number makes it fly there, as a repeated choice must. */
  focus: { lng: number; lat: number; request: number } | null;
  onHover: (hover: Hover | null) => void;
  /** Called with the cell that was clicked, or null for a click on no cell. */
  onSelect: (index: number | null) => void;
}) {
  const container = useRef<HTMLDivElement>(null);
  const overlay = useRef<MapboxOverlay | null>(null);
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
    const layers = new MapboxOverlay({ interleaved: false, layers: [] });
    basemap.addControl(layers);
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
    overlay.current?.setProps({
      layers: [
        new PolygonLayer<HexCell>({
          id: "hex-cells",
          data: cells,
          getPolygon: (cell) => cell.polygon,
          // Read by index, so that a new score only re-evaluates the colours, not the shapes.
          getFillColor: (_cell, { index }) => colours[index],
          updateTriggers: { getFillColor: colours },
          filled: true,
          stroked: false,
          opacity,
          pickable: true,
          autoHighlight: true,
          highlightColor: [255, 255, 255, 110],
          onHover: ({ index, x, y }) =>
            onHover(index >= 0 ? { index, x, y } : null),
          onClick: ({ index }) => onSelect(index >= 0 ? index : null),
        }),
        new PolygonLayer<HexCell>({
          id: "selected-cell",
          data: selected === null ? [] : [cells[selected]],
          getPolygon: (cell) => cell.polygon,
          filled: false,
          stroked: true,
          getLineColor: [20, 20, 20, 255],
          lineWidthMinPixels: 3,
        }),
      ],
    });
  }, [cells, colours, opacity, selected, onHover, onSelect]);

  return (
    <div
      ref={container}
      data-testid="map"
      data-cells={cells.length}
      className="h-full w-full"
    />
  );
}

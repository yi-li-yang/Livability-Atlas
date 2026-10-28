import { PolygonLayer } from "@deck.gl/layers";
import { MapboxOverlay } from "@deck.gl/mapbox";
import { Map as MapLibreMap, setWorkerUrl } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import { useEffect, useRef } from "react";
import { CELL_OPACITY } from "./colour";
import type { HexCell } from "./hexcells";
import { LONDON_BOUNDS, LONDON_CENTRE } from "./london";

// MapLibre 6 looks for its worker script beside the bundle, where Vite does not
// put it. Importing it with ?url makes Vite emit it, and this points MapLibre there.
setWorkerUrl(workerUrl);

// OpenFreeMap needs no key (docs/tech-stack.md).
const STYLE_URL = "https://tiles.openfreemap.org/styles/liberty";

/** A basemap of London with the hex cells drawn over it, coloured by their score. */
export function HexMap({ cells }: { cells: HexCell[] }) {
  const container = useRef<HTMLDivElement>(null);
  const overlay = useRef<MapboxOverlay | null>(null);

  useEffect(() => {
    if (!container.current) return;
    const map = new MapLibreMap({
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
    map.addControl(layers);
    overlay.current = layers;
    return () => {
      overlay.current = null;
      map.remove();
    };
  }, []);

  useEffect(() => {
    overlay.current?.setProps({
      layers: [
        new PolygonLayer<HexCell>({
          id: "hex-cells",
          data: cells,
          getPolygon: (cell) => cell.polygon,
          getFillColor: (cell) => cell.colour,
          filled: true,
          stroked: false,
          opacity: CELL_OPACITY,
        }),
      ],
    });
  }, [cells]);

  return (
    <div
      ref={container}
      data-testid="map"
      data-cells={cells.length}
      className="h-full w-full"
    />
  );
}

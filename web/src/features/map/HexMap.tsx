import { PolygonLayer, ScatterplotLayer, TextLayer } from "@deck.gl/layers";
import { MapLibreOverlay } from "@deck.gl/maplibre";
import { Map as MapLibreMap, setWorkerUrl } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import { useEffect, useRef, useState } from "react";
import {
  FEW_HOMES_OUTLINE_MAX_PIXELS,
  FEW_HOMES_OUTLINE_METRES,
  type Rgba,
} from "./colour";
import type { HexCell } from "./hexcells";
import { type Inset, insetFor } from "./inset";
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

/**
 * The part of the map that the panels over it leave clear: those marked `data-covers-map` beside
 * the map (the preferences, the legend, the reasons). The camera keeps what it is asked to show
 * inside it, with a small margin.
 */
function clearPart(element: HTMLElement | null): Inset {
  if (!element?.parentElement) return { top: 0, right: 0, bottom: 0, left: 0 };
  const panels = [
    ...element.parentElement.querySelectorAll("[data-covers-map]"),
  ].map((panel) => panel.getBoundingClientRect());
  const { top, right, bottom, left } = insetFor(
    element.getBoundingClientRect(),
    panels,
  );
  const margin = 8;
  return {
    top: top + margin,
    right: right + margin,
    bottom: bottom + margin,
    left: left + margin,
  };
}

/** The middle of a hexagon, as [longitude, latitude]. */
function centreOf(corners: readonly [number, number][]): [number, number] {
  const n = corners.length;
  return [
    corners.reduce((sum, [x]) => sum + x, 0) / n,
    corners.reduce((sum, [, y]) => sum + y, 0) / n,
  ];
}

/** Where the pointer is over a cell, in pixels from the map's top left corner. */
export interface Hover {
  index: number;
  x: number;
  y: number;
}

/**
 * Runs `add` while the map says its style is loaded. deck.gl adds its layers to the map only when
 * `isStyleLoaded()` is true, which MapLibre reports only once every tile has loaded too: on a slow
 * network the cells would wait for the whole basemap, and never come while the map keeps moving.
 * Adding a layer needs only the style itself, which has loaded by the time this is called.
 */
function withStyleLoaded(map: MapLibreMap, add: () => void): void {
  const own = map as unknown as { isStyleLoaded?: () => boolean };
  own.isStyleLoaded = () => true;
  try {
    add();
  } finally {
    delete own.isStyleLoaded;
  }
}

/**
 * A basemap of London with the hex cells drawn inside it, coloured by their score (D23): over the
 * land, under the water, roads and place names, which stay sharp. A cell with few or no homes has
 * no fill, so the land use under it shows. The user sets how solid the cells are.
 *
 * The cells are deck.gl layers interleaved with MapLibre's (`@deck.gl/maplibre`), handed over as
 * soon as the style has loaded (see `withStyleLoaded`).
 */
export function HexMap({
  cells,
  colours,
  outlines,
  opacity,
  selected,
  focus,
  places = [],
  marks = [],
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
  /** The top neighbourhoods' best cells, marked on the map with their places in the list. */
  marks?: readonly { cell: number; place: number }[];
  onHover: (hover: Hover | null) => void;
  /** Called with the cell that was clicked, or null for a click on no cell. */
  onSelect: (index: number | null) => void;
}) {
  const container = useRef<HTMLDivElement>(null);
  const overlay = useRef<MapLibreOverlay | null>(null);
  const [stack, setStack] = useState<Stack | null>(null);
  const map = useRef<MapLibreMap | null>(null);
  // The latest click handler, for the map's own click listener, which is added once.
  const select = useRef(onSelect);
  select.current = onSelect;
  const hover = useRef(onHover);
  hover.current = onHover;
  const fitted = useRef(false);

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
    basemap.once("style.load", () => setStack(restack(basemap)));
    // A click is picked here, not by deck.gl's onClick: interleaved with MapLibre, deck.gl's own
    // click (picked asynchronously from the pointer-down) was lost on the full London bundle, while
    // hovering still worked. pickObject reads the cell under the point at once.
    basemap.on("click", (event) => {
      const picked = layers.pickObject({
        x: event.point.x,
        y: event.point.y,
        layerIds: ["hex-cells"],
      });
      select.current(picked && picked.index >= 0 ? picked.index : null);
    });
    // The quick look describes the cell under the pointer, so it goes when the pointer leaves the
    // map (onto a panel, the legend or off the page) and when the map starts to move under it.
    const element = container.current;
    const leave = () => hover.current(null);
    element.addEventListener("pointerleave", leave);
    basemap.on("movestart", leave);
    overlay.current = layers;
    map.current = basemap;
    return () => {
      element.removeEventListener("pointerleave", leave);
      overlay.current = null;
      map.current = null;
      basemap.remove();
    };
  }, []);

  // The first view: the region's centre in the middle of the part of the map the panels leave
  // clear, not under the panel. It waits for the cells, since the panels come with the data.
  useEffect(() => {
    const basemap = map.current;
    if (!basemap || !stack || cells.length === 0 || fitted.current) return;
    fitted.current = true;
    requestAnimationFrame(() =>
      basemap.jumpTo({
        center: LONDON_CENTRE,
        zoom: basemap.getZoom(),
        padding: clearPart(container.current),
      }),
    );
  });

  useEffect(() => {
    if (focus) {
      map.current?.flyTo({
        center: [focus.lng, focus.lat],
        zoom: 13,
        duration: 900,
        padding: clearPart(container.current),
      });
    }
  }, [focus]);

  // A chosen cell stays in sight: if the reasons (or a sheet) open over it, the map moves it into
  // the clear part. It waits a frame, for the reasons to be drawn and measured.
  useEffect(() => {
    const basemap = map.current;
    if (!basemap || selected === null || !cells[selected]) return;
    const frame = requestAnimationFrame(() => {
      const [lng, lat] = centreOf(cells[selected].polygon);
      const point = basemap.project([lng, lat]);
      const clear = clearPart(container.current);
      const { clientWidth: width, clientHeight: height } =
        basemap.getContainer();
      const inside =
        point.x >= clear.left &&
        point.x <= width - clear.right &&
        point.y >= clear.top &&
        point.y <= height - clear.bottom;
      if (!inside) {
        basemap.easeTo({ center: [lng, lat], padding: clear, duration: 400 });
      }
    });
    return () => cancelAnimationFrame(frame);
  }, [selected, cells]);

  useEffect(() => {
    const basemap = map.current;
    const deck = overlay.current;
    if (!stack || !basemap || !deck) return;
    withStyleLoaded(basemap, () =>
      deck.setProps({
        layers: [
          new PolygonLayer<HexCell, InMap>({
            id: "hex-cells",
            beforeId: stack.cellsBefore,
            data: cells,
            getPolygon: (cell) => cell.polygon,
            // Read by index, so that a new score only re-evaluates the colours, not the shapes.
            getFillColor: (_cell, { index }) => colours[index],
            getLineColor: (_cell, { index }) =>
              outlines?.[index] ?? [0, 0, 0, 0],
            updateTriggers: { getFillColor: colours, getLineColor: outlines },
            filled: true,
            stroked: outlines !== undefined,
            lineWidthUnits: "meters",
            getLineWidth: FEW_HOMES_OUTLINE_METRES,
            lineWidthMaxPixels: FEW_HOMES_OUTLINE_MAX_PIXELS,
            opacity,
            pickable: true,
            autoHighlight: true,
            highlightColor: [255, 255, 255, 110],
            onHover: ({ index, x, y }) =>
              onHover(index >= 0 ? { index, x, y } : null),
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
          new ScatterplotLayer<
            { name: string; lat: number; lng: number },
            InMap
          >({
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
          // The answer on the map: each top neighbourhood's best cell, with its place in the list.
          // These go over the place names, which would otherwise hide them in the centre.
          new ScatterplotLayer<{ cell: number; place: number }, InMap>({
            id: "top-marks",
            data: marks,
            getPosition: ({ cell }) => centreOf(cells[cell].polygon),
            getRadius: 9,
            radiusUnits: "pixels",
            getFillColor: [255, 255, 255, 240],
            getLineColor: [30, 30, 30, 255],
            lineWidthMinPixels: 2,
            stroked: true,
          }),
          new TextLayer<{ cell: number; place: number }, InMap>({
            id: "top-mark-numbers",
            data: marks,
            getPosition: ({ cell }) => centreOf(cells[cell].polygon),
            getText: ({ place }) => String(place),
            getSize: 11,
            sizeUnits: "pixels",
            getColor: [20, 20, 20, 255],
            fontWeight: 700,
            getTextAnchor: "middle",
            getAlignmentBaseline: "center",
            characterSet: "0123456789",
          }),
        ],
      }),
    );
  }, [
    stack,
    cells,
    colours,
    outlines,
    opacity,
    selected,
    places,
    marks,
    onHover,
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

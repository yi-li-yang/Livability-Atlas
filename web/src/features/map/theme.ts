import { useEffect, useState } from "react";
import { EXCLUDED, LAND_COLOURS, type Rgba, WATER } from "./colour";

/**
 * The page's theme. Dark is home (DESIGN.md); light follows the reader's system setting, and
 * `data-theme="dark"` or `"light"` on <html> fixes either, as the visual system's tokens.css does.
 */
export type Scheme = "dark" | "light";

const LIGHT_QUERY = "(prefers-color-scheme: light)";

export function currentScheme(): Scheme {
  if (typeof document === "undefined") return "dark";
  const fixed = document.documentElement.dataset.theme;
  if (fixed === "dark" || fixed === "light") return fixed;
  return window.matchMedia?.(LIGHT_QUERY).matches ? "light" : "dark";
}

/** The theme now, and again whenever the reader's system setting changes. */
export function useScheme(): Scheme {
  const [scheme, setScheme] = useState<Scheme>(currentScheme);
  useEffect(() => {
    const query = window.matchMedia?.(LIGHT_QUERY);
    if (!query) return;
    const change = () => setScheme(currentScheme());
    query.addEventListener("change", change);
    return () => query.removeEventListener("change", change);
  }, []);
  return scheme;
}

/** A colour of the visual system, read from its custom property on the page, as RGBA. */
export function token(name: string, alpha = 255): Rgba {
  const value =
    typeof document === "undefined"
      ? ""
      : getComputedStyle(document.documentElement)
          .getPropertyValue(`--${name}`)
          .trim();
  const hex = /^#([0-9a-f]{6})$/i.exec(value)?.[1];
  if (!hex) return [128, 128, 128, alpha];
  return [
    Number.parseInt(hex.slice(0, 2), 16),
    Number.parseInt(hex.slice(2, 4), 16),
    Number.parseInt(hex.slice(4, 6), 16),
    alpha,
  ];
}

/** The basemap's colours in one theme: what shows in a cell with few or no homes, and around it. */
export interface Basemap {
  land: { green: string; industry: string; railway: string };
  water: string;
  /** A hex cell that a hard limit leaves out. */
  excluded: Rgba;
}

/** The light theme keeps Positron's own pale map, with the land use tints in colour.ts. */
const LIGHT: Basemap = {
  land: LAND_COLOURS,
  water: WATER,
  excluded: EXCLUDED,
};

/**
 * The dark theme: Positron repainted in the stone of the visual system's dark ground, matte, with
 * the land use as faint tints of it (green, violet-grey, brown-grey) so that none passes for a
 * score colour, which are all far lighter and more saturated at the cells' opacity. A cell left out
 * by a hard limit is a mid stone grey: it recedes on the dark ground, as the light grey does on the
 * light one.
 */
const DARK: Basemap = {
  land: { green: "#1f251c", industry: "#221f26", railway: "#24221e" },
  water: "#1a2226",
  excluded: [78, 79, 76, 255],
};

export function basemapFor(scheme: Scheme): Basemap {
  return scheme === "light" ? LIGHT : DARK;
}

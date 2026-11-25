export interface FactorColour {
  /** The factor's own colour, as CSS: the name of the factor reads on it in `ink`. */
  base: string;
  /** The tint that its sub-factors take, as CSS: their names read on it in `tintInk`. */
  tint: string;
  /** The text colour that reads on `base`. */
  ink: string;
  /** The text colour that reads on `tint`. */
  tintInk: string;
}

// The visual system's Earth 8, in its order (DESIGN.md): the colours for seven or eight groups. A
// level of the factor tree shows at most a handful of factors, and each box and row also carries
// the factor's name, so a colour that comes round again never stands alone.
const EARTH_8 = [
  "glacier",
  "rust",
  "spruce",
  "sand",
  "dusk",
  "rose",
  "olive",
  "sky",
] as const;

/**
 * A factor's colours from a data colour of the system. They follow the theme: index.css mixes the
 * data colour towards a ground that keeps the name at WCAG AA in the dark and the light theme.
 */
function fromData(name: (typeof EARTH_8)[number]): FactorColour {
  const data = `var(--data-${name})`;
  return {
    base: `color-mix(in srgb, ${data} var(--factor-share), var(--factor-towards))`,
    tint: `color-mix(in srgb, ${data} var(--factor-tint-share), var(--factor-tint-towards))`,
    ink: "var(--factor-on)",
    tintInk: "var(--ink)",
  };
}

// The catalogue's top-level factors in its order, so that a factor keeps its colour whatever
// subset of the factors a bundle holds.
const ORDER = [
  "housing-and-cost",
  "transport",
  "daily-amenities",
  "environment",
  "climate",
  "natural-hazards",
  "safety",
  "health-care",
  "education",
  "community-and-people",
  "culture-and-leisure",
  "animal-friendliness",
  "work-and-economy",
  "digital-connectivity",
  "urban-form-and-change",
  "governance-and-rights",
  "published-rankings",
  "resident-wellbeing",
];

/** The colour of a top-level factor. One that the catalogue does not list takes the next free one. */
export function factorColour(id: string, position = 0): FactorColour {
  const index = ORDER.indexOf(id);
  return fromData(
    EARTH_8[(index >= 0 ? index : ORDER.length + position) % EARTH_8.length],
  );
}

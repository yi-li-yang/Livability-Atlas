export interface FactorColour {
  /** The factor's own colour: it carries white text at a contrast of 4.5:1 or more. */
  base: string;
  /** The tint that its sub-factors take: it carries dark text. */
  tint: string;
}

// The categorical palette of the Salt design system (J.P. Morgan, Apache-2.0), as the factor
// explorer uses it: step 500 for a factor, step 200 for its sub-factors.
const SALT: FactorColour[] = [
  { base: "#4676bf", tint: "#c6d3ef" }, // cobalt
  { base: "#ab6528", tint: "#ffc99e" }, // cider
  { base: "#9f55c2", tint: "#e6b9fa" }, // plum
  { base: "#2a8285", tint: "#b1e5e5" }, // aqua
  { base: "#b0549d", tint: "#fabeed" }, // rose
  { base: "#6d7c4d", tint: "#d2deb8" }, // olive
  { base: "#bd5558", tint: "#ffc2c2" }, // salmon
  { base: "#7665cf", tint: "#d0c2fc" }, // indigo
  { base: "#2d8543", tint: "#b3e5bb" }, // jade
  { base: "#877410", tint: "#f0e1a5" }, // citrine
  { base: "#bd5a13", tint: "#ffc5a1" }, // autumn
  { base: "#946694", tint: "#edc7ed" }, // lavender
  { base: "#008094", tint: "#b4e5f0" }, // ocean
  { base: "#c24795", tint: "#ffbfe5" }, // fuchsia
  { base: "#667d15", tint: "#d7e3a8" }, // lime
  { base: "#996a45", tint: "#f5d6bf" }, // fur
  { base: "#636ebf", tint: "#cacbfc" }, // violet
  { base: "#23855e", tint: "#bce8d3" }, // forest
];

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
  return SALT[(index >= 0 ? index : ORDER.length + position) % SALT.length];
}

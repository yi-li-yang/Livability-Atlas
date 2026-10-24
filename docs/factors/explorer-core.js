// Factor explorer logic, without any drawing. It checks the factor catalogue,
// fills in inherited scales, and computes each factor's share of total weight
// (docs/methodology/scoring.md, section 5). explorer.html loads it as a
// classic script, and the tests load it with require().
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.ExplorerCore = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const ROOT_ID = "root";
  const SCALES = ["within-city", "across-cities"];
  const STATUSES = ["idea", "researched", "spiked", "built"];
  // Until default weights are set from evidence (D14), 3 is the placeholder,
  // and any other default weight must give its reason.
  const PLACEHOLDER_WEIGHT = 3;
  const ID_PATTERN = /^[a-z0-9]+(-[a-z0-9]+)*$/;

  // The fields research adds to a measured indicator (catalogue/README.md),
  // and the values they allow.
  const INDICATOR_FIELDS = ["unit", "preference_type", "curve", "curve_reason", "evidence_type",
    "comparable_across_regions", "method", "datasets"];
  const FACTOR_FIELDS = ["id", "name", "description", "default_weight", "weight_reason", "scales", "status",
    "children", ...INDICATOR_FIELDS];
  const PREFERENCE_TYPES = ["fixed", "user-direction", "user-range", "user-choice"];
  const EVIDENCE_TYPES = ["direct", "estimate", "indirect", "perception", "ranking"];
  const CURVE_SHAPES = ["ramp", "ideal-range", "lookup", "percentile"];
  // The fields each research status requires of a measured indicator, beyond
  // a name and a default weight.
  const RESEARCHED = ["unit", "preference_type", "evidence_type", "comparable_across_regions", "method",
    "datasets", "curve_reason"];
  const REQUIRED_BY_STATUS = {
    idea: [],
    researched: RESEARCHED,
    spiked: [...RESEARCHED, "curve"],
    built: [...RESEARCHED, "curve"],
  };

  const isMapping = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
  const isText = (value) => typeof value === "string" && value.trim() !== "";
  const isNumber = (value) => typeof value === "number" && Number.isFinite(value);

  // Returns a list of problems, each naming the factor it concerns.
  // An empty list means that the catalogue can be drawn. `datasetsDoc` is
  // the parsed datasets.yaml, against which dataset ids are checked.
  function validateCatalogue(catalogue, datasetsDoc = { datasets: [] }) {
    if (!catalogue || !Array.isArray(catalogue.factors) || catalogue.factors.length === 0) {
      return ["The catalogue needs a non-empty list under factors."];
    }
    const problems = [];
    const seen = new Set();
    const known = new Map();
    for (const dataset of isMapping(datasetsDoc) && Array.isArray(datasetsDoc.datasets) ? datasetsDoc.datasets : []) {
      if (isMapping(dataset) && typeof dataset.id === "string") known.set(dataset.id, dataset);
    }

    function checkCurve(curve, label) {
      if (!isMapping(curve)) {
        problems.push(`${label}: curve must be a mapping with a shape, such as {shape: ramp, t0: 25, t1: 5}.`);
        return;
      }
      if (curve.shape === "ramp") {
        if (!isNumber(curve.t0) || !isNumber(curve.t1) || curve.t0 === curve.t1) {
          problems.push(`${label}: a ramp needs two different numbers, t0 and t1.`);
        }
      } else if (curve.shape === "ideal-range") {
        const { l0, l1, u1, u0 } = curve;
        if (![l0, l1, u1, u0].every(isNumber) || !(l0 < l1 && l1 <= u1 && u1 < u0)) {
          problems.push(`${label}: an ideal-range curve needs numbers with l0 < l1 ≤ u1 < u0.`);
        }
      } else if (curve.shape === "lookup") {
        const scores = curve.scores;
        const valid = isMapping(scores) && Object.keys(scores).length > 0
          && Object.values(scores).every((score) => isNumber(score) && score >= 0 && score <= 1);
        if (!valid) problems.push(`${label}: a lookup curve needs scores, with a score from 0 to 1 for each category.`);
      } else if (curve.shape === "percentile") {
        if (curve.better !== "higher" && curve.better !== "lower") {
          problems.push(`${label}: a percentile curve needs better: higher or lower.`);
        }
      } else {
        problems.push(`${label}: curve.shape must be one of ${CURVE_SHAPES.join(", ")}.`);
      }
    }

    // The fields of a measured indicator: each one present is checked, and
    // its research status decides which must be present.
    function checkIndicator(node, label) {
      for (const field of ["unit", "curve_reason", "method"]) {
        if (node[field] !== undefined && !isText(node[field])) problems.push(`${label}: ${field} must be non-empty text.`);
      }
      if (node.preference_type !== undefined && !PREFERENCE_TYPES.includes(node.preference_type)) {
        problems.push(`${label}: preference_type must be one of ${PREFERENCE_TYPES.join(", ")}.`);
      }
      if (node.evidence_type !== undefined && !EVIDENCE_TYPES.includes(node.evidence_type)) {
        problems.push(`${label}: evidence_type must be one of ${EVIDENCE_TYPES.join(", ")}.`);
      }
      if (node.comparable_across_regions !== undefined && typeof node.comparable_across_regions !== "boolean") {
        problems.push(`${label}: comparable_across_regions must be true or false.`);
      }
      if (node.curve !== undefined) {
        checkCurve(node.curve, label);
        if (node.curve_reason === undefined) problems.push(`${label}: a curve needs a curve_reason.`);
        if (node.preference_type === "user-range" && isMapping(node.curve) && node.curve.shape !== "ideal-range") {
          problems.push(`${label}: a user-range measured indicator needs an ideal-range curve, because its user drags a band.`);
        }
      }
      if (node.datasets !== undefined) {
        if (!Array.isArray(node.datasets) || node.datasets.length === 0 || !node.datasets.every(isText)) {
          problems.push(`${label}: datasets must be a non-empty list of dataset ids.`);
        } else {
          node.datasets.forEach((id, i) => {
            if (node.datasets.indexOf(id) !== i) {
              problems.push(`${label}: dataset ${id} is listed twice.`);
            } else if (!known.has(id)) {
              problems.push(`${label}: datasets.yaml has no dataset ${id}.`);
            } else if (node.evidence_type === "ranking" && known.get(id).credibility === undefined) {
              problems.push(`${label}: evidence type ranking needs a credibility rating on dataset ${id}.`);
            }
          });
        }
      }
      const required = REQUIRED_BY_STATUS[node.status || "idea"] || [];
      const missing = required.filter((field) => node[field] === undefined);
      if (missing.length > 0) problems.push(`${label}: at status ${node.status}, it needs ${missing.join(", ")}.`);
    }

    function check(node, parentScales, where) {
      if (node === null || typeof node !== "object" || Array.isArray(node)) {
        problems.push(`${where}: each factor must be a mapping of fields.`);
        return;
      }
      const label = typeof node.id === "string" ? node.id : where;
      for (const field of Object.keys(node)) {
        if (!FACTOR_FIELDS.includes(field)) problems.push(`${label}: unknown field ${field}.`);
      }
      if (typeof node.id !== "string" || !ID_PATTERN.test(node.id)) {
        problems.push(`${label}: id must be kebab-case, such as air-quality.`);
      } else if (seen.has(node.id)) {
        problems.push(`${label}: this id is used more than once.`);
      } else {
        seen.add(node.id);
      }
      if (typeof node.name !== "string" || node.name.trim() === "") {
        problems.push(`${label}: name is missing.`);
      }
      const weight = node.default_weight;
      if (!Number.isInteger(weight) || weight < 0 || weight > 5) {
        problems.push(`${label}: default_weight must be a whole number from 0 to 5.`);
      } else if (weight !== PLACEHOLDER_WEIGHT && !(typeof node.weight_reason === "string" && node.weight_reason.trim())) {
        problems.push(`${label}: a default_weight other than ${PLACEHOLDER_WEIGHT} needs a weight_reason.`);
      }
      if (node.status !== undefined && !STATUSES.includes(node.status)) {
        problems.push(`${label}: status must be one of ${STATUSES.join(", ")}.`);
      }
      let scales = parentScales || SCALES;
      if (node.scales === undefined) {
        if (parentScales === null) problems.push(`${label}: a top-level factor must list its scales.`);
      } else if (!Array.isArray(node.scales) || node.scales.length === 0 || node.scales.some((s) => !SCALES.includes(s))) {
        problems.push(`${label}: scales must list ${SCALES.join(", ")}, or both.`);
      } else if (parentScales !== null && node.scales.some((s) => !parentScales.includes(s))) {
        problems.push(`${label}: it lists a scale that its parent does not have.`);
      } else {
        scales = node.scales;
      }
      if (node.children === undefined) {
        checkIndicator(node, label);
        return;
      }
      const indicatorFields = INDICATOR_FIELDS.filter((field) => node[field] !== undefined);
      if (indicatorFields.length > 0) {
        problems.push(`${label}: a factor with sub-factors is not a measured indicator, so it cannot have ${indicatorFields.join(", ")}.`);
      }
      if (node.status !== undefined) {
        problems.push(`${label}: a factor with sub-factors takes its research status from them, so it has none of its own.`);
      }
      if (!Array.isArray(node.children) || node.children.length === 0) {
        problems.push(`${label}: children must be a non-empty list.`);
      } else {
        node.children.forEach((child, i) => check(child, scales, `${label}, child ${i + 1}`));
      }
    }

    catalogue.factors.forEach((factor, i) => check(factor, null, `factor ${i + 1}`));
    return problems;
  }

  // Returns the catalogue as a tree with every field filled in: inherited
  // scales, the default status, each factor's position among its siblings in
  // the catalogue (index), and a root above the top-level factors.
  function normaliseCatalogue(catalogue) {
    function copy(node, parentScales, index) {
      const scales = node.scales || parentScales;
      return {
        id: node.id,
        name: node.name,
        description: node.description || "",
        defaultWeight: node.default_weight,
        weightReason: node.weight_reason || "",
        scales,
        status: node.status || "idea",
        index,
        children: (node.children || []).map((child, i) => copy(child, scales, i)),
      };
    }
    return {
      id: ROOT_ID,
      name: "All factors",
      description: "",
      defaultWeight: 1,
      weightReason: "",
      scales: SCALES.slice(),
      status: "idea",
      index: 0,
      children: catalogue.factors.map((factor, i) => copy(factor, SCALES, i)),
    };
  }

  // Returns the tree for one scale, with the user's weights applied.
  // `weights` maps a factor's id to the weight the user set; every other
  // factor keeps its default. Each node of the result holds:
  //   weight        the weight in use
  //   countsAsZero  true when the weight is 0, or every sub-factor counts as 0
  //   share         its share of total weight, 0 when it counts as 0
  //   counted, notCounted  its sub-factors at this scale, split by whether they count
  //   parentId      its parent's id, or null for the root
  //   index         its position among its siblings in the catalogue, so that
  //                 anything keyed to it, such as colour, does not shift when
  //                 the scale or the weights hide a sibling
  // byId maps each id to its node.
  function buildTree(root, scale, weights) {
    const byId = new Map();

    function build(node, parentId) {
      const subFactors = node.children
        .filter((child) => child.scales.includes(scale))
        .map((child) => build(child, node.id));
      const weight = node.id === ROOT_ID ? 1 : weights[node.id] !== undefined ? weights[node.id] : node.defaultWeight;
      const counted = subFactors.filter((s) => !s.countsAsZero);
      const view = {
        id: node.id,
        name: node.name,
        description: node.description,
        weightReason: node.weightReason,
        status: node.status,
        scales: node.scales,
        index: node.index,
        defaultWeight: node.defaultWeight,
        weight,
        countsAsZero: weight === 0 || (subFactors.length > 0 && counted.length === 0),
        share: 0,
        counted,
        notCounted: subFactors.filter((s) => s.countsAsZero),
        parentId,
      };
      byId.set(node.id, view);
      return view;
    }

    function assignShares(view, share) {
      view.share = share;
      const total = view.counted.reduce((sum, s) => sum + s.weight, 0);
      view.counted.forEach((s) => assignShares(s, (share * s.weight) / total));
    }

    const top = build(root, null);
    assignShares(top, top.countsAsZero ? 0 : 1);
    return { root: top, byId };
  }

  // Returns the ids from the root down to the factor with this id,
  // or an empty list when no factor has it.
  function pathTo(root, id) {
    if (root.id === id) return [root.id];
    for (const child of root.children) {
      const path = pathTo(child, id);
      if (path.length > 0) return [root.id, ...path];
    }
    return [];
  }

  return { ROOT_ID, SCALES, STATUSES, PLACEHOLDER_WEIGHT, validateCatalogue, normaliseCatalogue, buildTree, pathTo };
});

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

  // Returns a list of problems, each naming the factor it concerns.
  // An empty list means that the catalogue can be drawn.
  function validateCatalogue(catalogue) {
    if (!catalogue || !Array.isArray(catalogue.factors) || catalogue.factors.length === 0) {
      return ["The catalogue needs a non-empty list under factors."];
    }
    const problems = [];
    const seen = new Set();

    function check(node, parentScales, where) {
      if (node === null || typeof node !== "object" || Array.isArray(node)) {
        problems.push(`${where}: each factor must be a mapping of fields.`);
        return;
      }
      const label = typeof node.id === "string" ? node.id : where;
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
      if (node.children !== undefined) {
        if (!Array.isArray(node.children) || node.children.length === 0) {
          problems.push(`${label}: children must be a non-empty list.`);
        } else {
          node.children.forEach((child, i) => check(child, scales, `${label}, child ${i + 1}`));
        }
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

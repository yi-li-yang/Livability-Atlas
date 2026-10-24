// Factor explorer logic, without any drawing: it checks the factor catalogue.
// explorer.html loads it as a classic script, and the tests load it with require().
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.ExplorerCore = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

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

  return { SCALES, STATUSES, PLACEHOLDER_WEIGHT, validateCatalogue };
});

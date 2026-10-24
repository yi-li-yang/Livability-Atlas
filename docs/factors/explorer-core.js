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

  // The fields of a dataset in datasets.yaml, and the values they allow.
  const DATASET_FIELDS = ["id", "name", "publisher", "url", "tier", "area", "resolution", "date", "licence",
    "licence_checked", "public_build", "licence_note", "attribution", "tells", "credibility", "credibility_reason"];
  const TIERS = ["city", "country", "global"];
  const CREDIBILITY = ["high", "medium", "low"];
  // Licences that allow redistribution and commercial use, by SPDX id (D07).
  // Only datasets under one of them may go into public builds. A licence that
  // SPDX does not list takes a LicenseRef- id: TfL's open data licence is
  // version 2.0 of the Open Government Licence with TfL's amendments.
  const OPEN_LICENCES = ["OGL-UK-1.0", "OGL-UK-2.0", "OGL-UK-3.0", "CC-BY-3.0", "CC-BY-4.0", "CC-BY-SA-3.0",
    "CC-BY-SA-4.0", "CC0-1.0", "ODbL-1.0", "CDLA-Permissive-1.0", "CDLA-Permissive-2.0", "Apache-2.0",
    "LicenseRef-TfL-Open-Data"];

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
      // An unknown status is reported above, and requires nothing here.
      const status = node.status || "idea";
      const required = STATUSES.includes(status) ? REQUIRED_BY_STATUS[status] : [];
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

  // A date as YAML gives it, as YYYY-MM-DD: an unquoted 2026-10-24 arrives
  // as a Date, a quoted one as text. Returns null for anything else.
  function isoDate(value) {
    if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value.toISOString().slice(0, 10);
    if (typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(value))) return value;
    return null;
  }

  // Returns a list of problems in datasets.yaml, each naming the dataset it
  // concerns. It enforces D07: only openly licensed datasets, with their
  // licence checked, may go into public builds.
  function validateDatasets(datasetsDoc) {
    if (!isMapping(datasetsDoc) || !Array.isArray(datasetsDoc.datasets)) {
      return ["datasets.yaml needs a list under datasets."];
    }
    const problems = [];
    const seen = new Set();
    datasetsDoc.datasets.forEach((dataset, i) => {
      if (!isMapping(dataset)) {
        problems.push(`dataset ${i + 1}: each dataset must be a mapping of fields.`);
        return;
      }
      const label = `dataset ${typeof dataset.id === "string" ? dataset.id : i + 1}`;
      const problem = (message) => problems.push(`${label}: ${message}`);
      for (const field of Object.keys(dataset)) {
        if (!DATASET_FIELDS.includes(field)) problem(`unknown field ${field}.`);
      }
      if (typeof dataset.id !== "string" || !ID_PATTERN.test(dataset.id)) {
        problem("id must be kebab-case, such as laei.");
      } else if (seen.has(dataset.id)) {
        problem("this id is used more than once.");
      } else {
        seen.add(dataset.id);
      }
      for (const field of ["name", "publisher", "area", "resolution", "licence"]) {
        if (dataset[field] === undefined) problem(`${field} is missing.`);
        else if (!isText(dataset[field])) problem(`${field} must be non-empty text.`);
      }
      for (const field of ["licence_note", "attribution", "credibility_reason"]) {
        if (dataset[field] !== undefined && !isText(dataset[field])) problem(`${field} must be non-empty text.`);
      }
      if (dataset.url === undefined) problem("url is missing.");
      else if (typeof dataset.url !== "string" || !/^https?:\/\/\S+$/.test(dataset.url)) problem("url must start with http:// or https://.");
      if (dataset.tier === undefined) problem("tier is missing.");
      else if (!TIERS.includes(dataset.tier)) problem(`tier must be one of ${TIERS.join(", ")}.`);
      if (dataset.date === undefined) problem("date is missing.");
      else if (!isText(dataset.date) && !Number.isInteger(dataset.date)) problem("date must be text or a year, such as 2022.");
      if (dataset.tells === undefined) problem("tells is missing.");
      else if (!Array.isArray(dataset.tells) || dataset.tells.length === 0 || !dataset.tells.every(isText)) problem("tells must be a non-empty list of text.");
      if (dataset.licence_checked !== undefined && isoDate(dataset.licence_checked) === null) {
        problem("licence_checked must be a date, such as 2026-10-24.");
      }
      if (dataset.public_build === undefined) {
        problem("public_build is missing.");
      } else if (typeof dataset.public_build !== "boolean") {
        problem("public_build must be true or false.");
      } else if (dataset.public_build) {
        if (isText(dataset.licence) && !OPEN_LICENCES.includes(dataset.licence)) {
          problem(`public_build is true, but ${dataset.licence} is not on D07's list of open licences: ${OPEN_LICENCES.join(", ")}.`);
        }
        if (dataset.licence_checked === undefined) problem("public_build is true, so it needs licence_checked, the date its licence was checked at the source.");
        if (dataset.attribution === undefined) problem("public_build is true, so it needs an attribution.");
      } else if (dataset.licence_note === undefined) {
        problem("public_build is false, so it needs a licence_note saying why.");
      }
      if (dataset.credibility !== undefined) {
        if (!CREDIBILITY.includes(dataset.credibility)) problem(`credibility must be one of ${CREDIBILITY.join(", ")}.`);
        if (dataset.credibility_reason === undefined) problem("credibility needs a credibility_reason.");
      }
    });
    return problems;
  }

  // Returns the catalogue as a tree with every field filled in: inherited
  // scales, the default status, each factor's position among its siblings in
  // the catalogue (index), a measured indicator's research, and a root above
  // the top-level factors.
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
        unit: node.unit || "",
        preferenceType: node.preference_type || "",
        curve: node.curve || null,
        curveReason: node.curve_reason || "",
        evidenceType: node.evidence_type || "",
        comparableAcrossRegions: typeof node.comparable_across_regions === "boolean" ? node.comparable_across_regions : null,
        method: node.method || "",
        datasets: node.datasets || [],
        children: (node.children || []).map((child, i) => copy(child, scales, i)),
      };
    }
    // The root goes through the same copy, so that it has every field too.
    return copy({ id: ROOT_ID, name: "All factors", default_weight: 1, children: catalogue.factors }, SCALES.slice(), 0);
  }

  // Returns the tree for one scale, with the user's weights applied.
  // `weights` maps a factor's id to the weight the user set; every other
  // factor keeps its default. Each node of the result holds the normalised
  // factor's fields, and:
  //   weight        the weight in use
  //   countsAsZero  true when the weight is 0, or every sub-factor counts as 0
  //   share         its share of total weight, 0 when it counts as 0
  //   counted, notCounted  its sub-factors at this scale, split by whether they count
  //   parentId      its parent's id, or null for the root
  //   progress      how many of the measured indicators at or below it, at
  //                 this scale, are researched or further, out of how many
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
      // At this scale, a factor without sub-factors is a measured indicator.
      const progress = subFactors.length === 0
        ? { researched: node.status === "idea" ? 0 : 1, total: 1 }
        : subFactors.reduce((sum, s) => ({
          researched: sum.researched + s.progress.researched,
          total: sum.total + s.progress.total,
        }), { researched: 0, total: 0 });
      const { children, ...fields } = node;
      const view = {
        ...fields,
        weight,
        countsAsZero: weight === 0 || (subFactors.length > 0 && counted.length === 0),
        share: 0,
        counted,
        notCounted: subFactors.filter((s) => s.countsAsZero),
        parentId,
        progress,
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

  // Returns the datasets of datasets.yaml as a map by id, with every field
  // filled in and both dates as text.
  function normaliseDatasets(datasetsDoc) {
    const byId = new Map();
    for (const dataset of isMapping(datasetsDoc) && Array.isArray(datasetsDoc.datasets) ? datasetsDoc.datasets : []) {
      byId.set(dataset.id, {
        id: dataset.id,
        name: dataset.name,
        publisher: dataset.publisher,
        url: dataset.url,
        tier: dataset.tier,
        area: dataset.area,
        resolution: dataset.resolution,
        date: String(dataset.date),
        licence: dataset.licence,
        licenceChecked: isoDate(dataset.licence_checked) || "",
        publicBuild: dataset.public_build === true,
        licenceNote: dataset.licence_note || "",
        attribution: dataset.attribution || "",
        tells: dataset.tells || [],
        credibility: dataset.credibility || "",
        credibilityReason: dataset.credibility_reason || "",
      });
    }
    return byId;
  }

  const number = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 6 });

  // Puts a scoring curve into words, with its thresholds in the measured
  // indicator's unit, e.g. "1 at 10 µg/m³ or less, falling to 0 at 40 µg/m³
  // or more". Scores run from 0 (worst) to 1 (best), as in scoring.md.
  function describeCurve(curve, unit) {
    const value = (x) => {
      const text = number.format(x);
      if (!unit) return text;
      return unit === "%" ? `${text}%` : `${text} ${unit}`;
    };
    switch (curve.shape) {
      case "ramp":
        return curve.t1 < curve.t0
          ? `1 at ${value(curve.t1)} or less, falling to 0 at ${value(curve.t0)} or more`
          : `0 at ${value(curve.t0)} or less, rising to 1 at ${value(curve.t1)} or more`;
      case "ideal-range": {
        const best = curve.l1 === curve.u1
          ? `1 at ${value(curve.l1)}`
          : `1 from ${number.format(curve.l1)} to ${value(curve.u1)}`;
        return `${best}, falling to 0 at ${value(curve.l0)} or less and at ${value(curve.u0)} or more`;
      }
      case "lookup": {
        // Best first. The keys' own order cannot be trusted, because
        // JavaScript puts keys that look like whole numbers first.
        const best = Object.entries(curve.scores).sort(([, a], [, b]) => b - a);
        return `by category: ${best.map(([category, score]) => `${category} ${number.format(score)}`).join(", ")}`;
      }
      case "percentile":
        return `by rank within the region, where ${curve.better} values score better`;
      default:
        return "";
    }
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

  return {
    ROOT_ID, SCALES, STATUSES, PLACEHOLDER_WEIGHT, OPEN_LICENCES,
    validateCatalogue, validateDatasets, normaliseCatalogue, normaliseDatasets, buildTree, describeCurve, pathTo,
  };
});

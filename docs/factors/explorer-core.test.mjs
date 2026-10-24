// Tests for explorer-core.js. Run: node --test "docs/factors/*.test.mjs"
import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const core = require("./explorer-core.js");

// The worked example in docs/methodology/scoring.md, section 8.
function example() {
  return {
    factors: [
      { id: "housing", name: "Housing and cost", default_weight: 4, weight_reason: "Example.", scales: ["within-city"] },
      { id: "transport", name: "Transport", default_weight: 4, weight_reason: "Example.", scales: ["within-city"] },
      {
        id: "environment",
        name: "Environment",
        default_weight: 2,
        weight_reason: "Example.",
        scales: ["within-city"],
        children: [
          {
            id: "air-quality",
            name: "Air quality",
            default_weight: 3,
            children: [
              { id: "no2", name: "NO₂", default_weight: 2, weight_reason: "Example." },
              { id: "pm25", name: "PM2.5", default_weight: 2, weight_reason: "Example." },
            ],
          },
          { id: "noise", name: "Noise", default_weight: 3 },
          { id: "green-space", name: "Green space", default_weight: 0, weight_reason: "Example." },
        ],
      },
    ],
  };
}

test("the worked example passes every check", () => {
  assert.deepEqual(core.validateCatalogue(example()), []);
});

test("an empty catalogue is rejected", () => {
  assert.deepEqual(core.validateCatalogue({}), ["The catalogue needs a non-empty list under factors."]);
});

test("each check names its problem and the factor it concerns", () => {
  const cases = [
    [(c) => { c.factors[1].id = "housing"; }, /^housing: this id is used more than once/],
    [(c) => { c.factors[0].id = "Housing_Cost"; }, /id must be kebab-case/],
    [(c) => { delete c.factors[0].name; }, /^housing: name is missing/],
    [(c) => { c.factors[0].default_weight = 7; }, /^housing: default_weight must be a whole number from 0 to 5/],
    [(c) => { c.factors[0].default_weight = 2.5; }, /default_weight must be a whole number/],
    [(c) => { delete c.factors[0].weight_reason; }, /^housing: a default_weight other than 3 needs a weight_reason/],
    [(c) => { c.factors[0].scales = ["regional"]; }, /^housing: scales must list/],
    [(c) => { delete c.factors[0].scales; }, /^housing: a top-level factor must list its scales/],
    [(c) => { c.factors[2].children[1].scales = ["across-cities"]; }, /^noise: it lists a scale that its parent does not have/],
    [(c) => { c.factors[2].children[1].status = "done"; }, /^noise: status must be one of idea, researched, spiked, built/],
    [(c) => { c.factors[2].children[1].children = []; }, /^noise: children must be a non-empty list/],
  ];
  for (const [change, expected] of cases) {
    const catalogue = example();
    change(catalogue);
    const problems = core.validateCatalogue(catalogue);
    assert.ok(problems.some((p) => expected.test(p)), `expected ${expected}, got ${JSON.stringify(problems)}`);
  }
});

function treeOf(catalogue, weights = {}, scale = "within-city") {
  return core.buildTree(core.normaliseCatalogue(catalogue), scale, weights);
}
function close(actual, expected) {
  assert.ok(Math.abs(actual - expected) < 1e-9, `${actual} is not ${expected}`);
}
const ids = (views) => views.map((v) => v.id);

test("shares of total weight match the worked example in scoring.md", () => {
  const { byId } = treeOf(example());
  close(byId.get("housing").share, 0.4);
  close(byId.get("transport").share, 0.4);
  close(byId.get("environment").share, 0.2);
  close(byId.get("air-quality").share, 0.1);
  close(byId.get("noise").share, 0.1);
  close(byId.get("no2").share, 0.05);
  close(byId.get("pm25").share, 0.05);
});

test("a factor that starts at weight 0 is listed as not counted", () => {
  const { byId } = treeOf(example());
  assert.deepEqual(ids(byId.get("environment").notCounted), ["green-space"]);
  assert.equal(byId.get("green-space").share, 0);
});

test("setting a weight to 0 removes the factor, and its siblings share its part", () => {
  const { byId } = treeOf(example(), { transport: 0 });
  assert.deepEqual(ids(byId.get("root").notCounted), ["transport"]);
  close(byId.get("housing").share, 4 / 6);
  close(byId.get("environment").share, 2 / 6);
  assert.equal(byId.get("transport").share, 0);
});

test("a factor whose sub-factors all have weight 0 counts as weight 0", () => {
  const { byId } = treeOf(example(), { no2: 0, pm25: 0 });
  assert.equal(byId.get("air-quality").countsAsZero, true);
  assert.equal(byId.get("air-quality").share, 0);
  assert.deepEqual(ids(byId.get("environment").notCounted), ["air-quality", "green-space"]);
  close(byId.get("noise").share, 0.2);
});

test("the scale filter keeps the factors for that scale, and sub-factors inherit scales", () => {
  const root = core.normaliseCatalogue({
    factors: [
      { id: "climate", name: "Climate", default_weight: 3, scales: ["across-cities"] },
      {
        id: "environment",
        name: "Environment",
        default_weight: 3,
        scales: ["within-city", "across-cities"],
        children: [
          { id: "noise", name: "Noise", default_weight: 3, scales: ["within-city"] },
          { id: "air-quality", name: "Air quality", default_weight: 3 },
        ],
      },
    ],
  });
  const within = core.buildTree(root, "within-city", {});
  const across = core.buildTree(root, "across-cities", {});
  assert.deepEqual(ids(within.root.counted), ["environment"]);
  assert.deepEqual(ids(across.root.counted), ["climate", "environment"]);
  assert.deepEqual(ids(within.byId.get("environment").counted), ["noise", "air-quality"]);
  assert.deepEqual(ids(across.byId.get("environment").counted), ["air-quality"]);
});

test("pathTo lists the ids from the root down to a factor", () => {
  const root = core.normaliseCatalogue(example());
  assert.deepEqual(core.pathTo(root, "no2"), ["root", "environment", "air-quality", "no2"]);
  assert.deepEqual(core.pathTo(root, "missing"), []);
});

test("each factor keeps its catalogue position among its siblings, whatever the scale", () => {
  const root = core.normaliseCatalogue({
    factors: [
      { id: "housing", name: "Housing", default_weight: 3, scales: ["within-city", "across-cities"] },
      { id: "climate", name: "Climate", default_weight: 3, scales: ["across-cities"] },
      {
        id: "environment",
        name: "Environment",
        default_weight: 3,
        scales: ["within-city", "across-cities"],
        children: [
          { id: "noise", name: "Noise", default_weight: 3, scales: ["within-city"] },
          { id: "air-quality", name: "Air quality", default_weight: 3 },
        ],
      },
    ],
  });
  const within = core.buildTree(root, "within-city", {});
  const across = core.buildTree(root, "across-cities", {});
  assert.equal(within.byId.get("environment").index, 2);
  assert.equal(across.byId.get("environment").index, 2);
  assert.equal(across.byId.get("climate").index, 1);
  assert.equal(within.byId.get("air-quality").index, 1);
  assert.equal(across.byId.get("air-quality").index, 1);
});

// Measured indicators: the fields that research adds (catalogue format spec).

// A measured indicator with every field that the status researched requires.
function researched(fields = {}) {
  return {
    id: "pm25",
    name: "PM2.5, annual mean",
    default_weight: 3,
    status: "researched",
    unit: "µg/m³",
    preference_type: "fixed",
    curve: { shape: "ramp", t0: 25, t1: 5 },
    curve_reason: "The WHO's 2021 guideline and its second interim target.",
    evidence_type: "estimate",
    comparable_across_regions: true,
    method: "The area-weighted mean of the modelled annual mean over the hex cell.",
    datasets: ["laei"],
    ...fields,
  };
}

function without(record, field) {
  const copy = { ...record };
  delete copy[field];
  return copy;
}

// A catalogue whose only measured indicator sits under Environment.
function catalogueWith(indicator) {
  return { factors: [{ id: "environment", name: "Environment", default_weight: 3, scales: ["within-city"], children: [indicator] }] };
}

// datasets.yaml with one valid dataset.
function datasetsDoc(fields = {}) {
  return {
    datasets: [{
      id: "laei",
      name: "London Atmospheric Emissions Inventory (LAEI)",
      publisher: "Greater London Authority and Transport for London",
      url: "https://data.london.gov.uk/dataset/london-atmospheric-emissions-inventory--laei--2022",
      tier: "city",
      area: "Greater London",
      resolution: "20 m grid",
      date: "2022",
      licence: "unknown",
      public_build: false,
      licence_note: "The publisher names no licence.",
      tells: ["Modelled annual mean concentrations of NO₂ and PM2.5"],
      ...fields,
    }],
  };
}

function problemsOf(indicator, datasets = datasetsDoc()) {
  return core.validateCatalogue(catalogueWith(indicator), datasets);
}

function expectProblem(problems, pattern) {
  assert.ok(problems.some((p) => pattern.test(p)), `expected ${pattern}, got ${JSON.stringify(problems)}`);
}

test("the worked example passes every check when datasets are given too", () => {
  assert.deepEqual(core.validateCatalogue(example(), datasetsDoc()), []);
});

test("a researched measured indicator with every required field passes", () => {
  assert.deepEqual(problemsOf(researched()), []);
});

test("a researched measured indicator needs each field its status requires", () => {
  const fields = ["unit", "preference_type", "evidence_type", "comparable_across_regions", "method", "datasets", "curve_reason"];
  for (const field of fields) {
    expectProblem(problemsOf(without(researched(), field)), new RegExp(`^pm25: at status researched, it needs ${field}\\.`));
  }
});

test("a spiked measured indicator also needs its curve", () => {
  assert.deepEqual(problemsOf(researched({ status: "spiked" })), []);
  expectProblem(problemsOf(without(researched({ status: "spiked" }), "curve")), /^pm25: at status spiked, it needs curve/);
});

test("each value must come from its allowed list", () => {
  const cases = [
    [{ preference_type: "sometimes" }, /^pm25: preference_type must be one of fixed, user-direction, user-range, user-choice/],
    [{ evidence_type: "anecdote" }, /^pm25: evidence_type must be one of direct, estimate, indirect, perception, ranking/],
    [{ comparable_across_regions: "yes" }, /^pm25: comparable_across_regions must be true or false/],
    [{ unit: "" }, /^pm25: unit must be non-empty text/],
    [{ method: 42 }, /^pm25: method must be non-empty text/],
    [{ curve: { shape: "s-curve" } }, /^pm25: curve.shape must be one of ramp, ideal-range, lookup, percentile/],
    [{ curve: { shape: "percentile", better: "more" } }, /^pm25: a percentile curve needs better: higher or lower/],
  ];
  for (const [fields, expected] of cases) expectProblem(problemsOf(researched(fields)), expected);
});

test("a curve must follow the rule of its shape", () => {
  const cases = [
    [{ shape: "ramp", t0: 5, t1: 5 }, /^pm25: a ramp needs two different numbers, t0 and t1/],
    [{ shape: "ramp", t0: "high", t1: 5 }, /^pm25: a ramp needs two different numbers, t0 and t1/],
    [{ shape: "ideal-range", l0: 14, l1: 20, u1: 18, u0: 32 }, /^pm25: an ideal-range curve needs numbers with l0 < l1 ≤ u1 < u0/],
    [{ shape: "lookup", scores: { low: 1.5 } }, /^pm25: a lookup curve needs scores, with a score from 0 to 1 for each category/],
    [{ shape: "lookup", scores: {} }, /^pm25: a lookup curve needs scores/],
    ["ramp", /^pm25: curve must be a mapping with a shape/],
  ];
  for (const [curve, expected] of cases) expectProblem(problemsOf(researched({ curve })), expected);
  const valid = [
    { shape: "ramp", t0: 0, t1: 10 },
    { shape: "ideal-range", l0: 14, l1: 20, u1: 20, u0: 32 },
    { shape: "lookup", scores: { "very low": 1, low: 0.75, high: 0 } },
    { shape: "percentile", better: "lower" },
  ];
  for (const curve of valid) assert.deepEqual(problemsOf(researched({ curve })), [], JSON.stringify(curve));
});

test("a curve needs a reason, whatever the status", () => {
  const idea = { id: "pm25", name: "PM2.5", default_weight: 3, curve: { shape: "ramp", t0: 25, t1: 5 } };
  expectProblem(problemsOf(idea), /^pm25: a curve needs a curve_reason/);
});

test("a user-range measured indicator needs an ideal-range curve", () => {
  expectProblem(problemsOf(researched({ preference_type: "user-range" })), /^pm25: a user-range measured indicator needs an ideal-range curve/);
  const band = { shape: "ideal-range", l0: 14, l1: 20, u1: 26, u0: 32 };
  assert.deepEqual(problemsOf(researched({ preference_type: "user-range", curve: band })), []);
});

test("a factor with sub-factors has no measured-indicator fields and no status", () => {
  const withUnit = catalogueWith(researched());
  withUnit.factors[0].unit = "µg/m³";
  expectProblem(core.validateCatalogue(withUnit, datasetsDoc()), /^environment: a factor with sub-factors is not a measured indicator, so it cannot have unit/);
  const withStatus = catalogueWith(researched());
  withStatus.factors[0].status = "researched";
  expectProblem(core.validateCatalogue(withStatus, datasetsDoc()), /^environment: a factor with sub-factors takes its research status from them/);
});

test("an unknown field is rejected, so that a misspelt name does not pass unseen", () => {
  expectProblem(problemsOf(researched({ units: "µg/m³" })), /^pm25: unknown field units/);
});

test("a measured indicator names each of its datasets once, and each must exist", () => {
  expectProblem(problemsOf(researched({ datasets: ["laei", "missing-one"] })), /^pm25: datasets.yaml has no dataset missing-one/);
  expectProblem(problemsOf(researched({ datasets: ["laei", "laei"] })), /^pm25: dataset laei is listed twice/);
  expectProblem(problemsOf(researched({ datasets: [] })), /^pm25: datasets must be a non-empty list of dataset ids/);
  expectProblem(problemsOf(researched(), { datasets: [] }), /^pm25: datasets.yaml has no dataset laei/);
});

test("a measured indicator of evidence type ranking needs datasets with a credibility rating", () => {
  expectProblem(problemsOf(researched({ evidence_type: "ranking" })), /^pm25: evidence type ranking needs a credibility rating on dataset laei/);
  const rated = datasetsDoc({ credibility: "medium", credibility_reason: "Its method is published." });
  assert.deepEqual(problemsOf(researched({ evidence_type: "ranking" }), rated), []);
});

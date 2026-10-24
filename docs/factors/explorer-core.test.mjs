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

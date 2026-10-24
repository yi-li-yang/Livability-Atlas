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

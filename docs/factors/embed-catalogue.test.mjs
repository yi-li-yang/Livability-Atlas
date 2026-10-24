// Tests for embed-catalogue.mjs. Run: node --test "docs/factors/*.test.mjs"
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { CATALOGUE, PAGE, embed, embeddedCopy } from "./embed-catalogue.mjs";

const page = '<p>Before</p>\r\n<script type="text/yaml" id="catalogue">\r\nold: 1\r\n</script>\r\n<p>After</p>\r\n';

test("embed puts the catalogue between the markers, and embeddedCopy reads it back", () => {
  const out = embed(page, "factors: []\r\n");
  assert.equal(embeddedCopy(out), "factors: []\n");
  assert.ok(out.startsWith("<p>Before</p>\n"));
  assert.ok(out.endsWith("</script>\n<p>After</p>\n"));
});

test("embed refuses text that would end the script block early", () => {
  assert.throws(() => embed(page, "a: </script>"), /must not contain/);
  assert.throws(() => embed(page, "a: <!-- b"), /must not contain/);
});

test("the page's embedded copy matches catalogue/factors.yaml", () => {
  const yaml = readFileSync(CATALOGUE, "utf8").replace(/\r\n/g, "\n");
  assert.equal(embeddedCopy(readFileSync(PAGE, "utf8")), yaml, "Run: node docs/factors/embed-catalogue.mjs");
});

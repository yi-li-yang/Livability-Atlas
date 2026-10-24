// Tests for embed-catalogue.mjs. Run: node --test "docs/factors/*.test.mjs"
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { PAGE, SOURCES, embed, embeddedCopy } from "./embed-catalogue.mjs";

const page = [
  "<p>Before</p>",
  '<script type="text/yaml" id="factors">',
  "old: 1",
  "</script>",
  '<script type="text/yaml" id="datasets">',
  "old: 2",
  "</script>",
  "<p>After</p>",
  "",
].join("\r\n");

test("embed puts a file between its block's markers, and embeddedCopy reads it back", () => {
  const out = embed(page, "factors", "factors: []\r\n");
  assert.equal(embeddedCopy(out, "factors"), "factors: []\n");
  assert.ok(out.startsWith("<p>Before</p>\n"));
  assert.ok(out.endsWith("</script>\n<p>After</p>\n"));
});

test("embedding one block leaves the other unchanged", () => {
  const out = embed(page, "datasets", "datasets: []\n");
  assert.equal(embeddedCopy(out, "datasets"), "datasets: []\n");
  assert.equal(embeddedCopy(out, "factors"), "old: 1\n");
});

test("a page without the named block is refused, naming the block", () => {
  assert.throws(() => embeddedCopy("<p>No blocks</p>", "datasets"), /has no <script type="text\/yaml" id="datasets"> block/);
});

test("embed refuses text that would end the script block early", () => {
  assert.throws(() => embed(page, "factors", "a: </script>"), /factors\.yaml must not contain/);
  assert.throws(() => embed(page, "datasets", "a: <!-- b"), /datasets\.yaml must not contain/);
});

test("the page's embedded copies match catalogue/factors.yaml and catalogue/datasets.yaml", () => {
  const html = readFileSync(PAGE, "utf8");
  for (const [name, file] of Object.entries(SOURCES)) {
    const yaml = readFileSync(file, "utf8").replace(/\r\n/g, "\n");
    assert.equal(embeddedCopy(html, name), yaml, `Run: node docs/factors/embed-catalogue.mjs (${name})`);
  }
});

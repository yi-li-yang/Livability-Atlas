// Tests for artifact-page.mjs. Run: node --test "docs/factors/*.test.mjs"
import test from "node:test";
import assert from "node:assert/strict";
import { artifactPage } from "./artifact-page.mjs";

test("artifactPage drops the document wrapper and keeps everything else", () => {
  const html = [
    "<!doctype html>",
    '<html lang="en-GB">',
    "<head>",
    '<meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
    "<title>Factor explorer</title>",
    "</head>",
    "<body>",
    "<main>Hello</main>",
    "</body>",
    "</html>",
    "",
  ].join("\r\n");
  assert.equal(artifactPage(html), "<title>Factor explorer</title>\n<main>Hello</main>\n");
});

test("artifactPage fails loudly when the wrapper is not where it expects", () => {
  assert.throws(() => artifactPage("<main>Hello</main>"), /Expected to remove 9 wrapper lines/);
});

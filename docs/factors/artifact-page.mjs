// Writes the Artifact copy of the explorer: the same page without the
// <!doctype>, <html>, <head> and <body> wrapper, which the Artifact host adds
// itself. Usage: node docs/factors/artifact-page.mjs <output.html>
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const PAGE = path.join(path.dirname(fileURLToPath(import.meta.url)), "explorer.html");
const WRAPPER = [
  /^<!doctype html>$/i,
  /^<html\b[^>]*>$/i,
  /^<head>$/i,
  /^<meta charset="utf-8">$/i,
  /^<meta name="viewport"[^>]*>$/i,
  /^<\/head>$/i,
  /^<body>$/i,
  /^<\/body>$/i,
  /^<\/html>$/i,
];

export function artifactPage(html) {
  const lines = html.split(/\r?\n/);
  const kept = lines.filter((line) => !WRAPPER.some((pattern) => pattern.test(line.trim())));
  const removed = lines.length - kept.length;
  if (removed !== WRAPPER.length) {
    throw new Error(`Expected to remove ${WRAPPER.length} wrapper lines, but removed ${removed}. Check the first and last lines of explorer.html.`);
  }
  return kept.join("\n");
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const output = process.argv[2];
  if (!output) {
    console.error("Usage: node docs/factors/artifact-page.mjs <output.html>");
    process.exit(2);
  }
  writeFileSync(output, artifactPage(readFileSync(PAGE, "utf8")));
  console.log(`Wrote the Artifact copy to ${output}.`);
}

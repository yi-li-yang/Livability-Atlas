// Copies catalogue/factors.yaml into explorer.html, inside the
// <script type="text/yaml" id="catalogue"> block. With --check it changes
// nothing, and exits with status 1 when the copy is out of date.
// Usage: node docs/factors/embed-catalogue.mjs [--check]
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
export const CATALOGUE = path.join(here, "..", "..", "catalogue", "factors.yaml");
export const PAGE = path.join(here, "explorer.html");
const OPEN = '<script type="text/yaml" id="catalogue">';
const CLOSE = "</script>";

const lf = (text) => text.replace(/\r\n/g, "\n");

function blockBounds(html) {
  const start = html.indexOf(OPEN);
  if (start === -1) throw new Error(`explorer.html has no ${OPEN} block.`);
  const end = html.indexOf(CLOSE, start + OPEN.length);
  return { start: start + OPEN.length, end };
}

// Returns the catalogue text embedded in the page, with LF line endings.
export function embeddedCopy(html) {
  const text = lf(html);
  const { start, end } = blockBounds(text);
  return text.slice(start, end).replace(/^\n/, "");
}

// Returns the page with the catalogue embedded, with LF line endings.
export function embed(html, yaml) {
  if (/<\/script|<!--/i.test(yaml)) {
    throw new Error("factors.yaml must not contain '</script' or '<!--', because they would end the script block early.");
  }
  const text = lf(html);
  const { start, end } = blockBounds(text);
  return `${text.slice(0, start)}\n${lf(yaml)}${text.slice(end)}`;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const yaml = readFileSync(CATALOGUE, "utf8");
  const html = readFileSync(PAGE, "utf8");
  if (process.argv.includes("--check")) {
    const current = embeddedCopy(html) === lf(yaml);
    console.log(current
      ? "The embedded catalogue is up to date."
      : "The embedded catalogue is out of date. Run: node docs/factors/embed-catalogue.mjs");
    process.exit(current ? 0 : 1);
  }
  writeFileSync(PAGE, embed(html, yaml));
  console.log("Copied catalogue/factors.yaml into docs/factors/explorer.html.");
}

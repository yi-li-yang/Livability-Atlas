// Copies the factor catalogue into explorer.html: catalogue/factors.yaml into
// the <script type="text/yaml" id="factors"> block, and catalogue/datasets.yaml
// into the <script type="text/yaml" id="datasets"> block. With --check it
// changes nothing, and exits with status 1 when a copy is out of date.
// Usage: node docs/factors/embed-catalogue.mjs [--check]
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const catalogue = path.join(here, "..", "..", "catalogue");
// Each embedded block, by its id in the page, and the file it copies.
export const SOURCES = {
  factors: path.join(catalogue, "factors.yaml"),
  datasets: path.join(catalogue, "datasets.yaml"),
};
export const PAGE = path.join(here, "explorer.html");
const CLOSE = "</script>";

const lf = (text) => text.replace(/\r\n/g, "\n");
const opening = (name) => `<script type="text/yaml" id="${name}">`;

function blockBounds(html, name) {
  const open = opening(name);
  const start = html.indexOf(open);
  if (start === -1) throw new Error(`explorer.html has no ${open} block.`);
  const end = html.indexOf(CLOSE, start + open.length);
  return { start: start + open.length, end };
}

// Returns the text embedded in the named block, with LF line endings.
export function embeddedCopy(html, name) {
  const text = lf(html);
  const { start, end } = blockBounds(text, name);
  return text.slice(start, end).replace(/^\n/, "");
}

// Returns the page with the YAML embedded in the named block, with LF line endings.
export function embed(html, name, yaml) {
  if (/<\/script|<!--/i.test(yaml)) {
    throw new Error(`${name}.yaml must not contain '</script' or '<!--', because they would end the script block early.`);
  }
  const text = lf(html);
  const { start, end } = blockBounds(text, name);
  return `${text.slice(0, start)}\n${lf(yaml)}${text.slice(end)}`;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  let html = readFileSync(PAGE, "utf8");
  if (process.argv.includes("--check")) {
    const stale = Object.entries(SOURCES)
      .filter(([name, file]) => embeddedCopy(html, name) !== lf(readFileSync(file, "utf8")))
      .map(([name]) => `${name}.yaml`);
    console.log(stale.length === 0
      ? "The embedded catalogue is up to date."
      : `The embedded copy of ${stale.join(" and ")} is out of date. Run: node docs/factors/embed-catalogue.mjs`);
    process.exit(stale.length === 0 ? 0 : 1);
  }
  for (const [name, file] of Object.entries(SOURCES)) html = embed(html, name, readFileSync(file, "utf8"));
  writeFileSync(PAGE, html);
  console.log("Copied catalogue/factors.yaml and catalogue/datasets.yaml into docs/factors/explorer.html.");
}

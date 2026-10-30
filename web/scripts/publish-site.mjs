// Builds the web app for GitHub Pages, adds the newest published data bundle of a region, and
// pushes the result to the `gh-pages` branch (replacing it: the branch holds only the site).
//
//   node scripts/publish-site.mjs [--region london] [--dry-run]
//
// The bundle is whatever `latest.json` names under the data folder's `published/`, which only
// holds a bundle that passed the QA report. The data folder is ATLAS_DATA_DIR, else `data/` in the
// repository. Run from web/.
import { execFileSync } from "node:child_process";
import {
  cpSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const args = process.argv.slice(2);
const region = args.includes("--region")
  ? args[args.indexOf("--region") + 1]
  : "london";
const dryRun = args.includes("--dry-run");
const repo = resolve(import.meta.dirname, "../..");
const web = join(repo, "web");
const data = process.env.ATLAS_DATA_DIR ?? join(repo, "data");
const published = join(data, "published", region);
const run = (cmd, argv, options = {}) =>
  execFileSync(cmd, argv, {
    stdio: "inherit",
    shell: process.platform === "win32",
    ...options,
  });

const { version } = JSON.parse(
  readFileSync(join(published, "latest.json"), "utf8"),
);
const bundle = join(published, version);
if (!existsSync(join(bundle, "manifest.json"))) {
  throw new Error(`there is no bundle ${version} in ${published}`);
}
const remote = execFileSync("git", ["remote", "get-url", "origin"], {
  cwd: repo,
})
  .toString()
  .trim();
const name = remote
  .replace(/\.git$/, "")
  .split("/")
  .pop();

run("npm", ["run", "build"], {
  cwd: web,
  env: { ...process.env, VITE_BASE: `/${name}/` },
});

const site = mkdtempSync(join(tmpdir(), "site-"));
cpSync(join(web, "dist"), site, { recursive: true });
const target = join(site, "bundles", region);
mkdirSync(join(target, version), { recursive: true });
for (const file of ["manifest.json", "cells.parquet"]) {
  cpSync(join(bundle, file), join(target, version, file));
}
writeFileSync(join(target, "latest.json"), JSON.stringify({ version }) + "\n");
writeFileSync(join(site, ".nojekyll"), "");
console.log(`site for ${region} ${version} is in ${site}`);

if (dryRun) process.exit(0);
const git = (...argv) =>
  execFileSync("git", argv, { cwd: site, stdio: "inherit" });
git("init", "-q", "-b", "gh-pages");
git("add", "-A");
git(
  "-c",
  "user.name=Livability Atlas",
  "-c",
  "user.email=noreply@users.noreply.github.com",
  "commit",
  "-q",
  "-m",
  `Site with ${region} bundle ${version}`,
);
git("push", "--force", remote, "gh-pages");
rmSync(site, { recursive: true, force: true });
console.log(`published to the gh-pages branch of ${remote}`);

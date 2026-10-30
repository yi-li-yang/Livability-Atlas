import { join, resolve } from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";
import { serveBundles } from "./serve-bundles.ts";

// Bundles come from ATLAS_BUNDLES_DIR, else from `published/` in the data folder that
// `atlas build` writes to (ATLAS_DATA_DIR, else `data/` in the repository).
const bundles =
  process.env.ATLAS_BUNDLES_DIR ??
  join(
    process.env.ATLAS_DATA_DIR ?? resolve(import.meta.dirname, "../data"),
    "published",
  );

// https://vite.dev/config/
export default defineConfig({
  // The site is served from a folder on GitHub Pages, which `just site` sets with VITE_BASE.
  base: process.env.VITE_BASE ?? "/",
  plugins: [react(), tailwindcss(), serveBundles(bundles)],
  // Playwright's tests live in e2e/ and run with `just e2e`, not under Vitest.
  test: { include: ["src/**/*.test.{ts,tsx}"] },
});

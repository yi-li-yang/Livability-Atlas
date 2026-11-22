import { defineConfig } from "@playwright/test";

// Another app on the machine may hold the usual port: ATLAS_E2E_PORT picks another one.
const port = Number(process.env.ATLAS_E2E_PORT ?? 4173);

export default defineConfig({
  testDir: "./e2e",
  webServer: {
    command: `npm run preview -- --port ${port} --strictPort`,
    // The tests read a small bundle that is kept in the repository, not the real data.
    env: { ATLAS_BUNDLES_DIR: "./e2e/fixtures/bundles" },
    url: `http://localhost:${port}`,
    reuseExistingServer: false,
    timeout: 30_000,
  },
  use: {
    baseURL: `http://localhost:${port}`,
    // Headless Chromium has no GPU, and MapLibre needs WebGL.
    launchOptions: {
      args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
    },
  },
});

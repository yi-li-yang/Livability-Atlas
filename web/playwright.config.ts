import { defineConfig } from "@playwright/test";

// Another app on the machine may hold the usual port: ATLAS_E2E_PORT picks another one.
const port = Number(process.env.ATLAS_E2E_PORT ?? 4173);

// MapLibre and deck.gl need WebGL. Headless Chromium draws it in software (SwiftShader) unless it is
// told to use the GPU, and software WebGL keeps several CPU threads busy in each browser. On a local
// Windows machine the GPU works through Direct3D 11, and a full run takes a third of the time.
// CI (Linux, no GPU) and other local machines draw in software.
const gpu = !process.env.CI && process.platform === "win32";

export default defineConfig({
  testDir: "./e2e",
  // Each worker is a browser. Playwright's default, half the CPU threads, starts so many that a
  // local machine stalls and tests time out. CI keeps the default.
  workers: process.env.CI ? undefined : gpu ? 4 : 2,
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
    launchOptions: {
      // With the GPU, SwiftShader stays allowed as the fallback if the GPU cannot be used.
      args: gpu
        ? ["--use-angle=d3d11", "--enable-unsafe-swiftshader"]
        : ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
    },
  },
});

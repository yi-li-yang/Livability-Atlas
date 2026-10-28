import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Playwright's tests live in e2e/ and run with `just e2e`, not under Vitest.
  test: { include: ["src/**/*.test.{ts,tsx}"] },
});

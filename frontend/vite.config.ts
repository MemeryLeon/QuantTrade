/// <reference types="vitest" />

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/backtests": apiProxyTarget,
      "/jobs": apiProxyTarget,
      "/market": apiProxyTarget,
      "/health": apiProxyTarget,
    },
  },
  test: {
    environment: "jsdom",
    exclude: ["node_modules/**", "dist/**", "tests/e2e/**"],
    globals: true,
    setupFiles: "./src/test/setup.ts",
  },
});

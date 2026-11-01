import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// The build goes to ../web, which Flask serves. In dev, /api calls go to Flask on port 5000.
export default defineConfig({
  plugins: [react()],
  build: { outDir: "../web", emptyOutDir: true, modulePreload: { polyfill: false } },
  server: { proxy: { "/api": "http://localhost:5000" } },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: false,
    coverage: { provider: "v8", include: ["src/**/*.{ts,tsx}"], exclude: ["src/test/**", "src/main.tsx", "src/types.ts", "src/**/*.test.*"] },
  },
});

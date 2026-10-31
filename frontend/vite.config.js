import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The build goes to ../web, which Flask serves. In dev, /api calls go to Flask on port 5000.
export default defineConfig({
  plugins: [react()],
  build: { outDir: "../web", emptyOutDir: true, modulePreload: { polyfill: false } },
  server: { proxy: { "/api": "http://localhost:5000" } },
});

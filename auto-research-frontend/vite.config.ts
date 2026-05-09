import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// Relative `base` so the built bundle works from any path on disk
// (e.g. `runs/<id>/_dashboard/` served by `python -m http.server`).
export default defineConfig({
  plugins: [react()],
  base: "./",
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          katex: ["katex"],
          recharts: ["recharts"],
        },
      },
    },
  },
});

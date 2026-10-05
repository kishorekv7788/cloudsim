import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },   // send API calls to FastAPI
  optimizeDeps: { exclude: ["pyodide"] },   // pyodide.mjs branches on Node builtins; let it load as-is
});

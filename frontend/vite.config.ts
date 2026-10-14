import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

// In development the API runs on :8000 (override with API_URL); in Docker nginx does this proxying.
export default defineConfig(({ mode }) => ({
  plugins: [react()],
  server: { port: 5173, proxy: { "/api": loadEnv(mode, ".", "").API_URL || "http://localhost:8000" } },
  test: { environment: "node" },
}));

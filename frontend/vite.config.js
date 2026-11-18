import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// In dev, /api/* is proxied to the FastAPI server so the browser sees one origin (no CORS setup needed).
// Override the target with VITE_PROXY_TARGET if the backend runs elsewhere.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: { "/api": process.env.VITE_PROXY_TARGET || "http://localhost:8000" },
  },
  test: { environment: "jsdom", setupFiles: "./src/test/setup.js", globals: true },
});

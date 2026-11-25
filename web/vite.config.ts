import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vite";
import { arenaMock } from "./mock/arenaMock";

// The page only draws; every rule lives in the Python server. In development, /api and /ws go to it.
// `vite --mode mock` (bun run dev:mock) swaps the Python server for a fake one inside Vite.
export default defineConfig(({ mode }) => ({
  plugins: mode === "mock" ? [react(), tailwindcss(), arenaMock()] : [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  server: {
    host: "127.0.0.1",
    proxy:
      mode === "mock"
        ? undefined
        : { "/api": "http://127.0.0.1:8000", "/ws": { target: "ws://127.0.0.1:8000", ws: true } },
  },
}));

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The page only draws; every rule lives in the Python server. In development, /api and /ws go to it.
export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/ws": { target: "ws://127.0.0.1:8000", ws: true },
    },
  },
});

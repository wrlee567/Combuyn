import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In docker-compose the backend is reachable at http://api:8000; for a plain
// local run it's http://localhost:8000. Override with PROXY_TARGET if needed.
const proxyTarget = process.env.PROXY_TARGET ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": proxyTarget,
      "/auth": proxyTarget,
      "/health": proxyTarget,
      "/ready": proxyTarget,
    },
  },
});

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5022,
    proxy: {
      "/api": {
        target: "http://localhost:8022",
        changeOrigin: true,
      },
    },
  },
});

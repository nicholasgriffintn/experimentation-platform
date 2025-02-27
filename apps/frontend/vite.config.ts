import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";
import { join } from "path";

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    port: 3000,
    host: true,
    cors: true,
    watch: {
      usePolling: true,
    },
  },
  resolve: {
    alias: {
      $lib: join(__dirname, "src/lib"),
    },
  },
});

// @ts-check
import { defineConfig } from "astro/config";
import react from "@astrojs/react";
import tailwindcss from "@tailwindcss/vite";

// Static-first; React islands hydrate only where needed [P1a,P5a].
export default defineConfig({
  integrations: [react()],
  vite: { plugins: [tailwindcss()] },
});

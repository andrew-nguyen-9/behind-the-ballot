// @ts-check
import { defineConfig } from "astro/config";
import react from "@astrojs/react";
import sitemap from "@astrojs/sitemap";
import mdx from "@astrojs/mdx";
import tailwindcss from "@tailwindcss/vite";

// `site` feeds sitemap + canonical/OG URLs [U4a,U5a]. Placeholder until the domain is
// provisioned (account-blocked, see ACCOUNTS.md); finalize in v1.0.4 era.
export default defineConfig({
  site: "https://ballot.an9.dev",
  integrations: [react(), sitemap(), mdx()],
  vite: { plugins: [tailwindcss()] },
});

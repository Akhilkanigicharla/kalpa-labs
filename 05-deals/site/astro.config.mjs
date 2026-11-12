import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";
// Site URL is a placeholder until the CEO approves the brand name and domain (b5.W1.1).
export default defineConfig({ site: "https://calc.example.in", integrations: [sitemap({ filter: (p) => !p.includes("/kits/thanks") })], build: { format: "directory" },
  // never inline scripts: the CSP in public/_headers allows scripts from our own files only
  vite: { build: { assetsInlineLimit: 0 } } });

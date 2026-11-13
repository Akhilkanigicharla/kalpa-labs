// robots.txt from the one site URL in astro.config.mjs (SEO check 2): allow the site, block the API and the private thanks page.
import type { APIRoute } from "astro";
export const GET: APIRoute = ({ site }) =>
  new Response(`User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /kits/thanks/\n\nSitemap: ${new URL("/sitemap-index.xml", site)}\n`, { headers: { "Content-Type": "text/plain; charset=utf-8" } });

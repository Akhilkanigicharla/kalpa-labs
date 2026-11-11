// llms.txt (SEO check 20): what the site offers, for whom, and links to key pages. No prices: kits are not on sale yet.
import type { APIRoute } from "astro";
import { CALCS } from "../lib/calcs";
import { KITS } from "../lib/kits";
export const GET: APIRoute = ({ site }) => {
  const u = (p: string) => new URL(p, site).toString();
  const body = [
    "# Kalpa Labs money calculators",
    "",
    "> Free money calculators for people in India, in English and Telugu: income tax for tax year 2026-27 (new vs old regime), salary in hand, GST, gratuity, SIP, EMI, FD, RD, PPF and HRA. No sign-up; works on a phone. A calculator, not financial or tax advice.",
    "",
    "## Calculators (English)",
    ...CALCS.map((c) => `- [${c.title.en}](${u(`/${c.slug}/`)}): ${c.blurb.en}`),
    "",
    "## Calculators (Telugu)",
    `- [Telugu home](${u("/te/")})`,
    "",
    "## Google Sheets kits",
    ...KITS.map((k) => `- [${k.name}](${u(`/kits/${k.slug}/`)}): ${k.short}`),
    "",
    "## About",
    `- [About](${u("/legal/about/")})`,
    `- [Contact](${u("/legal/contact/")})`,
    "",
  ].join("\n");
  return new Response(body, { headers: { "Content-Type": "text/plain; charset=utf-8" } });
};

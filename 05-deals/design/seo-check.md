# SEO check: money calculators site (05-deals/site) · 11 Nov 2026

Public site: 11 calculators in English and Telugu, the kits pages and the policy pages (33 pages). Built with Astro;
`astro.config.mjs` `site` is the one URL every canonical, og:url, sitemap, robots.txt and llms.txt is built from.
It is still the placeholder `https://calc.example.in` until Akhil approves the name and domain (b5.W1.1); change that one
line, rebuild and run the checker again with the real URL.

Run: `cd 05-deals/site && npx astro build && cd ../.. && python3 00-hq/site/tests/test_seo.py 05-deals/site/dist https://calc.example.in --private=kits/thanks/index.html --live`
Result 11 Nov 2026: **PASS SEO checks** (all 16 automatic checks, external links answered). `npx vitest run`: 58 passed.

What was added (A194): share tags (og:*, twitter card) + `public/og.png` (1200×630, 39 KB, `scripts/og.py`), Organization +
WebSite schema on both home pages and WebPage schema on pages without their own, `robots.txt` and `llms.txt` generated
from the site URL, `noindex` on the private thanks page, `src/lib/seo.ts` keeps every title 30–60 and description 70–160
(tested for every calculator and kit), missing `#lite` targets fixed. The checker now reads Astro output
(subfolder pages, `sitemap-index.xml`) and takes `--private=`.

| # | Manual row | Status |
|---|---|---|
| 14 | Core Web Vitals | Static pages, about 20–40 KB HTML each, no third-party scripts. Missing: fonts still come from Google Fonts (one render-blocking stylesheet, preconnect set); self-host them like `00-hq/site/fonts` if PageSpeed mobile shows it matters. Real PageSpeed number after go-live. |
| 17 | Clean URL slugs | Lowercase and hyphens: `/income-tax/`, `/te/income-tax/`, `/kits/gate-2027/`, `/legal/privacy/`. No `.html`, no query strings. |
| 19 | Search Console | Not yet: needs the real domain (b5.W1.1), then Akhil adds the property with the HTML-tag method like C66. |
| — | Target words | "income tax calculator 2026-27 new vs old regime", "salary in hand calculator", "SIP calculator", "EMI calculator", Telugu: "ఆదాయపు పన్ను కాలిక్యులేటర్". Fuller list queued for the free agents (K067). |
| — | ASCI #ad | The site has no affiliate links today: kit links are our own product with the full price shown (`KitCta.astro`). Affiliate deals go only to the Telegram channel, where `src/bot/post.py` and `channel.py` refuse any post without `#ad` in its first two lines (tests `test_post.py`, `test_channel.py`). Any future affiliate link on the site must carry `rel="sponsored"` and a visible `#ad` label. |

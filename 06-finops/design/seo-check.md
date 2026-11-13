# SEO check: Ledger Peaks site · 12 Nov 2026 (A192)

Automatic: `python3 06-finops/site/build.py && python3 00-hq/site/tests/test_seo.py 06-finops/site/_dist https://ledger-peaks.netlify.app` → **PASS** (also `06-finops/tests/test_site.py`, and the Kalpa quality workflow builds the site before `eng_check.py`: finops-site 14 pass, 0 fail). Sources stay in `06-finops/design/`; `site/build.py` adds the tags, so every rebuild keeps them. Tap sweep 390 px light + dark: PASS on `/`, `/sample-x-ray`, `/404` (local serve).

Public pages: `/` (landing + free X-ray form) and `/sample-x-ray` (sample report, synthetic data). `404.html` is noindex. `/api/` is disallowed in robots.txt and is not deployed (rule 9).

| # | Manual row | Status |
|---|---|---|
| 14 | Core Web Vitals | Static pages under 20 KB HTML, self-hosted fonts, no third-party scripts. PageSpeed numbers: after Akhil's go and first deploy. |
| 16 | HTTPS + HSTS | `_headers` sends HSTS, strict CSP (`script-src 'self'`, inline scripts moved to `*.page.js`), `frame-ancestors 'none'`, nosniff, Permissions-Policy. Netlify serves HTTPS on its subdomain. |
| 17 | Clean URL slugs | `/`, `/sample-x-ray` (Netlify pretty URLs; canonicals use the clean form). |
| 19 | Search Console | Not done: needs the site live first (Akhil's go), then a URL-prefix property the same way as C66. |
| — | Host name | `ledger-peaks.netlify.app` is a placeholder until the Netlify site exists; set `SITE_URL` and rebuild if the name differs. |
| — | Target words | "LLM cost per customer India", "OpenAI bill in rupees", "AI cost audit India". |

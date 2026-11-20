# Static-site host fallback (A222, 21 Nov 2026)

Checked today on the providers' own pages (Firecrawl, live fetch).

| | Netlify Free (now) | Cloudflare Pages Free (fallback) |
|---|---|---|
| Monthly budget | 300 credits, hard limit; site **pauses** until next billing cycle when reached | 500 builds a month, 1 build at a time |
| Cost of one production deploy | 15 credits (≈ 20 deploys/month if nothing else used credits) | 1 build |
| Bandwidth | 20 credits per GB (counts against the same 300) | unverified (the product page fetched today showed no figure) |
| Headers | `netlify.toml` | `_headers` file, max 100 rules |
| Size limits | — | 20,000 files per site, 25 MiB per file |
| Card needed | no (Free) | no (Free) — unverified today |

Sources (fetched 2026-11-21): netlify.com/pricing; docs.netlify.com …/credit-based-pricing-plans; developers.cloudflare.com/pages/platform/limits. Cloudflare's bandwidth and "no card" lines are **unverified**; Cloudflare also now points Pages users at Workers static assets (its MCP lists a "migrate Pages to Workers" guide), so check that before any move.

Our rule (in CLAUDE.md, `00-hq/tools/deploy_budget.py`): one Netlify deploy per site per day, stop at 240 credits. Bandwidth also eats credits, so the 240 cap leaves 60 credits (= 3 GB) of headroom.

Recommendation for Akhil: stay on Netlify while deploys stay under ~10 a month; if the budget tool says STOP twice in a cycle, move the static HQ site to Cloudflare Pages (needs Akhil's own Cloudflare account, C65 already covers it). Nothing moves without his yes.

Free-model draft K145 used; its numbers were all "UNVERIFIED" and are replaced by the table above.

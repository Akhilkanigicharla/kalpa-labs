# SEO check: BotBhai · 9 Nov 2026

BotBhai has two kinds of web output:
1. **Client sites** (`seo/seo_bot.py`, one per business): public, must pass all 20 checks. `tools/test-all.sh` builds a sample salon, gym, real-estate and exam-kits site and runs `00-hq/site/tests/test_seo.py` on each: all PASS. New on 9 Nov: og:url, og:image (client's `cover_photo`, else a plain 1200×630 hero-green card written with the standard library), twitter card, WebSite schema next to the LocalBusiness subtype + FAQPage.
2. **Private screens and sales papers** (`web/dist`: dashboard, inbox, billing, artifact, invoice sample, `sales/*` HTML + PDF, `cards/*`, `screens/*`): never in search. App screens carry `<meta name="robots" content="noindex">`; every private path also gets `X-Robots-Tag: noindex, nofollow` in `netlify.toml` (covers PDFs). `seo/test_private_noindex.py` fails if a new private file is missed (proved by removing a rule).

| # | Manual row | Status |
|---|---|---|
| 14 | Core Web Vitals | Client sites are one static page, self-hosted fonts; existing Lighthouse config in `seo/lighthouserc.json`. Real PageSpeed per client after go-live. |
| 17 | Clean URL slugs | `/` and `/<service>-in-<area>` (only with real local content). |
| 19 | Search Console | Per client, done during onboarding with the client's own Google account (in `citations.csv` steps). |
| — | Target words | "<service> near me", "<service> in <area>" (from `keywords.csv`). |

## Glow-up pages (A199, 12 Nov 2026)
Built by `botbhai/glowup/glowup.py` on the same client-site template as `seo/seo_bot.py`. `tools/test_glowup.py` runs `test_seo.py` (20 checks) and the 390 px tap sweep (light + dark) on a worst-case demo (long name with emoji and `<script>`, Telugu text, 80-letter word, GPS-tagged photos). Found and fixed: JSON-LD could be broken by a `</script>` in a client name (now `<`, fixes every client site), long titles/short descriptions, sideways scroll from long words.

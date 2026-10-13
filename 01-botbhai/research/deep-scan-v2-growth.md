# Deep Scan v2 · Growth tools for every world (scraping, SEO, CRM, email, social)

Deep-Scan step 5 of 8, 13 Oct 2026. Follows [a3-leads-seo.md](a3-leads-seo.md). Engineering research, not legal advice.

**Method.** Star counts and "updated" dates come from GitHub topic pages sorted by stars (`web-scraping`, `seo`, `marketing-automation`, `crm`, `newsletter`, `social-media-scheduler`), read on 13 Oct 2026 (GitHub's page cache, so treat them as ±5%). "Last activity" is the topic page's *Updated* date. Licences were read from each repo's `LICENSE` file on its default branch (raw file, not the sidebar). Repos that only repackage AI prompts ("Claude skills") are left out of the ranking.

**Headline.** The growth stack that is both popular and permissive is small: **Scrapling (BSD-3), Scrapy (BSD-3), Crawlee (Apache-2.0), changedetection.io (Apache-2.0), Lighthouse CI (Apache-2.0), open-seo (MIT), extruct (BSD-3), trafilatura (Apache-2.0)**. Almost every popular CRM, newsletter and social-scheduler tool is **AGPL or GPL** (Twenty, listmonk, Postiz, Mautic, BillionMail, EspoCRM, frappe/crm), so Kalpa Labs can only run them as separate, unmodified services and must never copy their code into anything sold.

## Top 30 by stars

| # | Repo | Stars | Last activity | Licence (caveats) | What it is | Verdict for Kalpa |
|---|---|---|---|---|---|---|
| 1 | [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl) | 177k | 2026-09-05 | **AGPL-3.0** | Hosted scrape/crawl API for LLMs | AVOID code; its paid API isn't needed |
| 2 | [D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling) | 78.5k | 2026-09-04 | BSD-3 | Adaptive scraper (selectors survive layout changes) | LEARN: step up if enrich.py ever needs multi-page crawls |
| 3 | [scrapy/scrapy](https://github.com/scrapy/scrapy) | 64.2k | 2026-09-03 | BSD-3 | Classic crawling framework | LEARN (too heavy for 1 page per prospect) |
| 4 | [dgtlmoon/changedetection.io](https://github.com/dgtlmoon/changedetection.io) | 33.6k | 2026-09-04 | Apache-2.0 | Page-change monitor with alerts | **ADOPT later** for b5 deals (price-drop alerts on pages we may watch) |
| 5 | [CloakHQ/CloakBrowser](https://github.com/CloakHQ/CloakBrowser) | 31.2k | 2026-09-04 | (not checked) | Stealth Chromium to evade bot detection | **AVOID**: evading detection breaks site terms |
| 6 | [ScrapeGraphAI/Scrapegraph-ai](https://github.com/ScrapeGraphAI/Scrapegraph-ai) | 30.6k | 2026-08-27 | MIT | LLM-driven scraper | LEARN; costs tokens per page, unneeded |
| 7 | [apify/crawlee](https://github.com/apify/crawlee) | 25.7k | 2026-09-04 | Apache-2.0 | JS crawling + browser automation | LEARN |
| 8 | [twentyhq/twenty](https://github.com/twentyhq/twenty) | 54.9k | 2026-08-13 | **AGPL-3.0 + commercial `ee`** | Salesforce alternative | AVOID code; BotBhai's Supabase lead table is enough |
| 9 | [frappe/erpnext](https://github.com/frappe/erpnext) | 38k | 2026-08-13 | GPL-3.0 | ERP | AVOID |
| 10 | [knadh/listmonk](https://github.com/knadh/listmonk) | 23.4k | 2026-09-06 | **AGPL-3.0** | Self-hosted newsletter (one binary) | Separate service only, if b3/b5 email ever needs it |
| 11 | [krayin/laravel-crm](https://github.com/krayin/laravel-crm) | 23.7k | 2026-08-07 | MIT | Laravel CRM | LEARN (pipeline stages) |
| 12 | [open-seo (every-app)](https://github.com/every-app/open-seo) | 21.3k | 2026-09-20 | MIT | Semrush/Ahrefs alternative | LEARN for a sellable "SEO health check"; needs paid data APIs |
| 13 | [apify/crawlee-python](https://github.com/apify/crawlee-python) | 9.5k | 2026-09-04 | Apache-2.0 | Python crawler | LEARN (a3's pick for multi-page crawls) |
| 14 | [maxun](https://github.com/getmaxun/maxun) | 17.4k | 2026-09-05 | **AGPL-3.0** | No-code scraping | AVOID |
| 15 | [Billionmail/BillionMail](https://github.com/Billionmail/BillionMail) | 15.6k | 2026-06-11 | **AGPL-3.0** | Mail server + marketing | AVOID (self-hosted mail = deliverability pain) |
| 16 | [mautic/mautic](https://github.com/mautic/mautic) | 10.5k | 2026-09-22 | **GPL-3.0** | Marketing automation | Separate service only |
| 17 | [HEAD (joshbuchea)](https://github.com/joshbuchea/HEAD) | 30.3k | 2026-05-28 | (not checked) | Every `<head>` tag explained | LEARN: checklist for seo_bot |
| 18 | [next-seo](https://github.com/garmeeh/next-seo) | 8.5k | 2026-07-29 | MIT | Next.js SEO metadata | LEARN (we use Astro/plain HTML) |
| 19 | [alirezamika/autoscraper](https://github.com/alirezamika/autoscraper) | 7.9k | 2026-07-29 | MIT | Learns selectors from examples | LEARN |
| 20 | [GoogleChrome/lighthouse-ci](https://github.com/GoogleChrome/lighthouse-ci) | 6.5k | 2025-06 | Apache-2.0 | Lighthouse + score assertions in CI | **ADOPT** (built below) |
| 21 | [Mailtrain](https://github.com/Mailtrain-org/mailtrain) | 5.8k | 2025-10-05 | GPL-3.0 | Newsletter app | AVOID (stale) |
| 22 | [adbar/trafilatura](https://github.com/adbar/trafilatura) | 4.5k | 2026-10-06 | Apache-2.0 | Main-text extraction | LEARN: clean "about" text for outreach openers |
| 23 | [harlan-zw/unlighthouse](https://github.com/harlan-zw/unlighthouse) | 4k | 2026-10-11 | MIT | Whole-site Lighthouse scan | LEARN: one-off client audits |
| 24 | [MultiPost-Extension](https://github.com/leaperone/MultiPost-Extension) | 3.5k | 2026-09-14 | (not checked) | Post to many socials from the browser | LEARN for b4 ideas |
| 25 | [frappe/crm](https://github.com/frappe/crm) | 3.3k | 2026-08-13 | **AGPL-3.0** | CRM | AVOID |
| 26 | [espocrm/espocrm](https://github.com/espocrm/espocrm) | 3.2k | 2026-08-13 | **AGPL-3.0** | CRM | AVOID |
| 27 | [eracle/OpenOutreach](https://github.com/eracle/OpenOutreach) | 3.1k | 2026-09-07 | (not checked) | AI LinkedIn outreach agent | **AVOID**: automates LinkedIn against its terms |
| 28 | [brightbean-studio](https://github.com/brightbeanxyz/brightbean-studio) | 2.4k | 2026-09-20 | **AGPL-3.0** | Social media scheduler | Separate service only |
| 29 | [Notifuse/notifuse](https://github.com/Notifuse/notifuse) | 2.2k | 2026-09-17 | **Mixed: AGPL part + BSL** | Newsletter + transactional email | AVOID (source-available parts) |
| 30 | [scrapinghub/extruct](https://github.com/scrapinghub/extruct) | 0.9k | 2026-09-27 | BSD-3 | JSON-LD / microdata / OpenGraph extraction | **ADOPT** (built below, with a caveat) |

Also seen: gitroomhq/postiz-app (AGPL-3.0, the best-known open social scheduler: separate service only), ChatbotX (MIT core plus an `enterprise` folder: check before reuse), StJudeWasHere/seonaut (MIT, Go SEO auditor: LEARN), Google-Maps scrapers (MIT, but scraping Maps breaks Google's terms and CLAUDE.md rule 4: **AVOID**).

## Tried it (13 Oct 2026)

Published packages only (PyPI `extruct==0.18.0`, npm `@lhci/cli@0.15`), in throwaway environments. No cloned repo code was executed.

**1. Lighthouse CI on the BotBhai SEO site (salon sample, 2 pages, desktop preset, the sandbox's Chromium).**

| | Accessibility | Best practices | SEO | Performance | color-contrast | errors-in-console |
|---|---|---|---|---|---|---|
| Before (white on `#25d366`, no favicon) | 0.90 | 0.96 | 1.00 | 1.00 | **fail** (1.98:1) | **fail** (favicon 404) |
| After (button `#0e7c4a`, `favicon.svg`) | **1.00** | **1.00** | 1.00 | 1.00 | pass (5.25:1) | pass |

With the new assertions, the old build fails CI and the new one passes, so the workflow catches this class of bug for good.

**2. extruct 0.18 (40 MB venv).** It reads microdata well (a `HealthClub` with email and phone). **Caveat found:** if one JSON-LD block on a page is malformed, `extruct.extract(..., errors="ignore")` returns **no JSON-LD at all**, silently losing the good blocks. Real small-business sites often have a broken plugin block next to a good one. So `enrich.py` now parses JSON-LD block by block with the standard library and uses extruct only for microdata (optional).

## What was built

| Item | Files | Check | Result |
|---|---|---|---|
| enrich.py + structured data | `botbhai/leadfinder/enrich.py`: `structured()` reads schema.org JSON-LD (`@graph`, `mailto:`, `sameAs` socials, `ReserveAction` / `acceptsReservations` = already has booking); schema email beats regex decoys; new `schema_type` and `phone` columns. Microdata via extruct when installed | `python3 leadfinder/test_enrich.py` (stdlib and extruct modes) | pass |
| SEO bot contrast + favicon | `botbhai/seo/seo_bot.py`: button `#0e7c4a`, `favicon.svg` + `<link rel="icon">` | `python3 seo/test_seo.py` computes WCAG ratios from the CSS (≥ 4.5) and checks the favicon | pass |
| Lighthouse CI | `.github/workflows/lighthouse.yml`, `botbhai/seo/lighthouserc.json`, `lh-config.json` | `lhci autorun` locally: all assertions pass; the old CSS fails | pass |

`bash 01-botbhai/botbhai/tools/test-all.sh` → ALL BOTBHAI TESTS PASSED.

## Concrete next changes (not built)

- b5: use changedetection.io (Apache-2.0) as a separate service to watch public deal pages, not scrape stores.
- A01b (restyle) should keep the new contrast test and Lighthouse gate green when moving seo_bot to Kalamkari tokens.
- Outreach openers: trafilatura "about" text → one personalised line per lead (needs an LLM step; keep it optional).

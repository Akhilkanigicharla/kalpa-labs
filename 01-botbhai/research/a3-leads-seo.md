# A3: Open-source tools for legal B2B lead-gen and local SEO

Research agent 3 of 8, 2026-10-13. Scope: crawlers and extractors, OSM/Overpass, enrichment, local-SEO tooling, GBP/Meta SDKs, outreach/CRM.

## Summary

BotBhai's `leadfinder/enrich.py` and `seo/seo_bot.py` are already well designed and legal, and don't need a framework. A few small permissive libraries fix their real gaps: **extruct** (BSD) reads a prospect's own schema.org JSON-LD, **Lighthouse CI** (Apache-2.0) checks the generated sites in GitHub Actions, and **Crawlee-python** (Apache-2.0) is the step up if we need multi-page crawls. Firecrawl, Twenty and listmonk are AGPL and Mautic is GPL-3, so we can only run them as separate services and must not copy their code into anything we sell. Google-Maps scrapers (for example gosom/google-maps-scraper) are MIT-licensed, but using them breaks Google's terms, so they are AVOID.

## Shortlist

Stars are approximate (the GitHub API is blocked here). Last commit and licence were checked with a shallow `git clone` of each repo's LICENSE file and HEAD.

| Repo | What | Stars ~ | Last commit | Licence | Fit 1–5 | Verdict | Why |
|---|---|---|---|---|---|---|---|
| [scrapinghub/extruct](https://github.com/scrapinghub/extruct) | Extracts JSON-LD, microdata and OpenGraph from HTML | 0.9k | 2026-09-27 | BSD-3 | 5 | **ADOPT** | Pulls `email`, `telephone`, `sameAs` (Instagram) and `@type` from a prospect's own schema, which is more reliable than regex. It can also check seo_bot's own output. Runs in 1 ms, pure Python, small install. |
| [GoogleChrome/lighthouse-ci](https://github.com/GoogleChrome/lighthouse-ci) | Lighthouse audits plus score assertions in CI | 6.5k | 2025-06-25 | Apache-2.0 | 5 | **ADOPT** | Free on GitHub Actions. Fails a build if SEO drops below 0.9. It found a real contrast bug in seo_bot (see "Tried it"). Releases are slow, but the project is stable. |
| [apify/crawlee-python](https://github.com/apify/crawlee-python) | Async crawler (BeautifulSoup/Playwright), queues, retries, robots.txt | 6k+ | 2026-10-12 | Apache-2.0 | 4 | **ADOPT (when needed)** | Lightweight install (65 MB venv, 5 s). Has `respect_robots_txt_file=True` built in. Use it when enrich needs to visit /contact pages at scale. |
| [scrapy/protego](https://github.com/scrapy/protego) | robots.txt parser (wildcards, Google spec) | <0.1k | 2026-10-08 | BSD-3 | 3 | LEARN | Gave the same results as stdlib `urllib.robotparser` on Python 3.13 in our test. Switch to it only if we hit edge cases. |
| [adbar/trafilatura](https://github.com/adbar/trafilatura) | Main-text and metadata extraction | 4.5k | 2026-10-06 | Apache-2.0 | 3 | LEARN | Gives clean "about" text for LLM-written personalised outreach openers. Installs 93 MB together with extruct and protego. |
| [JoshData/python-email-validator](https://github.com/JoshData/python-email-validator) | Email syntax/domain validation | 1.2k | 2026-10-01 | Unlicense (public domain) | 4 | **ADOPT** | Rejects junk such as `a@b` and reserved domains before outreach, which protects sender reputation. It did **not** reject `sentry@wixpress.com`, so keep enrich's `SKIP_EMAIL` blocklist. |
| [unclecode/crawl4ai](https://github.com/unclecode/crawl4ai) | LLM-friendly crawler (Playwright to Markdown) | 55k+ | 2026-10-11 | Apache-2.0 | 3 | LEARN | Works well and honours robots.txt (returns 403 "Access denied by robots.txt"). Too heavy for the low-spec PC: 832 MB venv plus a 114 MB browser. Only worth it in Actions/Colab for JS-heavy sites. |
| [harlan-zw/unlighthouse](https://github.com/harlan-zw/unlighthouse) | Whole-site Lighthouse scan from the sitemap | 4k | 2026-10-11 | MIT | 3 | LEARN | Good for a one-off client audit report (a sellable "SEO health check"). Lighthouse CI is enough for CI. |
| [google/schema-dts](https://github.com/google/schema-dts) | TypeScript types for schema.org | 1k | 2026-10-02 | Apache-2.0 | 2 | LEARN | Only useful if the site generator moves to TypeScript. |
| [AnswerDotAI/llms-txt](https://github.com/AnswerDotAI/llms-txt) | llms.txt spec and parser | 1.5k | 2026-09-25 | Apache-2.0 | 3 | LEARN | Our llms.txt is missing the spec's link-list sections (`- [Page](url): note`). |
| [towfiqi/serpbear](https://github.com/towfiqi/serpbear) | Self-hosted rank tracker (Google Search Console + SERP APIs) | 1.7k | 2026-05-14 | MIT | 3 | LEARN | Its Search Console integration is the free, allowed way to track rankings. Paid scraper APIs are not. |
| [eliasdabbas/advertools](https://github.com/eliasdabbas/advertools) | Sitemap/robots/crawl SEO analysis | 1.2k | 2026-06-30 | MIT | 2 | LEARN | Useful in Colab for audits. Duplicates what Lighthouse CI and extruct already do. |
| [DinoTools/python-overpy](https://github.com/DinoTools/python-overpy) | Overpass API wrapper | 0.25k | 2025-02-17 | MIT | 2 | LEARN | leadfinder.py's raw urllib plus endpoint fallback is already enough. The project is quiet. |
| [facebook/facebook-python-business-sdk](https://github.com/facebook/facebook-python-business-sdk) | Meta Marketing API SDK | 1.3k | 2026-09-17 | Custom Meta platform licence | 3 | LEARN (flag licence) | Permissive, but limited to use with Meta's platform. That is fine for client ads. Lead Ads webhooks are an opt-in lead source. |
| google-api-python-client (Business Profile APIs) | GBP posts, reviews and locations through discovery | n/a | 2026-09-30 (PyPI) | Apache-2.0 | 3 | LEARN | Automating `gbp_posts.csv` needs Google to approve API access (a quota request). Until then, posting stays manual. |
| [twentyhq/twenty](https://github.com/twentyhq/twenty) | Modern CRM | 35k | 2026-10-12 | AGPL-3.0 | 2 | AVOID copying | Self-host only as a separate service. Supabase plus a Google Sheet is cheaper at our scale. |
| [knadh/listmonk](https://github.com/knadh/listmonk) | Newsletter/mailing manager | 17k | 2026-10-11 | AGPL-3.0 | 2 | LEARN (separate service) | Usable for the b5 newsletter as a separate service. Not suitable for cold email. |
| [mautic/mautic](https://github.com/mautic/mautic) | Marketing automation | 8k | 2026-10-12 | GPL-3.0 | 1 | AVOID | Heavy PHP/MySQL stack, too much to host on free tiers. |
| [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl) | Crawl-to-Markdown API | 60k+ | 2026-10-12 | AGPL-3.0 | 1 | AVOID | AGPL plus heavy self-host. crawl4ai or Crawlee do the same job under Apache-2.0. |
| [gosom/google-maps-scraper](https://github.com/gosom/google-maps-scraper) | Google Maps scraper | 2k | 2026-09-24 | MIT | 0 | **AVOID** | Breaks Google Maps terms of service. enrich.py's header already forbids this. |

Other candidates screened: apify/crawlee (JS), scrapy, selectolax (MIT, fast parser), OSMPythonTools (GPL-3, avoid), Nominatim (GPL, use the public API only under its usage policy), matomo/plausible (GPL/AGPL analytics, separate service only), Lighthouse core.

## Tried it

All runs used fresh venvs in scratch. The test targets were two local `python3 -m http.server` instances only:

- `:8731` served a fake "Lotus Unisex Salon" prospect site: a homepage with JSON-LD, a `/contact/` page with a wa.me link, and robots.txt disallowing `/private/`.
- `:8732` served the site `seo_bot.py --setup salon` generated (31 pages).

No outside sites were contacted.

1. **extruct 0.18 + trafilatura 2.3.1 + protego 0.7 + email-validator 2.3**
   - Install: `pip install extruct trafilatura protego email-validator` took 62 s and the venv is 93 MB.
   - extruct parsed the prospect JSON-LD in **1 ms**: `@type=BeautySalon`, `email=hello@lotus-salon.test`, `sameAs=[instagram.com/lotus.salon.hyd]`.
   - Audited all **31 seo_bot pages: 0 with unexpected JSON-LD**. Every page has `BeautySalon` + `FAQPage`, and the index page has 6 offers and OpenGraph.
   - protego and stdlib robotparser agreed on all 3 test paths, including the wildcard `/*?sort=` rule.
   - email-validator rejected `a@b` and the reserved `.test` domain but accepted `sentry@wixpress.com`, so the regex blocklist is still needed.
   - trafilatura returned clean body text and the page title.
2. **Crawlee-python 1.10.4** (`pip install 'crawlee[beautifulsoup]'`, 5 s, 65 MB)
   - `BeautifulSoupCrawler(respect_robots_txt_file=True)` with `enqueue_links(strategy="same-domain")` crawled 2 pages in 0.64 s and **skipped `/private/`** as robots.txt requires.
   - It found `bookings@lotus-salon.test` and WhatsApp `919000000000` **on /contact/ only**. enrich.py fetches only the homepage, so it would have missed the WhatsApp link and scored the lead wrongly ("no WhatsApp", +5).
3. **crawl4ai 0.9.4** (`pip install crawl4ai` in 43 s, venv **832 MB**, plus `playwright install chromium` at 114 MB)
   - `CrawlerRunConfig(check_robots_txt=True)` with a custom UA crawled the homepage in 4.2 s, including browser start-up, and returned clean Markdown plus internal links.
   - `/private/admin.html` returned `success=False, 403, "Access denied by robots.txt"`.
4. **Lighthouse CI 0.15.1** (`npm i @lhci/cli`, 28 s; `CHROME_PATH=<playwright chromium> npx lhci autorun` with an SEO ≥ 0.9 assertion, 32 s for 2 URLs)
   - seo_bot pages scored **performance 1.0, SEO 1.0, best-practices 0.96, accessibility 0.90**.
   - Failing audits were `color-contrast` (white text on the `#25d366` WhatsApp button, about 2:1) and `errors-in-console` (most likely the missing `/favicon.ico` 404).

Clones, venvs and servers were deleted or stopped afterwards.

## Concrete changes for Kalpa Labs

- **`01-botbhai/botbhai/leadfinder/enrich.py`**:
  - Add optional `extruct` JSON-LD parsing in `extract()`. Prefer schema `email`, `telephone` and `sameAs` over regex, and record `has_schema=yes/no`. A business without schema is a prime SEO-upsell prospect, worth +5 in `rescore()`.
  - Also fetch at most 2 same-site pages linked as contact, book or about (still checked with `allowed()` and the 1 req/s rate limit). WhatsApp links often live only on /contact.
- **`01-botbhai/botbhai/leadfinder/enrich.py`**: run `email_validator.validate_email(e, check_deliverability=False)` on the chosen email before it is used for outreach. Keep `SKIP_EMAIL`.
- **`01-botbhai/botbhai/seo/seo_bot.py`**:
  - Darken the `.wa` button background, for example to `#0e7c4a` or `#128c4a`, so it passes WCAG contrast.
  - Emit a `favicon.svg` and add a `<link rel="icon">` tag.
  - Add a link list to `llms.txt` (`- [Hair spa in Madhapur](url): ₹… `) to follow the llms.txt spec.
- **`01-botbhai/botbhai/seo/test_seo.py`**: add an extruct-based test (when the library is installed) that checks every generated page has `LocalBusiness`-subtype plus `FAQPage` JSON-LD.
- **New `.github/workflows/seo-lighthouse.yml`** (beside the existing `.github/workflows/leadfinder.yml`): build a sample client, serve it with `python -m http.server`, and run `npx @lhci/cli@0.15.1 autorun` with `categories:seo ≥ 0.9` as an error and accessibility as a warning. This is free on Actions.
- **CRM/outreach**: don't self-host Twenty or Mautic. Keep leads in Supabase or a Sheet. If the b5 newsletter needs a mailer later, run listmonk only as a separate service (AGPL).

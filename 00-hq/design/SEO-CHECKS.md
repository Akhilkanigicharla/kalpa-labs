# Kalpa SEO checks: the 20 every public Kalpa page must pass

Akhil, 9 Nov 2026: "add them to whole Kalpa Labs". Source: the list in Josh Hoeg's reel "20 SEO checks for your vibecoded
website". Checks below are ours. Applies to every **public** page (our site, product landing pages, store/listing pages);
app screens behind a login use `noindex` instead and skip the rest.

**How to use it.** Run `python3 00-hq/site/tests/test_seo.py <site folder> <https://live-url>` (it checks 16 of the 20
automatically; works for any static site folder). Fill the 4 manual rows in that world's `design/seo-check.md`.
Before ticking a public page: the checker passes and the manual rows are filled.

| # | Check | Kalpa rule | Auto |
|---|---|---|---|
| 1 | sitemap.xml | Lists every public page with its full https URL and lastmod; linked from robots.txt. | ✅ |
| 2 | robots.txt | Allows the site, names the sitemap, blocks only private paths (functions, previews). | ✅ |
| 3 | No stray noindex | Public pages never carry `noindex`; private/app pages always do. | ✅ |
| 4 | Canonical tag | Each page has one `<link rel="canonical">` with its own full https URL. | ✅ |
| 5 | Meta title | 30–60 characters, says what it is and for whom ("… for Indian small businesses"). | ✅ |
| 6 | Meta description | 70–160 characters, plain words, one clear offer; never claims more than is built. | ✅ |
| 7 | One H1 | Exactly one `<h1>` per page. | ✅ |
| 8 | Heading order | No skipped levels (h2 → h4). | ✅ |
| 9 | Alt text | Every `<img>` has `alt` (empty `alt=""` only for decoration); inline SVG icons are `aria-hidden` or titled. | ✅ |
| 10 | Schema markup | JSON-LD that parses: Organization + WebSite on home; Product/Offer, FAQPage, Event, LocalBusiness where true. | ✅ |
| 11 | Internal links | Every `#anchor` and `/path` points at something that exists. | ✅ |
| 12 | No broken links | External links answer (the live check); bot-blocked sites are noted, not "fixed". | ✅ (live) |
| 13 | Compressed images | Images WebP/AVIF/PNG under 200 KB each, with width and height set; fonts self-hosted and cached. | ✅ |
| 14 | Core Web Vitals | Page weight small (< 300 KB HTML), no render-blocking third-party scripts; real numbers from PageSpeed when live. | ½ |
| 15 | Mobile layout | `viewport` meta + the 390 px tap sweep (`test_tap_sweep.py`) passes, light and dark. | ✅ |
| 16 | HTTPS everywhere | No `http://` links or assets; HTTPS redirect + HSTS header on the host. | ✅ |
| 17 | Clean URL slugs | Lowercase, hyphens, no `.html` in links we share, no query junk. | manual |
| 18 | og:image | og:title, og:description, og:url, og:image (1200×630, < 300 KB) + twitter:card, so WhatsApp/LinkedIn previews look right. | ✅ |
| 19 | Search Console | Site verified in Google Search Console and the sitemap submitted (Akhil's Google account, laptop). | manual |
| 20 | llms.txt | `/llms.txt` says in plain words what Kalpa offers, for whom, prices only if live, and links to key pages. | ✅ |

Manual rows for `design/seo-check.md`: 14 (PageSpeed mobile score once live), 17 (slugs), 19 (Search Console), and a
one-line note on the target search words (e.g. "WhatsApp bot for salons Hyderabad", "Telugu WhatsApp assistant").

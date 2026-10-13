# GitHub research A5: b3 Kits and b5 Deals

Agent 5 of 8 · 2026-10-13 · Discovery used WebSearch, GitHub topic pages via WebFetch, ecosyste.ms repo metadata (stars, last push and licence, because the GitHub API was blocked), PyPI/npm JSON, and shallow clones. All clones were deleted after use.

## Summary

The tax engine for b5 is ready to use. **india-tax-guru** (MIT, 247 tests passing) matched the official FY 2026-27 slabs on 3 test salaries, including the ₹12L 87A marginal-relief edge case. The more popular **taxcalcindia** gets that edge case wrong by ₹40,300. For b3 kits, the fastest legal path is to sell through a **Razorpay Payment Page** and then deliver a **per-buyer stamped PDF/Sheet link** made with pypdf (BSD-3). This took 0.16 s for a 60-page kit. **Open Payment Host** is the only self-hosted Gumroad alternative found with Razorpay built in, but it is AGPL, so run it unmodified as a separate service or learn from it. For b5 deals, Amazon's PA-API 5 is now deprecated and returns 403; the **Creators API** replaces it (MIT wrapper `python-amazon-paapi` 7.x supports the IN marketplace). EarnKaro has **no public API**, only its Magic Tool link converter and a bot set up by an account manager. So the Telegram deals channel should be grammY or aiogram (both MIT) plus Creators API data, with no scraping.

## Official slab source used (FY 2026-27 = tax year 2026-27 = AY 2027-28)

- **Finance Bill 2026 memorandum** ([indiabudget.gov.in/doc/memo.pdf](https://www.indiabudget.gov.in/doc/memo.pdf)) says there is **no change** in individual rates.
  - New regime (115BAC(1A)): 0–4L nil; 4–8L 5%; 8–12L 10%; 12–16L 15%; 16–20L 20%; 20–24L 25%; above 24L 30%.
  - Old-regime slabs for under-60s: 0–2.5L nil; 2.5–5L 5%; 5–10L 20%; above 10L 30%.
- **incometaxindia.gov.in** ([tax-rates-and-computation](https://www.incometaxindia.gov.in/w/tax-rates-and-computation)): the 87A rebate threshold is ₹12L **with marginal relief**, and the maximum rebate is ₹60,000.
- **Carried forward from Finance Act 2025 (not restated in the 2026 memo; re-verify before launch):**
  - Standard deduction: ₹75,000 (new regime) and ₹50,000 (old regime).
  - Old-regime 87A: ₹12,500 up to ₹5L.
  - Cess: 4%.
- Note: the Income-tax Act 2025 replaces the 1961 Act from 1 Apr 2026. Section numbers change (for example, 115BAC becomes s.202), so site copy should cite both.

## Candidates screened (29)

Telegram: python-telegram-bot, aiogram, grammY, Telegraf, pyTelegramBotAPI.
Sheets/Apps Script: google/clasp, gspread, labnol/code, tanaikech libs.
Quiz/question bank: Moodle, TCExam, H5P, text2qti, mockguru, ng2-quiz, devgaganin/mock-test-generator.
PDF: pypdf, pikepdf, pdf-lib (and the cantoo fork), PyMuPDF, pdfme.
Storefront/payments: Open Payment Host, HonorBox, mintkit, Polar, Hyperswitch, razorpay-node/python, Keygen, Medusa.
Tax/finance calculators: taxcalcindia, india-tax-guru, aikar, Taxly, drishit96/income-tax-calculator, siddhpant/extortion-tools, indian-financial-calculators, taxgyaan.
Static sites: Astro, Eleventy, Hugo.
Deals: python-amazon-paapi, PriceBuddy, Discount-Bandit.
Newsletter: listmonk, Plunk, Mautic.

## Shortlist

| Repo | What | Stars | Last commit | Licence | Fit | Verdict | Why |
|---|---|---|---|---|---|---|---|
| [anivar/india-tax-guru](https://github.com/anivar/india-tax-guru) | India tax engine: old vs new regime, HRA, capital gains, CLI `itg`, agent skill | small (new; PyPI 0.2.1) | 2026-08-08 | MIT | 5 | **ADOPT** | Matched official slabs on every test, including 87A marginal relief. 247 tests pass. Has AY 2026-27 rules. Can be the b5 calculator backend and the b3 "tax kit" checker. Next step: add a TY 2026-27 rules file (a copy, since slabs are unchanged). |
| [amrajacivil/taxcalcindia](https://github.com/amrajacivil/taxcalcindia) | Simpler Python tax calculator | small (PyPI 0.1.4) | 2026-01-25 | MIT | 2 | LEARN | Gets ₹13L gross wrong: it gives ₹66,300 where the correct figure is ₹26,000, because it has no 87A marginal relief. One slab set for all years. |
| [py-pdf/pypdf](https://github.com/py-pdf/pypdf) | Pure-Python PDF merge/stamp/encrypt | ~10.3k | 2026-10-09 | BSD-3 | 5 | **ADOPT** | Per-buyer watermark, metadata and owner password all worked. Pure Python, so it runs on GitHub Actions or a Supabase/Netlify function. |
| [Hopding/pdf-lib](https://github.com/Hopding/pdf-lib) | JS PDF editing in any runtime | ~8.7k | 2024-07-17 (stale; [cantoo fork](https://github.com/cantoo-scribe/pdf-lib) active 2026-09) | MIT | 4 | ADOPT (alt) | Use it if stamping runs in a Netlify/Cloudflare JS function. Prefer the maintained fork. |
| [abishekmuthian/open-payment-host](https://github.com/abishekmuthian/open-payment-host) | Self-hosted Gumroad alternative (Go + SQLite). Supports Stripe, PayPal, **Razorpay** and Square; buyers check out without logging in. | ~234 | 2026-09-29 | **AGPL-3.0** | 3 | LEARN / run unmodified | It is the only open-source store found with Razorpay built in. AGPL means it can only be run as a separate service, and it needs an always-on host (Railway button), which is not free. |
| [Honorboxx/honorbox](https://github.com/Honorboxx/honorbox) | Store from a GitHub repo and Stripe, no server | ~16 | 2026-07-28 | MIT | 2 | LEARN | Good serverless pattern (webhook, then grant access). It is Stripe-only, and Stripe is unsuitable for an Indian sole-proprietor retail flow. Copy the pattern with Razorpay webhooks. |
| [grammyjs/grammY](https://github.com/grammyjs/grammY) / [aiogram/aiogram](https://github.com/aiogram/aiogram) | Telegram bot frameworks (TS / Python async) | ~3.8k / ~5.9k | 2026-10 | MIT / MIT | 5 | **ADOPT** (pick one) | grammY runs on Deno, Supabase Edge or Cloudflare webhooks for free. aiogram fits the Python stack (pypdf, tax engine). Avoid copying python-telegram-bot (LGPL-3.0, fine only as an unmodified library) and pyTelegramBotAPI (GPL-2.0). |
| [sergioteula/python-amazon-paapi](https://github.com/sergioteula/python-amazon-paapi) | Amazon **Creators API** wrapper; country `IN` supported | ~287 | 2026-09-16 | MIT | 4 | ADOPT (once eligible) | PA-API 5 is deprecated and returns 403 ([Amazon notice](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/paapiv5-deprecation)). This is the allowed data source for deal posts. You need Associates (amazon.in) Creators API credentials first. |
| [withastro/astro](https://github.com/withastro/astro) | Static site generator | ~63k | 2026-10-10 | MIT | 5 | **ADOPT** | Calculator pages are prerendered at build time for SEO, then hydrated. The build took 26 s with a 158 MB node_modules, so run it in Codespaces or Actions, not on the low-RAM PC. Eleventy 3.1.6 (MIT) is a lighter alternative. |
| [google/clasp](https://github.com/google/clasp) + [burnash/gspread](https://github.com/burnash/gspread) | Apps Script from git / Sheets via Python | ~5.9k / ~7.5k | 2026-08 / 2026-07 | Apache-2.0 / MIT | 4 | ADOPT | Version the kit's Apps Script with clasp and generate per-buyer Sheet copies with gspread. [labnol/code](https://github.com/labnol/code) (MIT) has snippets to learn from. |
| [knadh/listmonk](https://github.com/knadh/listmonk) | Self-hosted newsletter | ~23.7k | 2026-10-03 | AGPL-3.0 | 2 | LEARN / later | AGPL is fine if run unmodified as a separate service. It needs Postgres plus an always-on binary plus SMTP, so it is not free-tier friendly now. Start on a hosted free tier and move later. |
| [gpoore/text2qti](https://github.com/gpoore/text2qti) | Markdown to QTI quiz format | ~239 | 2024-08-12 | BSD-3 | 3 | LEARN | Good model for a plain-text question-bank format: write questions once and export them to Sheets, Telegram quiz polls, and PDF. Moodle, TCExam (AGPL) and H5P (GPL) are AVOID for copying. |

Also AVOID: **PyMuPDF** (AGPL); **Taxly** (Business Source License, not open source); **Keygen** (Fair Core License); **Discount-Bandit** (no licence, and it scrapes); **PriceBuddy** (custom licence described as "GPL-3.0 with modifications", scrapes); **mockguru** and **drishit96 tax calculator** (GPL-3.0).

## Tried it

All runs were in a scratch venv or folder. No sudo and no secrets were used. Clones were deleted afterwards.

**1. Tax engines compared with the official slabs.** Each salary was split 50/50 basic/special, with ₹1.5L 80C (old regime only). Setup was `pip install ./taxcalcindia ./india-tax-guru[cli]`, then `itg compare p<gross>.json` and a 6-line script for taxcalcindia.

| Gross salary | Hand calculation from cited slabs (new / old) | india-tax-guru | taxcalcindia |
|---|---|---|---|
| ₹12,75,000 (taxable 12.00L / 10.75L) | 0 (rebate ₹60k) / ₹1,40,400 | 0 / 1,40,400 ✅ | 0 / 1,40,400 ✅ |
| ₹13,00,000 (taxable 12.25L / 11.00L) | **₹26,000** (marginal relief) / ₹1,48,200 | 26,000 / 1,48,200 ✅ | **66,300 ❌** / 1,48,200 |
| ₹25,00,000 (taxable 24.25L / 23.00L) | ₹3,19,800 / ₹5,22,600 | 3,19,800 / 5,22,600 ✅ | 3,19,800 / 5,22,600 ✅ |

`pytest`: india-tax-guru **247 passed in 0.38 s**; taxcalcindia **9 passed**, but none of its tests cover marginal relief.

**2. Per-buyer PDF stamping (pypdf 6.20.1 + reportlab 5.0.1, both BSD).**
- Generated a 60-page sample kit.
- On every page, stamped a footer reading "Licensed to {name} <{email}> | Order {id}" plus a faint diagonal email.
- Wrote the order id into the PDF metadata and encrypted it with an owner password (print-only).
- Result: **0.164 s**. The output had 60 pages; the footer text was found on page 60; metadata read `order:ORD123`; `is_encrypted=True`. File size went from 28 KB to 62 KB.

**3. Astro 7.3.8 calculator site build.**
- Minimal project: one page plus `fin.js` with SIP, EMI and new-regime tax (₹75k standard deduction, 87A with marginal relief, 4% cess).
- `npm install && npx astro build` took **26 s** wall time and produced an 8 KB `dist`. Prerendered output:
  - SIP ₹5,000/month @12% for 10 years: ₹11,61,695 (same as the standard annuity-due formula used by Groww and others).
  - EMI on ₹20L @8.5% for 240 months: ₹17,356.
  - Tax at ₹13L gross: ₹26,000. Tax at ₹25L gross: ₹3,19,800. Both match the official-slab hand calculation.

Not run: the grammY and aiogram bots, because they need a BotFather token (a secret). Open Payment Host and listmonk were not run because they need always-on servers and Razorpay keys.

## Concrete next quests for b3 and b5

1. **b5 · Tax page v1.** Build an Astro site on Netlify free. Port the india-tax-guru logic (MIT, keep the attribution) or call it at build time. Add test fixtures for ₹12.75L, ₹13L and ₹25L so a slab change breaks CI. Show "Finance Bill 2026: rates unchanged" with source links.
2. **b5 · SIP/EMI/FD pages.** Reuse `fin.js` and add Telugu copy and FAQ schema. That gives 4 pages from one template.
3. **b3 · Delivery pipeline.** Razorpay Payment Page sends a webhook to a Supabase Edge Function or GitHub Actions job. That job stamps the PDF with pypdf (or pdf-lib), copies the Sheet with gspread, and emails a signed expiring link. Learn the order and file-access flow from the Open Payment Host source; do not copy its AGPL code.
4. **b3 · Question-bank format.** Define a plain-text or CSV MCQ schema (question, 4 options, answer, explanation, topic, source year), modelled on text2qti/GIFT. Export it to (a) a Google Sheets self-test kit with an Apps Script score sheet versioned by clasp, and (b) Telegram quiz polls.
5. **b5 · Telugu deals bot.** Build it with grammY on a free webhook host, posting deals from the Creators API (`python-amazon-paapi` 7.x, country `IN`). Apply for Amazon.in Associates and Creators API credentials first. Use EarnKaro only through its Magic Tool or account-manager bot, with no scraping. Add an affiliate disclosure line to every post.
6. **b5 · Newsletter.** Start on a hosted free tier. Revisit self-hosted listmonk (AGPL, unmodified, separate service) when there are more than ~1k subscribers and a cheap always-on box is justified.

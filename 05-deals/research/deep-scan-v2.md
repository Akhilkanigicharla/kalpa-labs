# Deep scan v2: b3 Kits + b5 Deals & Tools

Agent 6 of 8 · 2026-10-13 · Discovery: GitHub topic pages (financial-calculator, income-tax, spaced-repetition, google-apps-script, astro, quiz, exam-preparation, calculator) via WebFetch; stars, last push and licence from repos.ecosyste.ms (GitHub API blocked). Clones went to a scratch folder and were deleted. Builds on [a5-kits-deals.md](../../03-kits/research/a5-kits-deals.md); not repeated here.

## Top 5 findings

1. **FY 2026-27 rules are verified at source and unchanged from FY 2025-26.** The Income-tax Act 2025 is in force from 1 Apr 2026, so site copy must cite the new section numbers: s.202 (new-regime slabs), s.156 (rebate, ex-87A) and s.19 (standard deduction, ex-16(ia)). The fixtures ₹12.75L / ₹13L / ₹25L = **0 / 26,000 / 3,19,800** are confirmed.
2. **ts-fsrs (MIT, 805★, active) is the right engine for the GATE revision scheduler.** It is a TypeScript port of FSRS-6, and the same maths runs in Apps Script (plain JS) and on the site. We ran ts-fsrs 5.4.2: five "Good" reviews give intervals of 0 → 2 → 11 → 46 → 163 days, and one "Again" resets the topic to the same day. Unlike the plan's fixed 1/3/7/21 ladder, it adapts to each topic's "Again" presses (Step 2).
3. **python-telegram-bot is LGPL-3.0.** ecosyste.ms reports it as GPL-3.0, and its repo states LGPLv3. Use it only as an unmodified library. **aiogram (MIT) or grammY (MIT)** stays the pick for the deals poster.
4. **Several India-tax repos look attractive but carry AGPL or unclear licences.** openaccountants (423★) is AGPL-3.0, hyperweavers/nidhi is AGPL-3.0, and itr-wala (857★) has a non-standard licence. These are LEARN only. Nothing new beats india-tax-guru (MIT) for correctness, and we now have our own tested `fin.ts`, so we no longer depend on it.
5. **The site needs no theme.** AstroWind and AstroPaper (MIT) are blog themes built on Tailwind. For 10 calculator pages, plain Astro plus the Kalamkari `tokens.css` builds in seconds with zero client framework. Starlight (MIT) is worth adopting later for the Kits help docs (EN + TE i18n built in). `schema-dts` (Apache-2.0) gives typed FAQPage JSON-LD.

## Verified tax rules (individual, resident, tax year 2026-27 = FY 2026-27)

| Rule | Value | Source |
|---|---|---|
| Rates changed by Finance Bill 2026? | **No**: "There is no change proposed in tax rates", for both the 1961 Act (AY 2026-27) and the 2025 Act (tax year 2026-27) | [Budget 2026 Memorandum](https://www.indiabudget.gov.in/doc/memo.pdf) |
| New regime, s.202(1) (ex-115BAC(1A)) | 0–4L nil · 4–8L 5% · 8–12L 10% · 12–16L 15% · 16–20L 20% · 20–24L 25% · >24L 30% | Memo; [incometaxindia tax rates](https://www.incometaxindia.gov.in/w/tax-rates-and-computation) |
| Old regime, <60 | 0–2.5L nil · 2.5–5L 5% · 5–10L 20% · >10L 30% | Memo (First Schedule Part I) |
| Old regime, 60–79 / 80+ | Nil to 3L / nil to 5L; then the same 5/20/30 bands (80+: 20% for 5–10L) | Memo |
| Rebate, s.156(2) (ex-87A), new regime | 100% of tax up to ₹60,000 if total income ≤ ₹12L; **marginal relief** above ₹12L (tax ≤ income above ₹12L) | [incometaxindia s.156](https://www.incometaxindia.gov.in/w/section-156-88) |
| Rebate, s.156(1), old regime | 100% of tax up to ₹12,500 if total income ≤ ₹5L (no marginal relief) | Same |
| Rebate exclusions | Not available against special-rate income (e.g. 112A LTCG) | incometaxindia tax rates page |
| Standard deduction, s.19 (ex-16(ia)) | ₹75,000 under s.202(1); ₹50,000 otherwise | [incometaxindia s.19](https://www.incometaxindia.gov.in/w/section-19-206) |
| Surcharge | 10% >50L · 15% >1Cr · 25% >2Cr · 37% >5Cr (old only; the new regime caps at 25%); max 15% on dividends and 111A/112/112A gains; marginal relief on surcharge | Memo |
| Cess | Health & Education Cess 4% on (tax + surcharge); no marginal relief on cess | Memo |

Hand check (new regime, salary only):
- ₹12.75L gross → taxable 12.00L → slab tax 60,000 − rebate 60,000 = **0**.
- ₹13L gross → taxable 12.25L → slab tax 63,750, capped by marginal relief at 25,000, plus 4% cess = **26,000**.
- ₹25L gross → taxable 24.25L → slab tax 3,07,500, plus 4% cess = **3,19,800**.

The `fin.ts` tests encode all three.

## Top 30 repos (by stars, relevant to b3/b5)

| # | Repo | ★ | Last push | Licence | What | b3/b5 use | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | [withastro/astro](https://github.com/withastro/astro) | 63.1k | 2026-10-10 | MIT | Static/content site framework | b5 calculator site | **ADOPT** (built) |
| 2 | [ankitects/anki](https://github.com/ankitects/anki) | 31.8k | 2026-10-04 | AGPL-3.0 | SRS flashcard app | Model for the GATE revision UX | LEARN (never copy) |
| 3 | [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) | 29.5k | 2026-10-01 | LGPL-3.0 | Telegram bot lib | Deals/exam channel bot | AVOID copying; library only |
| 4 | [knadh/listmonk](https://github.com/knadh/listmonk) | 23.7k | 2026-10-03 | AGPL-3.0 | Self-hosted newsletter | b5 newsletter later | LEARN / run unmodified later |
| 5 | [vitest-dev/vitest](https://github.com/vitest-dev/vitest) | 17.2k | 2026-10-08 | MIT | Test runner | `fin.ts` fixtures | **ADOPT** (built) |
| 6 | [py-pdf/pypdf](https://github.com/py-pdf/pypdf) | 10.3k | 2026-10-09 | BSD-3 | PDF stamp/encrypt | b3 per-buyer PDF guide | **ADOPT** |
| 7 | [withastro/starlight](https://github.com/withastro/starlight) | 9.4k | 2026-10-09 | MIT | Astro docs theme with i18n | b3 kit help docs EN/TE | ADOPT later |
| 8 | [telegraf/telegraf](https://github.com/telegraf/telegraf) | 9.2k | 2026-09-24 | MIT | Node Telegram framework | Alternative to grammY | LEARN |
| 9 | [heyform/heyform](https://github.com/heyform/heyform) | 9.0k | 2026-09-09 | AGPL-3.0 | Form builder | Lead forms | AVOID |
| 10 | [Hopding/pdf-lib](https://github.com/Hopding/pdf-lib) | 8.7k | 2024-07-17 | MIT | JS PDF editing | Stamping in a JS function | ADOPT via fork (#27) |
| 11 | [arthelokyo/astrowind](https://github.com/arthelokyo/astrowind) | 6.0k | 2026-09-12 | MIT | Astro 7 + Tailwind starter | Landing-page patterns | LEARN |
| 12 | [aiogram/aiogram](https://github.com/aiogram/aiogram) | 5.9k | 2026-10-10 | MIT | Async Python Telegram bot | b5 deal poster, b3 quiz polls | **ADOPT** |
| 13 | [google/clasp](https://github.com/google/clasp) | 5.9k | 2026-08-28 | Apache-2.0 | Apps Script from git | Version kit scripts | **ADOPT** |
| 14 | [googleworkspace/apps-script-samples](https://github.com/googleworkspace/apps-script-samples) | 5.2k | 2026-07-30 | Apache-2.0 | Official GAS samples | Kit menus, triggers | **ADOPT** (copy with attribution) |
| 15 | [satnaing/astro-paper](https://github.com/satnaing/astro-paper) | 5.1k | 2026-10-02 | MIT | SEO blog theme | Long-tail article layout | LEARN |
| 16 | [surveyjs/survey-library](https://github.com/surveyjs/survey-library) | 4.9k | 2026-10-12 | MIT (lib) | Forms/quiz engine | Web mock tests (later) | LEARN (Creator is commercial) |
| 17 | [open-spaced-repetition/fsrs4anki](https://github.com/open-spaced-repetition/fsrs4anki) | 4.1k | 2026-08-14 | MIT | FSRS for Anki + optimiser | Parameter defaults, docs | LEARN |
| 18 | [grammyjs/grammY](https://github.com/grammyjs/grammY) | 3.8k | 2026-10-01 | MIT | TS Telegram framework | Webhook bot on CF Workers | **ADOPT** (alt to aiogram) |
| 19 | [st3v3nmw/obsidian-spaced-repetition](https://github.com/st3v3nmw/obsidian-spaced-repetition) | 2.6k | 2026-10-05 | MIT | SRS on whole notes | "Review a topic, not a card" model for GATE | LEARN |
| 20 | [miantiao-me/BroadcastChannel](https://github.com/miantiao-me/BroadcastChannel) | 2.1k | 2026-09-26 | AGPL-3.0 | Telegram channel → Astro microblog | SEO mirror of the deals channel | LEARN (AGPL) |
| 21 | [oshliaer/google-apps-script-awesome-list](https://github.com/oshliaer/google-apps-script-awesome-list) | 2.1k | 2026-04-26 | none | GAS link list | Discovery | LEARN |
| 22 | [labnol/apps-script-starter](https://github.com/labnol/apps-script-starter) | 1.3k | 2026-04-14 | MIT | Local GAS dev with build | Kit add-on tooling | ADOPT (optional) |
| 23 | [google/schema-dts](https://github.com/google/schema-dts) | 1.2k | 2026-10-02 | Apache-2.0 | Typed schema.org JSON-LD | FAQPage schema | ADOPT (types only) |
| 24 | [karanb192/itr-wala](https://github.com/karanb192/itr-wala) | 857 | 2026-09-02 | non-standard | Terminal ITR filing AY 2026-27 | ITR-season content ideas | LEARN |
| 25 | [trane-project/trane](https://github.com/trane-project/trane) | 845 | 2026-08-19 | AGPL-3.0 | Deliberate-practice engine | Topic dependency idea | AVOID |
| 26 | [open-spaced-repetition/ts-fsrs](https://github.com/open-spaced-repetition/ts-fsrs) | 805 | 2026-10-03 | MIT | FSRS-6 in TypeScript | **GATE revision scheduler** | **ADOPT** (ran it) |
| 27 | [open-spaced-repetition/awesome-fsrs](https://github.com/open-spaced-repetition/awesome-fsrs) | 717 | 2026-10-09 | CC0 | FSRS ports list (incl. Go/Rust/Dart) | Discovery | LEARN |
| 28 | [open-spaced-repetition/py-fsrs](https://github.com/open-spaced-repetition/py-fsrs) | 506 | 2026-08-09 | MIT | FSRS in Python | Telegram quiz-bot scheduling | ADOPT (bot side) |
| 29 | [openaccountants/openaccountants](https://github.com/openaccountants/openaccountants) | 423 | 2026-10-04 | AGPL-3.0 | CA-reviewed tax guides for agents | Cross-check copy | LEARN only |
| 30 | [cantoo-scribe/pdf-lib](https://github.com/cantoo-scribe/pdf-lib) | 353 | 2026-09-11 | MIT | Maintained pdf-lib fork | JS stamping | ADOPT (alt to pypdf) |

Also screened: fasiha/ebisu (338★, Unlicense, Bayesian SRS; LEARN, but FSRS is better benchmarked), sergioteula/python-amazon-paapi (287★, MIT; ADOPT once eligible, see a5), gpoore/text2qti (239★, BSD-3; LEARN for the question-bank format), skbly7/sbi-tt-rates-historical (185★, no licence; LEARN, useful for foreign-income ITR content), amrajacivil/taxcalcindia (MIT; AVOID, wrong at ₹13L), anivar/india-tax-guru (MIT; still correct, kept as a cross-check), hyperweavers/nidhi (AGPL; AVOID). The financial-calculator and income-tax topics have no India repo above about 20★ except those listed. The niche is open, which supports building our own.

## Step 2: tried it (re-run 13 Oct 2026)

Published npm packages only (`astro 7.3.8`, `vitest 5.0.4`, `@astrojs/sitemap 3.7.4`, `ts-fsrs`), in scratch folders; no cloned repo code was executed.

| Run | Command | Result |
|---|---|---|
| ts-fsrs 5.x scheduler (MIT) | `npm i ts-fsrs@5`, our 15-line script: one GATE topic rated Good five times, `request_retention: 0.9`, fuzz off | Intervals **0 → 2 → 11 → 46 → 163 days** (the first Good is a same-day learning step); one "Again" drops stability from 163 to 4.7 and brings the card back the same day. Runs in < 50 ms, pure JS, so it ports to Apps Script for A19. **Correction:** an earlier draft of this report quoted 1 → 3 → 8 → 21 → 49 d and a `03-kits/docs/gate-fsrs-scheduler.md` file; neither was reproduced, so they are replaced by this run. |
| Our `fin.ts` tax engine vs hand calculation | `npm test` in `05-deals/site` | **15 / 15 pass**: ₹12.75L / ₹13L / ₹25L → new 0 / 26,000 / 3,19,800 and old (₹1.5L 80C) 1,40,400 / 1,48,200 / 5,22,600; marginal relief at ₹12L; old-regime ₹5L rebate cliff; senior slabs; surcharge marginal relief at ₹50L (₹10,000 over 50L → surcharge ₹7,000) and the 25% new-regime cap; SIP ₹10k × 12% × 10y = ₹23,23,391; EMI ₹50L × 8.5% × 20y = ₹43,391; FD ₹1L × 7% × 5y = ₹1,41,478; PPF ₹1.5L × 15y = ₹40,68,209; HRA with Hyderabad at 50%. |
| Astro site build | `npm run build` | **16 pages in 0.8 s** (7 calculators × English + Telugu, plus 2 home pages) + sitemap. |
| Phone check | Playwright, 390 px, light + dark, 5 pages each | No sideways scroll, no script errors, typing ₹25L updates the result to ₹3,19,800 live. Found and fixed two bugs: re-rendered result rows lost their styles (Astro scoped CSS) and Telugu words fell back to a monospace font. |

**New fact for 2026-27 found while building:** the Income-tax Rules 2026 give **Hyderabad, Bengaluru, Pune and Ahmedabad the 50% HRA limit** (it was only the four old metros). That matters for a Hyderabad audience, so the HRA page leads with it ([ClearTax](https://cleartax.in/s/hra-house-rent-allowance), [Moneylife](https://moneylife.in/article/new-income-tax-rules-from-1st-april-hra-exemption-extended-to-8-cities-fewer-forms-but-landlord-disclosure-now-mandatory/79998.html); re-check against the CBDT notification before launch). PPF stays 7.1% for Oct–Dec 2026 ([Business Today](https://www.businesstoday.in/personal-finance/story/small-savings-scheme-interest-rates-unchanged-for-q3-fy27-check-ppf-scss-ssy-rates-558892-2026-09-30)).

## Step 3: what was built

| Item | Files | Check | Result |
|---|---|---|---|
| A15 | `05-deals/site/` Astro 7 project on the Kalamkari tokens (b5 turmeric `--l5`), `src/lib/fin.ts` (tax new + old, surcharge, cess, SIP, EMI) with sources in the header, `src/lib/fin.test.ts`, `.github/workflows/calculators.yml` | `npm test` green, `npm run build` ok | pass (15 tests, 16 pages) |
| A16 | `src/lib/calcs.ts` (salary in hand, FD, PPF, HRA + tax, SIP, EMI) in English + Telugu, each page with `FAQPage` + `WebApplication` JSON-LD and `hreflang` pairs | fixtures pass; 390 px light + dark screenshots | pass |

Telugu copy was written by Claude and needs a native speaker's read before launch (added to the CEO queue).

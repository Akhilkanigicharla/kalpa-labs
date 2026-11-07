# Elephant-Goldfish plan reviews: triage (A169)

Reviews K036–K043 (free models, 7 Nov 2026) read only the PLAN.md files. Each finding was checked against the real code on 7 Nov by Claude.
Verdicts: FALSE (already handled in code), TRUE (real; fixed or new item), COVERED (existing roadmap item), WONTFIX (opinion, with reason), REJECTED (breaks a rule), CHECK-AT-DEPTH (rechecked by that world's drift report), MINOR-DOC / ACCEPT.

| Finding | World | Severity | Verdict | Evidence / action |
|---|---|---|---|---|
| K036.1 | 00-hq | Blocker | FALSE | `WORLD_SHARE` lives in `00-hq/agents/registry.js:18`; Claude edits it after Akhil's yes (Kingdom shows it). |
| K036.2 | 00-hq | Blocker | FALSE | `A()` is defined in the same file, `registry.js:26`; no import needed. |
| K036.3 | 00-hq | Major | WONTFIX | Agent split is tested (`run.test.js`) and only costs a registry line each; merging gives no saving. |
| K036.4 | 00-hq | Major | TRUE→Akhil | The 12 opt-in closed-beta testers for the Play Store need a channel only Akhil can pick (friends/family opt-in). Asked in the summary. |
| K036.5 | 00-hq | Major | FALSE | Same as K036.1. |
| K036.6 | 00-hq | Minor | WONTFIX | `hq.freetier` is a cheap check; weekly-only would miss quota cliffs. |
| K036.7 | 00-hq | Minor | MINOR-DOC | Path added when Demo Builder ships (no code yet). |
| K036.8 | 00-hq | Minor | WONTFIX | 12-month view is the CEO's money plan; rolling 3 months shown inside it. |
| K036.9 | 00-hq | Minor | MINOR-DOC | Invoices are made by each world's billing code; no shared folder needed. |
| K036.10 | 00-hq | Minor | FALSE | `07-trading/src/gate.py` exists. |
| K037.1 | 01-botbhai | Blocker | TRUE | Plivo ₹0.38/min is provider-page-only (facts.md, 23 Oct). Marked 'single source, recheck before P1-M3-07' in `01-botbhai/PLAN.md`. |
| K037.2 | 01-botbhai | Major | TRUE | Exam kits (JEE etc.) can reach under-18 buyers; DPDP needs verifiable parent consent for children. New A175. |
| K037.3 | 01-botbhai | Major | FALSE | `human_until` expiry is built (`core/functions/inbox.js`, `supabase/schema.sql`). |
| K037.4 | 01-botbhai | Minor | TRUE-MINOR | WhatsApp rates already carry source + date in the plan; third-party figures stay labelled unverified. |
| K037.5 | 01-botbhai | Minor | CHECK-AT-DEPTH | Payload contracts are covered by BotBhai tests; recheck in A87 depth drift report. |
| K038.1 | 02-jobcard | Blocker | FALSE | Bill PDF is built with expo-print (`02-jobcard/src/src/lib/jobcard/share.ts`). |
| K038.2 | 02-jobcard | Major | WONTFIX | The 'My customers' web app is already built (`02-jobcard/web/`) and tested. |
| K038.3 | 02-jobcard | Major | TRUE | Web login uses Supabase phone OTP (`web/logic.mjs:47`), which needs an SMS provider that usually costs money. New A174: verify cost and pick the cheapest legal route. |
| K038.4 | 02-jobcard | Minor | FALSE | `next_invoice_no()` per-shop FY series with tests (`02-jobcard/supabase/test.sql`). |
| K038.5 | 02-jobcard | Minor | WONTFIX | Agent roles are registry lines, not separate services. |
| K039.1 | 03-kits | Major | WONTFIX | Same as K038.5. |
| K039.2 | 03-kits | Major | FALSE | Redirect-only delivery can be faked; the built webhook verifies Razorpay's HMAC on the raw body (`05-deals/site/src/lib/delivery.ts`). |
| K039.3 | 03-kits | Major | REJECTED | Narrowing to GATE only breaks rule 0 (no narrowing without Akhil's yes); Akhil chose TS/AP + teachers + banks + central first (C62). |
| K039.4 | 03-kits | Minor | WONTFIX | Telegram exam-date alerts are Akhil's ask (A163). |
| K039.5 | 03-kits | Major | FALSE | Delivery runs on Cloudflare Pages Functions, not Deno; plan wording is old. |
| K039.6 | 03-kits | Major | FALSE | Signature + payload handling is in `delivery.ts` with `delivery.test.ts`. |
| K039.7 | 03-kits | Minor | CHECK-AT-DEPTH | Kit formula tests exist (`03-kits/exam-kits/test_build.py`, LibreOffice recalc); tax kit gets the same at A89. |
| K039.8 | 03-kits | Minor | ACCEPT | Manual monthly Razorpay export is fine at our size. |
| K040.1 | 04-extensions | Blocker | COVERED | A53 already requires a *signed* licence before trusting Pro, which is what stops local tampering. |
| K040.2 | 04-extensions | Major | WONTFIX | Drive backup is a promised Pro feature; local export already exists for free users. |
| K040.3 | 04-extensions | Major | FALSE | Session schema is typed in `04-extensions/src/lib/store.ts`. |
| K040.4 | 04-extensions | Major | FALSE | Importers skip bad lines and count them (`lib/importers.ts`), with tests in `lifeboat.test.ts`. |
| K040.5 | 04-extensions | Minor | WONTFIX | Same as K038.5. |
| K041.1 | 05-deals | Blocker | FALSE | Formulas live in `05-deals/site/src/lib/fin.ts` and `calcs.ts`. |
| K041.2 | 05-deals | Major | CHECK-AT-DEPTH | Post scheduler file format recheck in A91 depth. |
| K041.3 | 05-deals | Major | CHECK-AT-DEPTH | Newsletter form method recheck in A91 depth. |
| K041.4 | 05-deals | Major | WONTFIX | Same as K038.5. |
| K042.1 | 06-finops | Blocker | FALSE | The Worker (`api/ingest.js`) only stores events; pricing runs in Python separately (`api/price_pass.py`). |
| K042.2 | 06-finops | Major | WONTFIX | OSCAL export is part of the Scale offer Akhil approved (A150); built last. |
| K042.3 | 06-finops | Major | TRUE-MINOR | `pii-scan.yml` is still a draft in `06-finops/.github-workflow-drafts/`; moves to `.github/workflows/` when F-15 ships (noted in PLAN). |
| K042.4 | 06-finops | Major | FALSE | Keys are stored as SHA-256 hashes (`06-finops/src/db/migrations/0002_api_key.sql`), Bearer header documented. |
| K042.5 | 06-finops | Minor | FALSE | Agents already live in `registry.js`. |
| K043.1 | 07-trading | Blocker | FALSE | `pbo_cscv` is tested: skilled set < 0.1, pure noise 0.25–0.75 (`07-trading/tests/test_lab.py`). |
| K043.2 | 07-trading | Major | FALSE | `data.py` uses yfinance; jugaad-data appears only in research notes. |
| K043.3 | 07-trading | Major | WONTFIX | Pinned versions keep backtests reproducible. |
| K043.4 | 07-trading | Minor | WONTFIX | Plan already allows paper → micro-live (matches Akhil, 6 Nov); L2 costs inform that step. |

**Totals (46 findings):** FALSE 18, WONTFIX 13, TRUE 4, CHECK-AT-DEPTH 4, MINOR-DOC 2, TRUE-MINOR 2, REJECTED 1, ACCEPT 1, COVERED 1

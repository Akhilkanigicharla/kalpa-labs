# Deep scan v2: JobCard (b2) open-source stack, Indian invoice rules, first build

Deep-Scan Agent 5 of 8, 13 Oct 2026. This builds on [a4-jobcard.md](a4-jobcard.md) and does not repeat its trials.

**How the data was gathered:**
- **Discovery:** GitHub topic pages sorted by stars: `expo`, `react-native-template`, `invoice` (pages 1–2), `invoicing`, `field-service-management`, `offline-first`, `local-first` and `speech-to-text` (pages 1–2), plus the awesome-local-first list.
- **Licences and last commits:** taken from a `git clone --depth 1 --filter=blob:none` of each repo, reading the LICENSE file and `git log -1`.
- **Package versions:** checked with `npm view` on 13 Oct 2026.
- **Star counts:** copied from the topic pages, so they are about ±5%. A dash means the repo wasn't on any topic page we read.

## Top findings

1. **No open-source invoice app is safe to copy except InvoicePlane (MIT) and Invio (Unlicense).**
   - AGPL: Invoice Ninja's mobile and admin apps aside, the server is **Elastic License 2.0**. Akaunting is **BSL**. IDURAR, InvoiceShelf, Crater, frappe/books, Bigcapital, invoicerr, easy-invoice-pdf and Triplit are all **AGPL**. Dolibarr is **GPL**.
   - Write our own invoice code; read these only for their data models.
2. **Write the invoice PDF in pure JS with pdf-lib, not through `expo-print` HTML.**
   - The same function then runs in the app, in a Supabase Edge Function (for the WhatsApp bot, b2.q09) and in Node tests. It needs no WebView or Chromium and gives byte-for-byte reproducible PDFs.
   - **Telugu needs real shaping.** pdf-lib + fontkit drop or misplace Telugu conjuncts, so we shape with **harfbuzzjs** (MIT, WASM) and draw the glyph outlines. See "Built" below for what we actually saw.
3. **The local Postgres 16 server already on this box works for RLS tests.** It is faster and more faithful than PGlite for Supabase-style `auth.uid()` policies. PGlite 0.5.9 (Apache-2.0) is the in-browser and Actions fallback.
4. **Starters:**
   - **Obytes** (4.4k★, MIT) is still the best template, but it is pinned to Expo SDK 54 and Expo is now at **57.0.28**.
   - **create-expo-stack** (2.6k★, MIT, 2026-09-15) is the strongest alternative. It generates a project at the current SDK with a choice of NativeWind (as our design system asks) and Supabase.
   - **react-native-reusables** (8.5k★, MIT) is shadcn/ui for React Native, which matches the design system's shadcn choice.
5. **HVAC field-service reference:** **clawnify/open-fieldservice** (MIT, 2026-10-06) is a small HVAC/pest-control job app with customers, technicians, *assets* (equipment history), recurring jobs and invoices. Its schema is MIT, so we can borrow ideas freely. That is where `appliance` plus `next_service_date` in our schema come from.

## Top 30 repos by stars (relevant to JobCard)

Verdicts: **ADOPT** (use it), **LEARN** (read it, don't depend on it), **AVOID** (licence or fit).

| # | Repo | ★ | Last commit | Licence | What | Verdict |
|---|---|---|---|---|---|---|
| 1 | [ggml-org/whisper.cpp](https://github.com/ggml-org/whisper.cpp) | 52.9k | 2026-10-12 | MIT | On-device Whisper | LEARN. A4 showed it fails on Telugu; English/Hinglish fallback only |
| 2 | [expo/expo](https://github.com/expo/expo) | 50.7k | 2026-10-12 (npm) | MIT | App framework: print, sqlite, sharing, notifications, audio | **ADOPT** |
| 3 | [pubkey/rxdb](https://github.com/pubkey/rxdb) | 23.4k | 2026-09-13 | Apache-2.0 core | Local-first DB | AVOID. The good RN SQLite storage is a paid plugin |
| 4 | [yjs/yjs](https://github.com/yjs/yjs) | 22.6k | 2026-08-06 | MIT | CRDT | AVOID. Built for collaborative text; job cards don't need it |
| 5 | [infinitered/ignite](https://github.com/infinitered/ignite) | 19.9k | 2026-04-30 | MIT | RN boilerplate + CLI | LEARN. Heavier than Obytes, and no commit for 5 months |
| 6 | [alphacep/vosk-api](https://github.com/alphacep/vosk-api) | 15.1k | 2026-08-09 | Apache-2.0 | Offline STT, small models | LEARN. Possible offline fallback; Telugu quality untested |
| 7 | [k2-fsa/sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) | 14.2k | 2026-10-12 | Apache-2.0 | Offline ASR/TTS on ONNX, Android builds | LEARN. Can run IndicConformer-style models on device later |
| 8 | [Nozbe/WatermelonDB](https://github.com/Nozbe/WatermelonDB) | 11.8k | 2025-08-11 | MIT | Reactive SQLite + sync protocol | AVOID. Stale (last npm 0.28.0 in 2025-07); you write your own sync endpoints |
| 9 | [electric-sql/electric](https://github.com/electric-sql/electric) | 10.4k | 2026-10-06 | Apache-2.0 | Postgres read-sync | LEARN. Read path only |
| 10 | [akaunting/akaunting](https://github.com/akaunting/akaunting) | 10.1k | 2026-10-08 | **BSL** | Accounting | AVOID |
| 11 | [invoiceninja/invoiceninja](https://github.com/invoiceninja/invoiceninja) | 10.0k | 2026-09-18 | **Elastic-2.0** | Invoicing | AVOID (not open source) |
| 12 | [idurar/idurar-erp-crm](https://github.com/idurar/idurar-erp-crm) | 8.8k | 2026-08-15 | **AGPL-3.0** | Node ERP/invoice | AVOID |
| 13 | [founded-labs/react-native-reusables](https://github.com/founded-labs/react-native-reusables) | 8.5k | 2026-09-27 | MIT | shadcn/ui for RN (NativeWind) | **ADOPT**. Fits the Kalamkari rule "shadcn on Radix" for mobile |
| 14 | [crater-invoice-inc/crater](https://github.com/crater-invoice-inc/crater) | 8.4k | 2023-02-19 | **AGPL-3.0** | Invoicing | AVOID (abandoned) |
| 15 | [Dolibarr/dolibarr](https://github.com/Dolibarr/dolibarr) | 7.6k | 2026-10-13 | **GPL-3.0** | ERP/CRM | AVOID |
| 16 | [Hopding/pdf-lib](https://github.com/Hopding/pdf-lib) | ~7k | 2021-11-11 | MIT | Pure-JS PDF writer | **ADOPT**. Frozen but stable; runs in RN, Deno and Node |
| 17 | [t3-oss/create-t3-turbo](https://github.com/t3-oss/create-t3-turbo) | 6.1k | 2025-12-11 | MIT | Next+Expo monorepo | AVOID. Too much for one app |
| 18 | [tinyplex/tinybase](https://github.com/tinyplex/tinybase) | 5.2k | 2026-09-24 | MIT | Reactive store + CRDT | ADOPT-alt. A4: merge worked in 0.7 ms |
| 19 | [frappe/books](https://github.com/frappe/books) | 4.9k | 2026-10-02 | **AGPL-3.0** | Offline accounting with an India GST model | AVOID copying; LEARN its GST fields |
| 20 | [obytes/react-native-template-obytes](https://github.com/obytes/react-native-template-obytes) | 4.4k | 2026-06-02 | MIT | Expo starter | **ADOPT** (upgrade SDK 54→57) |
| 21 | [bigcapitalhq/bigcapital](https://github.com/bigcapitalhq/bigcapital) | 3.9k | 2026-10-11 | **AGPL-3.0** | Accounting | AVOID |
| 22 | [expo/examples](https://github.com/expo/examples) | 3.7k | 2026-09-03 | MIT | Recipes (with-sqlite, with-pdf…) | LEARN |
| 23 | [InvoicePlane/InvoicePlane](https://github.com/InvoicePlane/InvoicePlane) | 3.1k | 2026-10-11 | MIT (+ trademark notice) | PHP invoicing | LEARN. Schema can be borrowed with attribution; name/logo cannot |
| 24 | [roninoss/create-expo-stack](https://github.com/roninoss/create-expo-stack) | 2.6k | 2026-09-15 | MIT | Expo scaffolder (NativeWind, Supabase, expo-router) | **ADOPT-alt**. Current SDK out of the box |
| 25 | [InvoiceShelf/InvoiceShelf](https://github.com/InvoiceShelf/InvoiceShelf) | 1.8k | 2026-09-29 | **AGPL-3.0** | Crater fork | AVOID |
| 26 | [sparksuite/simple-html-invoice-template](https://github.com/sparksuite/simple-html-invoice-template) | 1.7k | 2023-12-07 | MIT | HTML invoice layout | LEARN (layout only) |
| 27 | [kittendevv/Invio](https://github.com/kittendevv/Invio) | 1.2k | 2026-10-12 | Unlicense | Minimal self-hosted invoicing | LEARN (public domain) |
| 28 | [VladSez/easy-invoice-pdf](https://github.com/VladSez/easy-invoice-pdf) | 1.0k | 2026-10-09 | **AGPL-3.0** | In-browser invoice PDF | AVOID |
| 29 | [powersync-ja/powersync-js](https://github.com/powersync-ja/powersync-js) | 0.7k | 2026-10-12 | Apache-2.0 (client) | Offline SQLite ↔ Supabase | **ADOPT phase 2** |
| 30 | [jamsch/expo-speech-recognition](https://github.com/jamsch/expo-speech-recognition) | 0.7k | 2026-10-09 | MIT | Android/iOS live STT (`te-IN`) | **ADOPT** |

**Also screened (fewer stars, or only partly relevant):**

*LEARN:*
- invoicerr (AGPL, avoid copying).
- htmldocs (MIT).
- expo-local-first-template (MIT; Drizzle on expo-sqlite, last commit 2025-10).
- flemingvincent/expo-supabase-starter (MIT).
- LegendApp/legend-state (MIT; v3 still beta, npm `latest` is 2.1.15).
- rocicorp/mono, which is Zero (Apache-2.0; needs its own server).
- AI4Bharat/IndicConformerASR (MIT).
- harfbuzz/harfbuzzjs (MIT). We **adopted** this for Telugu.
- bhar4t/upiqr (MIT; we write the 6-line UPI string ourselves).
- clawnify/open-fieldservice (MIT; HVAC schema).
- electric-sql/pglite (Apache-2.0; test DB fallback).

*AVOID:*
- aspen-cloud/triplit (**AGPL**; Supabase bought it in 2025).
- namespace-ee/upcount (GPL).

## Recommended stack (exact versions, `npm view` on 13 Oct 2026)

| Layer | Package @ version | Licence | Why |
|---|---|---|---|
| App runtime | `expo@57.0.28`, `react-native@0.87.1`, `expo-router@57.0.26` | MIT | Current SDK. Obytes needs `npx expo install --fix` to get here |
| Starter | Obytes template (git HEAD 2026-06-02) **or** `create-expo-stack@2.23.3` | MIT | See "Starters tried" |
| UI | `nativewind@4.2.7` + react-native-reusables (`@react-native-reusables/cli@0.7.1`) | MIT | As DESIGN-SYSTEM.md requires |
| Voice (live, free) | `expo-speech-recognition@57.1.1` (`te-IN`, `persist: true`) | MIT | On-device Google recogniser |
| Voice (quality) | Sarvam STT REST from an Edge Function | API terms | ₹30/hour |
| Recording | `expo-audio@57.0.5` | MIT | |
| Local DB | `expo-sqlite@57.0.4` + outbox; `drizzle-orm@0.45.4` optional | MIT / Apache-2.0 | |
| Sync (phase 2) | `@powersync/react-native@2.3.1` | Apache-2.0 | Service is FSL |
| Server | `@supabase/supabase-js@2.117.3`, Postgres + RLS (`supabase/schema.sql`) | MIT | |
| Validation | `zod@4.6.7` | MIT | One JobCard schema for form and LLM JSON |
| **Invoice PDF** | `pdf-lib@1.17.1` + `@pdf-lib/fontkit@1.1.1` + `harfbuzzjs@1.6.3` + `qrcode@1.5.4` | MIT ×4 | Pure JS, the same code in app, Edge Function and tests |
| Fonts | `@fontsource/anek-telugu`, `anek-latin`, `rozha-one`, `jetbrains-mono` @5.3.0 | OFL-1.1 | Kalamkari faces embedded in the PDF |
| Share | `expo-sharing@57.0.23`, `expo-notifications@57.0.22` | MIT | Share the PDF to WhatsApp; AMC reminders |
| Tests | Node's built-in `node:test` (no install); `jest@30.5.2` inside the app | MIT | |
| Test DB | Local `postgres` 16 (Ubuntu) or `@electric-sql/pglite@0.5.9` | PostgreSQL / Apache-2.0 | |

**Drop from A4:** `expo-print` is no longer needed for invoices (keep it only for any future HTML reports), and `upiqr` is replaced by our own UPI string.

## Indian invoice rules for a technician

| Situation | Document | Must show | Source |
|---|---|---|---|
| **Not GST-registered** (service turnover under ₹20 lakh; Telangana is a normal-category state) | A plain **bill / cash memo**. GST law doesn't prescribe a format for unregistered people, and they **must not charge or show GST**. Calling it "Bill of Supply" is common but strictly a Rule 49 term for registered persons, so our wording is "Bill of Supply (not a tax invoice). Supplier not registered under GST; no GST charged." **The CA must confirm this (b2.q12).** | Name, phone, address, serial number, date, customer, description, amount | CGST Act s.22 (₹20 lakh services threshold); s.31(3)(c) |
| **Registered, composition scheme for services** (s.10(2A), 6%, turnover ≤ ₹50 lakh) | **Bill of Supply** (Rule 49), with the line **"composition taxable person, not eligible to collect tax on supplies"** at the top | Rule 49 list: supplier name, address, GSTIN; serial number ≤16 characters, unique per financial year; date; recipient name and address (+GSTIN if registered); HSN/SAC; description; value; signature | [Rule 49 (gstzen)](https://gstzen.in/a/bill-of-supply-cgst-rule-49.html); [Notfn 2/2019-CT(Rate)](https://gstzen.in/a/central-tax-notification-rate-022019-to-give-composition-scheme-for-supplier-of-services-with-a-tax-rate-of-6-having-annual-turn-over-in-preceding-year-upto-rs-50-lakhs.html); [knowyourgst](https://www.knowyourgst.com/blog/bill-of-supply-and-invoice-for-composition-levy-23/) |
| **Registered, regular** | **Tax Invoice** (Rule 46): CGST+SGST at 9%+9% within Telangana, IGST 18% across states | Rule 46 list: everything above, plus taxable value, rate, tax amount, place of supply (state name + code for inter-state), reverse-charge yes/no, signature. For an unregistered customer, their name, address and state are mandatory only if the taxable value is ≥ ₹50,000 (otherwise only if they ask) | [Rule 46 (teachoo)](https://www.teachoo.com/6095/1955/Rule-1---Tax-invoice/category/GST-Revised-Invoice-Rules/); [ICAI notes](https://live.icai.org/bos/vcc-2nd-batch-recorded-lectures/pdf/Tax%20Invoice.pdf) |
| **HSN/SAC digits** | Turnover ≤ ₹5 crore: **4 digits** mandatory on B2B, optional on B2C. Above ₹5 crore: 6 digits | Print the 6-digit SAC anyway (harmless and future-proof) | [Notfn 78/2020-CT](https://www.gstcouncil.gov.in/sites/default/files/2024-05/notfctn-78-central-tax-english-2020.pdf) |

**SAC codes** (all 18%; see the [busy.in 9987 list](https://busy.in/sac-code-9987) and [GimBooks](https://www.gimbooks.com/blog/maintenance-repair-installation-services-9987-hsn-code-gst-rate/amp/)):
- **998715** is "Maintenance and repair services of electrical household appliances". This is our **default for home split/window AC, fridges and washing machines**.
- **998717** (commercial and industrial machinery) is for office or central/ducted AC on AMC.
- **998736** is installation of electrical machinery n.e.c.: use it for new AC installation.
- Parts sold are **goods**. Use HSN 8415 for AC parts, 8418 for fridge parts, and 2903 for refrigerant gas, at their own rates. A registered technician who sells parts with a service may be making a *composite supply*, which is taxed at the principal supply's rate.
- PLAN.md's open question "998715 or 998717" is answered by appliance type: 998715 for homes, 998717 for commercial. The CA confirms in b2.q12.

**Our numbering:** `JC/26-27/0001` is 13 characters, under the 16-character limit, with a fresh series each financial year from 1 April. The database enforces this (see `supabase/schema.sql`).

## Starters tried (Step 2)

_Filled in below after the runs._

## Built (Step 3)

_Filled in below after the build._

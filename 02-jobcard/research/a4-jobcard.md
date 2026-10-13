# A4: Open-source building blocks for JobCard (b2)

Research agent 4 of 8, 2026-10-13. Scope: Expo starters, offline-first sync, speech-to-text for Telugu/Hindi/English, LLM extraction to JSON, GST invoice PDF, UPI links, field-service/invoice apps, subscription billing for India.

## Summary

JobCard can be built almost entirely from MIT/Apache parts that already sit inside the Expo SDK, so we don't need a framework:

- **App shell:** start from the **Obytes template** (MIT). In our run it type-checked cleanly and passed 40/40 tests. Its Zod forms, MMKV and i18n are what JobCard needs.
- **PDFs:** **expo-print** (MIT) turns an HTML string into a PDF on the device. In our test, a GST invoice with a UPI QR came out right. The catch is that Telugu text breaks unless the HTML embeds a Telugu font.
- **Sync:** **PowerSync** (client Apache-2.0) is the cleanest way to put an offline-first SQLite store on Supabase. **TinyBase** (MIT) is a lighter option. Its CRDT merge worked in our test.
- **Speech-to-text:** this was the biggest finding. **Whisper on the device is not usable for Telugu.** base and small (q5_1) produced garbage, and small hung for 151 s on a 15-second Telugu clip. Hindi only came out right on `small`. So:
  - Live dictation uses Android's free on-device recogniser through **expo-speech-recognition** (MIT).
  - The saved voice note goes to the **Sarvam** STT API (₹0.50/min) through a Supabase Edge Function.
  - whisper.rn is only an offline fallback for English and Hinglish.
- **Avoid:** the open-source invoice and FSM apps are AGPL (Crater, InvoiceShelf, IDURAR), ELv2 (Invoice Ninja), BSL (Akaunting) or GPL (ERPNext). We can learn from their data models but must not copy their code.

## Shortlist

Stars come from ecosyste.ms and are approximate (the GitHub API is blocked). Last commits come from shallow clones or ecosyste.ms `pushed_at`. Licences were read from each repo's LICENSE file or the npm tarball.

| Repo | What | Stars ~ | Last commit | Licence | Fit 1–5 | Verdict | Why |
|---|---|---|---|---|---|---|---|
| [obytes/react-native-template-obytes](https://github.com/obytes/react-native-template-obytes) | Expo starter: Expo Router, TS strict, Uniwind/Tailwind, Zustand, React Query, TanStack Form + Zod, MMKV, i18n, Jest, EAS profiles | 4.3k | 2026-06-02 | MIT | 5 | **ADOPT** | `tsc --noemit` passed in 20 s and Jest passed 40/40 tests in 15 s (see Tried it). It already includes the i18n, forms and storage JobCard needs. It is pinned to Expo SDK 54, so run `npx expo install --fix` after scaffolding. Comes with a `claude.md` for AI-assisted coding. |
| [expo/expo](https://github.com/expo/expo) packages: `expo-print`, `expo-sharing`, `expo-sqlite`, `expo-notifications`, `expo-audio` | HTML→PDF, share sheet (WhatsApp), local DB, scheduled reminders, recording | 52.6k | 2026-10-10 | MIT | 5 | **ADOPT** | Covers about 60% of JobCard with no extra native code: invoice PDF, share to WhatsApp, AMC reminders (local scheduled notifications that work offline), and voice-note recording. |
| [powersync-ja/powersync-js](https://github.com/powersync-ja/powersync-js) (`@powersync/react-native`) | Offline-first SQLite on the device, synced to Supabase Postgres | 0.7k | 2026-10-12 | Apache-2.0 (client). **Service is FSL-1.1-ALv2** | 4 | **ADOPT (phase 2)** | Has a ready `demos/react-native-supabase-todolist` (Supabase connector, `AppSchema.ts`, `database.sql`). The FSL licence only blocks offering a competing sync service, so running it ourselves or using PowerSync Cloud is fine. Using the cloud means a sign-up and a free-tier cap, and the owner would have to do that sign-up. |
| [tinyplex/tinybase](https://github.com/tinyplex/tinybase) | Reactive store plus CRDT `MergeableStore`, expo-sqlite persister, WebSocket/Durable-Object synchroniser | 5.2k | 2026-10-08 | MIT | 4 | **ADOPT (alt to PowerSync)** | In our test, two "devices" edited the same job card offline and merged in 0.7 ms with no lost edits. It has no Supabase sync, so we'd need a Cloudflare Durable Object relay (free tier) or our own push to Supabase. 2,000 jobs make about 0.5 MB of CRDT metadata. |
| [jamsch/expo-speech-recognition](https://github.com/jamsch/expo-speech-recognition) | Expo module for Android SpeechRecognizer and iOS SFSpeech, with on-device mode and audio recording | 0.7k | 2026-10-08 | MIT | 5 | **ADOPT** | Free live dictation in `te-IN`, `hi-IN` and `en-IN` through Google's recogniser, offline once the language pack is downloaded. `recordingOptions.persist` keeps the audio file so we can re-transcribe it later with better quality. |
| Sarvam STT API (no repo; SDK [`sarvamai`](https://www.npmjs.com/package/sarvamai) 1.1.12) | Hosted STT for 10+ Indian languages, with translate-to-English mode | n/a | npm 2026-10-12 | API ToS. **The npm SDK says "LICENSE" but ships no licence file** | 5 | **ADOPT (via REST, not the SDK)** | ₹30/hour (₹0.50/min) in batch or real time ([pricing](https://www.sarvam.ai/api-pricing)). 100 one-minute notes a month cost about ₹50 against a ₹149–299 plan. Call it with `fetch` from a Supabase Edge Function so the key never ships in the app. BotBhai already uses Sarvam (see A2). |
| [mybigday/whisper.rn](https://github.com/mybigday/whisper.rn) + [ggml-org/whisper.cpp](https://github.com/ggml-org/whisper.cpp) | On-device Whisper for RN | 0.8k / 54k | 2026-10-07 / 2026-10-12 | MIT | 2 | LEARN | **Fails on Telugu** (see Tried it). English works on `base` (142 MB, 2.7 s for an 8 s clip on 2 CPU cores). Only worth it as an offline English and Hinglish fallback, and it adds 75–190 MB of model download. |
| [AI4Bharat/IndicConformerASR](https://github.com/AI4Bharat/IndicConformerASR) | 600M multilingual Indic ASR (22 languages) | <0.1k | 2025-06-20 | MIT (code and weights) | 3 | LEARN | The fallback if Sarvam gets expensive: batch-transcribe voice notes on a Colab or Actions CPU. It isn't real time, but job cards don't need to be. Too big for a phone. |
| [software-mansion/react-native-executorch](https://github.com/software-mansion/react-native-executorch) | On-device LLM, Whisper and OCR for RN | 1.8k | 2026-10-12 | MIT | 2 | LEARN | Could run a small LLM for JSON extraction offline later. It is heavy for the ₹8–12k Android phones technicians use, and its Whisper has the same Telugu weakness. The [private-mind](https://github.com/software-mansion-labs/private-mind) demo app (MIT) is the reference. |
| [bhar4t/upiqr](https://github.com/bhar4t/upiqr) | UPI `upi://pay` intent string plus a QR data-URL | <0.1k | 2026-10-07 | MIT | 4 | **ADOPT** (tiny) | Produced a 1.7 KB QR data-URL that we put inside the invoice HTML. The default async export is deprecated, so use `upiqrSync`. The link format is short enough that we could just write it ourselves. |
| [RevenueCat/react-native-purchases](https://github.com/RevenueCat/react-native-purchases) | Play/App Store subscriptions, entitlements, paywalls | 1.2k | 2026-10-09 | MIT (SDK). The service is free below a revenue cap | 4 | **ADOPT (if Play Billing needed)** | It's the simplest correct way to sell a ₹149/₹299 monthly subscription inside a Play Store app. Using it requires the owner to sign up for a RevenueCat account. |
| [razorpay/react-native-razorpay](https://github.com/razorpay/react-native-razorpay) | Razorpay Checkout for RN (works with `subscription_id` for UPI AutoPay) | 0.1k | 2026-09-21 | MIT | 3 | LEARN | Lower fees and UPI AutoPay mandates. Whether we can use it for an in-app digital subscription depends on Play's payments policy in India (see Risks). Safer for web checkout from a landing page. |
| [flemingvincent/expo-supabase-starter](https://github.com/flemingvincent/expo-supabase-starter) | Minimal Expo Router + Supabase auth starter | ~1k? | 2026-07-02 | MIT | 3 | LEARN | Good reference for Supabase auth/session wiring (phone OTP) to add to the Obytes template. Smaller and less tested than Obytes. |
| [infinitered/ignite](https://github.com/infinitered/ignite) | Long-running RN boilerplate and CLI | 19.9k | 2026-04-30 | MIT | 3 | LEARN | Mature, but more opinionated and heavier than Obytes, and its last commit is older. |
| [Nozbe/WatermelonDB](https://github.com/Nozbe/WatermelonDB) | Lazy reactive SQLite DB with a sync protocol | 11.8k | 2026-09-16 | MIT | 2 | LEARN | You have to write your own push/pull endpoints, Expo needs a community config plugin, and the last npm release was 2025-07. PowerSync gives us the same thing ready-made. |
| [pubkey/rxdb](https://github.com/pubkey/rxdb) | Local-first DB with Supabase replication | 23.4k | 2026-10-09 | Apache-2.0 core. **SQLite storage for RN is a paid premium plugin** | 2 | AVOID | The free RN storage options are weak, and the good one costs money. |
| [electric-sql/electric](https://github.com/electric-sql/electric) | Postgres read-path sync ("shapes") | 10.4k | 2026-10-03 | Apache-2.0 | 2 | AVOID (for now) | Only syncs reads, so we'd still write our own write path and offline queue. The project is now pitched as an "agent platform built on sync". |
| [crater-invoice-inc/crater](https://github.com/crater-invoice-inc/crater) + crater-mobile | Laravel invoicing app plus an RN app | 8.4k / 0.4k | 2024-08-10 / 2023-03-04 | AGPL-3.0 | 1 | AVOID copying (LEARN schema) | Abandoned, and AGPL. Its fork [InvoiceShelf](https://github.com/InvoiceShelf/InvoiceShelf) (1.8k, active, AGPL) is the place to read how invoice numbering, tax types and estimates→invoices are modelled. |
| [frappe/erpnext](https://github.com/frappe/erpnext) + [kodlyft/fsm](https://github.com/kodlyft/fsm) | ERP with an India GST compliance app, plus an FSM add-on | 39.8k / <0.1k | 2026-10-05 / 2026-10-09 | GPL-3.0 / MIT on GPL Frappe | 1 | AVOID | Far too heavy for a single technician, and it's GPL. Read the `india_compliance` GST invoice print formats only to check which fields a GST invoice must carry. |

Other candidates screened:
- **Avoid:**
  - invoiceninja (**Elastic License 2.0**, not open source).
  - akaunting (**BSL**).
  - idurar-erp-crm (**AGPL**).
  - Odoo mobile framework (LGPL/old).
  - hyochan/react-native-iap (MIT but **archived**; its successor is `expo-iap`).
  - 567-labs/instructor-js (MIT, stale since 2025-01). Provider-native JSON-schema output plus Zod is enough.
- **Server-side only:** dottxt-ai/outlines (Apache-2.0), not needed for a hosted LLM.
- **No better than what we picked:**
  - LegendApp/legend-state (MIT, has a Supabase sync plugin, v3 still beta).
  - op-sqlite (MIT, faster SQLite; expo-sqlite is enough).
  - @react-pdf/renderer (MIT, but no React Native support, web/Node only).
  - christopherdro/react-native-html-to-pdf (MIT, 461★; expo-print does the same in the managed workflow).
  - pdf-lib (MIT, no release since 2022).
  - upiqrcode (Apache-2.0), upi-link (MIT, 2022).
  - DaveyEke/expo-speech-transcriber (MIT, iOS-only).
  - expo/examples (MIT, recipes).
  - supabase-js (MIT, will be used anyway).
  - bndkt/powerchat-tinybase.
  - aaronksaunders/expo-supabase-ai-template.
  - toyamarodrigo/expo-router-template.
  - goff-studio/InvoiceManager.
  - nrenx/excel2web-invoice-flow (couldn't be cloned).
  - WordPress "GST invoice" plugins (GPL, PHP).

## Tried it

All work was done in scratch and deleted afterwards. No accounts or API keys were used.

1. **Obytes template (Expo SDK 54, RN 0.81.5), already-installed clone, 686 MB `node_modules`**
   - `npx tsc --noemit`: **0 errors in 20 s**.
   - `npx jest`: **5 suites, 40/40 tests passed in 15 s**. Jest warns about an open handle on exit, which is harmless.
   - It ships `src/translations/{en,ar}.json`, so adding `te.json` and `hi.json` is a drop-in change.
   - Expo's current packages are at `57.x` (`expo-print@57.0.2`, `expo-sqlite@57.0.4`), so the template is **3 SDKs behind**. Plan one upgrade pass on day 1.
2. **GST invoice: job-card JSON → HTML (the exact string `expo-print`'s `printToFileAsync({html})` takes) → PDF**
   - Setup: `npm i upiqr@1.4.1 playwright-core tinybase@10.0.1` took 9 s. Headless Chromium stood in for Android's WebView print.
   - Test invoice: an intra-state Telangana invoice with 3 lines (2 SAC service lines, 1 HSN part).
   - Totals came out right: taxable ₹3,750.00, **CGST ₹337.50 + SGST ₹337.50**, total ₹4,425.00.
   - Amount in words used Indian lakh/crore grouping: "Four Thousand Four Hundred Twenty Five".
   - It produced a UPI intent `upi://pay?pa=…&am=4425.00&cu=INR&tn=JC%2F26-27%2F0042` plus a QR image, and a **37 KB A4 PDF in 2.8 s**.
   - **Bug found:** the Telugu line "ఏసీ గ్యాస్ రీఫిల్" printed with broken conjuncts. The machine had no Telugu shaping font and fell back to Unifont. Fix: embed Noto Sans Telugu as a base64 `@font-face` in the template. Don't rely on the phone having the font.
3. **Offline sync with TinyBase `MergeableStore`**
   - "Phone" marked job `j1` done with ₹4,425 while a "helper" device, also offline, added notes and a new job `j2`.
   - `merge()` took **0.7 ms**. Both stores came out identical with all 4 edits kept.
   - 2,000 job cards make 493 KB of mergeable content, which is fine for SQLite.
4. **whisper.cpp (HEAD 2026-10-12) on synthetic voice notes**
   - Setup: built `whisper-cli` in 86 s on 2 cores. The clips were 8–12 s gTTS recordings of a technician's note in Telugu, Hindi and Indian English, at 16 kHz mono.
   - **English:** both models gave a correct transcript ("AC gas refill done. 2,500 rupees. Capacitor changed. Next service after 6 months"). `base` took 2.7 s, `small-q5_1` took 11 s.
   - **Hindi:** `base` came out in **Urdu script**. `small-q5_1` produced good Devanagari ("चार सो पचास रुप्ये") in 22 s.
   - **Telugu:** `base` produced **mixed Urdu, Tamil and Cyrillic garbage**. `small-q5_1` looped for **151 s and returned "."**.
   - Conclusion: Telugu notes must go to Sarvam or IndicConformer, or to Google's on-device recogniser. Whisper on the device is not an option for Telugu.
   - Caveat: the clips were synthetic voices, not real technicians speaking over compressor noise.

Not tried: PowerSync end-to-end (needs a Supabase project and a PowerSync instance, which means sign-ups), Sarvam and LLM extraction (need API keys), and RevenueCat/Razorpay (need merchant accounts).

## Recommendations (concrete changes for Kalpa Labs)

- **`02-jobcard/src/`**: scaffold from the Obytes template with `npx create-obytes-app@latest` (or a degit of the repo), then run `npx expo install --fix` to reach the current SDK.
  - Add `src/translations/te.json` and `hi.json`.
  - Delete the `features/feed` example.
- **Feature folders**:
  - **`02-jobcard/src/features/jobcard/schema.ts`**: one Zod `JobCard` schema used both for the form and as the JSON schema for the LLM's structured output. Fields: `customer{name,phone,area}`, `appliance{type,brand,tonnage}`, `work[]{desc,sac_hsn,qty,rate,gst}`, `parts[]`, `next_service_date`, `amc{start,visits_left}`, `language`, `transcript`, `audio_uri`.
  - **`02-jobcard/src/features/voice/`**:
    - Use `expo-speech-recognition` with `lang: 'te-IN' | 'hi-IN' | 'en-IN'`, `requiresOnDeviceRecognition` when offline, and `recordingOptions.persist: true`. This gives the technician a free live preview on the device.
    - Queue the saved `.wav` in an outbox table. When the phone is back online, upload it to Supabase Storage.
  - **`02-jobcard/src/features/invoice/template.ts`**: HTML template built from trial 2.
    - Show a **Bill of Supply** for technicians who are not GST-registered (most are below ₹20 lakh turnover) and a **Tax Invoice** with CGST+SGST or IGST otherwise.
    - Use an FY-wise invoice series of at most 16 characters (e.g. `JC/26-27/0042`), amount in words in Indian grouping, an embedded Noto Sans Telugu font, and a UPI QR from `upiqrSync`.
    - Render it with `Print.printToFileAsync`, then call `Sharing.shareAsync(uri, {mimeType:'application/pdf'})` so the technician picks WhatsApp in the share sheet. A `wa.me` link can only carry text, not the PDF.
  - **`02-jobcard/src/features/reminders/`**: when a job closes, `Notifications.scheduleNotificationAsync` for `next_service_date` minus 3 days. Tapping it opens `https://wa.me/91XXXXXXXXXX?text=…` with a prefilled AMC reminder in Telugu or English. The technician sends it by hand, so there's no WhatsApp API cost.
- **New `02-jobcard/supabase/functions/transcribe-extract/index.ts`** (an Edge Function, free tier):
  - Send the audio to the Sarvam STT REST API, using translate mode to get English for extraction while keeping the original transcript.
  - Pass the transcript to an LLM in JSON-schema mode (Gemini Flash or Groq free tier), using the Zod schema exported as JSON Schema.
  - Validate the result, then write `job_cards`.
  - Keys stay in Edge Function secrets. Use plain `fetch` for Sarvam, not the `sarvamai` SDK, whose licence is unclear.
- **Data (phase 1, MVP)**: use `expo-sqlite` as the source of truth on the device, plus an outbox that pushes to Supabase tables (`customers`, `job_cards`, `invoices`, `amc_contracts`) with RLS on `auth.uid()`.
- **Data (phase 2)**: when a technician adds a helper or a second phone, switch to PowerSync, using `demos/react-native-supabase-todolist/library/powersync/{AppSchema,system}.ts` as the template. Use TinyBase plus a Cloudflare Durable Object relay only if we want to avoid the PowerSync service.
- **`02-jobcard/docs/decisions.md`** (when the build starts):
  - Record: "No on-device Whisper for Telugu (A4 test)" and "No AGPL invoice code".
  - Record the billing choice: RevenueCat plus Play Billing by default, or Razorpay subscriptions through a web checkout if Play's India policy allows.

## Risks

- **Play Store billing:** a ₹149–299 in-app subscription is a digital service, so Google Play Billing (15% fee on subscriptions) is normally required. India's alternative-billing rules have changed several times since 2023. Check the current Play Payments policy before wiring Razorpay inside the app.
- **UPI intent links to personal VPAs:** some UPI apps block or cap `upi://pay` intents with a preset amount when the payee is not a verified merchant. Show the **QR** as the main option, and push technicians toward a free business VPA (PhonePe/Paytm/GPay for Business). Test with the real apps before launch.
- **Speech quality:** the on-device Google recogniser needs the Telugu offline pack, which varies by device and Android version. Real notes are code-mixed Tenglish with AC jargon ("R32", "PCB", "tonnage"), so expect the LLM to have to fix brand and part names. Keep the transcript editable and always store the audio.
- **Cost per user:** Sarvam at ₹0.50/min plus LLM calls fits ₹149/month only if notes stay short. Cap the length at about 2 min and keep a monthly minute quota per account.
- **Licences:**
  - PowerSync's **service** is FSL-1.1 (it becomes Apache-2.0 after 2 years). We can use it, but must not resell it as a sync service.
  - The `sarvamai` npm package has no licence file.
  - Crater, InvoiceShelf, IDURAR and ERPNext are AGPL/GPL, and Invoice Ninja (ELv2) and Akaunting (BSL) are source-available. Read them only; never copy code into JobCard.
- **GST correctness:** the SAC/HSN codes and the 18% rate in the trial are placeholders. Have a CA confirm the codes for AC repair services and parts and the rules for a Bill of Supply versus a Tax Invoice before the first paying user.
- **Template drift:** Obytes lags Expo by about 3 SDKs, and the upgrade could break Uniwind/MMKV. Allow one session for it.
- **Low-RAM PC:** `node_modules` is about 690 MB. Develop in Codespaces and build APKs with EAS Build's free tier, not locally.

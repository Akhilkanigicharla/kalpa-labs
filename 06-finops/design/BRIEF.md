# Ledger Peaks screens: design brief (A12)

**Who:** the CTO or founder of an Indian SaaS / AI startup (seed to Series A, 5–50 people). They read our cold note on a phone, open the sample X-ray, and decide in under a minute whether to send last month's usage export. Later, their finance person opens the dashboard once a week.

**Screens (mockups on synthetic data, phone first, Kalpavruksha tokens from `00-hq/design/`, world colour `--l6` pomegranate):**

| Screen | File | Job |
|---|---|---|
| Landing | `landing.html` | One promise ("which customer is your AI bill eating?"), the trust note, 3 steps, price ladder, free X-ray call-to-action |
| Dashboard | `dashboard.html` | 4 bottom tabs: Overview (3 numbers, cost per day, feature, model, unpriced warning) · Customers (margin per customer) · Savings (3 ideas with assumptions) · Evidence (DPDP score and gaps, monthly pack) |
| X-ray report | `xray.html` | The 2-page free report: ₹ by customer/feature/model, unpriced models, 3 savings ideas, GST reverse-charge note, DPDP score /20, method and sources. "Save as PDF" prints it as 2 A4 pages |

Open them from the repo (they load `../../00-hq/design/tokens.css` and the self-hosted fonts), e.g. `python3 -m http.server` at the repo root, then `/06-finops/design/landing.html`.

## Where the numbers come from
`sample.py` makes one synthetic week for a made-up company, "Chaiwala AI" (6 customers, 5 features, 5 models), prices every row with **the real engine** (`src/price`, genai-prices + the cached FBIL rate) and writes the result into each page's `<script id="lp-data">` block. Savings ideas re-price the same rows with the change applied (more cache reads, gpt-4o → gpt-4o-mini, Batch API), so every ₹ on screen is traceable. One model (`sarvam/sarvam-m`) has no public price and shows up as "unpriced", never ₹0 (F-02). After changing `sample.py`, run `python3 06-finops/design/sample.py`.

## Research applied
- a7 + Deep Scan v2: ingest the tools they already use (OpenAI/Anthropic exports, LiteLLM, Langfuse, CSV), metadata only, INR at the RBI/FBIL rate, per-call pricing, unknown models flagged.
- PLAN.md §2 price ladder and §3 trust note (metadata only, Mumbai region, delete in 14 days); the X-ray contents follow the F-06 row.
- Same dashboard pattern as the BotBhai brief (`01-botbhai/design/BRIEF.md`, from shadcn-admin / dashboard-01): big numbers first, then one chart, then lists; details one tap away; bottom tab bar under 760 px; 44 px targets.

## Rules for these screens
1. **Three numbers at the top:** AI bill this month, customers losing money, savings found. Each opens its tab.
2. **Savings are estimates with their assumption printed next to them**, never a bare "save ₹X".
3. **Unpriced is loud:** a gold note, left out of every total.
4. **Customer names stay with the customer:** we store HMAC ids; names come from their own revenue file.
5. **DPDP score is "a checklist, not legal advice"**, and quotes no penalties.
6. **No external requests:** fonts are self-hosted from `00-hq/design/fonts` (A52 direction), no analytics, no CDN.
7. **Both themes, 390 px, no sideways scroll:** `python3 06-finops/design/screens.py` checks 12 screens (landing, X-ray, 4 dashboard tabs × light/dark) and saves PNGs to `design/screens/` (not in git). `tests/test_design.py` checks the numbers add up, prices match PLAN.md and the source rules.

## Next (not in this item)
- F-04: Akhil approves the name and the copy (CEO queue), then the landing moves to an Astro page on Netlify.
- A30 (F-06): the real X-ray generator reuses `xray.html` as its template, fed by an uploaded export instead of `sample.py`.
- A33 (F-12): the real dashboard reads Supabase (A28) instead of the inline sample.

## The real generator (A30, F-06)
`python3 06-finops/src/xray/generate.py usage.csv --company "Acme AI" --revenue revenue.csv --dpdp answers.json --out xray.html --pdf`
(or `--synthetic` for the demo) fills this same `xray.html` from an uploaded export: any importer format, ₹ from the real engine, 3 savings ideas from generic rules (cache / smaller model / Batch API, one per feature so they never double count), margins only when a revenue file is given, DPDP "not answered" until the client answers. The output is one self-contained file (tokens, CSS, fonts and script inlined; no external requests) that prints as 2 A4 pages. Tests: `06-finops/tests/test_xray.py`.

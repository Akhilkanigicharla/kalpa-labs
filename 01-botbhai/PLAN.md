# P1 — BotBhai (world b1): from zero to paying salons in Hyderabad

Planning agent P1 · 13 Oct 2026 · inputs: `00-hq/research/BRIEF.md`, research a1/a2/a3, `01-botbhai/botbhai/` (README, `setups/*`, `docs/requirements/salon.md`, `leads/hyderabad-leads.csv`), `00-hq/agents/registry.js`, `state.json`.

---

## 1. Verdict

BotBhai makes money by selling small Hyderabad salons a done-for-you WhatsApp front desk. It replies 24×7 in Telugu, Hindi and English, books slots, sends reminders and asks for reviews.

- **Revenue:** a setup fee plus a monthly fee.
- **Meta's message fees:** the salon pays them directly on its own account.
- **Product status:** about 80% built. The money depends on closing walk-in demos and keeping support under 45 min per client per month.

| Cash in per month | Low | Likely | High |
|---|---|---|---|
| Month 1 (to mid-Nov) | ₹0 | ₹3,000 (first founding advance) | ₹8,000 |
| Month 3 (mid-Jan) | ₹4,500 | ₹12,000 | ₹25,000 |
| Month 6 (mid-Apr) | ₹10,000 | ₹35,000 | ₹70,000 |
| Month 12 (Oct 2027) | ₹25,000 | ₹85,000 | ₹1,80,000 |

Each figure is MRR plus that month's setup fees. "Likely" at month 12 means about 18 salons, 5 gyms and 3 coaching institutes live.

**Biggest risk: founder time, not the product.** With 1 h a day, every live client adds support load, and every week spent building is a week not spent selling. The plan pauses if there are fewer than 2 paying salons by 31 Jan 2027 (§7).

---

## 2. Customer & offer

**Who pays first:** the owner of a 2–6 chair unisex or ladies salon in a dense area: SR Nagar/Ameerpet, KPHB, Madhapur/Kondapur or Dilsukhnagar. The salon is busy enough to lose bookings to missed calls and 11 PM WhatsApps, but too small for Zenoti.

**Offer:** "Your WhatsApp answers at 11 PM in Telugu, books the slot, reminds the customer twice and asks happy customers for a Google review. If it doesn't pay for itself in 60 days, stop paying."

**Why now:** wedding season (Nov–Feb muhurthams; a bridal lead is worth ₹15k–80k) and Sankranti.

### Salon price ladder

This is a recommended change to `setups/salon/setup.meta.json`. A ₹9,999 setup fee is a hard first ask when DINGG starts at ₹999/month, so ₹9,999 moves to the Pro tier.

| Tier | Setup | Monthly | Includes |
|---|---|---|---|
| **Founding** (first 3 salons, 12-month lock) | ₹2,999 | ₹1,499 for months 1–3, then ₹1,999 | Standard features. In return: a baseline from the salon's register, a testimonial, and use of anonymised numbers |
| **Lite** | ₹1,999 | ₹999 | WhatsApp bot (prices, FAQ, booking, reschedule/cancel), 24 h + 2 h reminders, owner alerts, dashboard + Excel |
| **Standard** | ₹4,999 | ₹2,999 | Lite plus review asks, opt-in win-back/offers, bridal enquiry flow, 9:30 AM daily list, SEO mini-site (`seo/seo_bot.py`), web voice, monthly ROI report |
| **Pro** | ₹9,999 | ₹4,999 | Standard plus Meta ads management (`core/functions/adsbot.js`; the salon pays ad spend) and a phone voice receptionist (300 min included, then ₹3/min) |

Terms for every tier:
- Setup fee: 50% on signing, 50% at go-live.
- Monthly: no lock-in.
- Annual prepay: 2 months free.

**Later setups** (setup fee + monthly):

| Setup | Lite | Standard | Pro |
|---|---|---|---|
| Gym | ₹1,999 + ₹1,499 | ₹6,999 + ₹3,499 | ₹9,999 + ₹5,999 |
| Exam kits / coaching | ₹2,999 + ₹1,999 | ₹9,999 + ₹4,999 | ₹14,999 + ₹7,999 |
| Real estate | — | ₹24,999 + ₹7,999 | ₹24,999 + ₹12,999 (calls at cost + ₹2/min) |

**Alternatives the owner has:**

| Alternative | Price | Gap vs BotBhai |
|---|---|---|
| DINGG | ₹999–2,499/mo | Software that staff must run. No Tenglish 24×7 booker |
| Zylu | ₹1,299–3,499/mo | Same: a tool, not done-for-you |
| AiSensy (DIY WhatsApp) | ₹1,500/mo + ₹2,500/mo chatbot add-on + ~26% markup on marketing messages | The salon builds flows itself. No booking lock or reminder logic |

The status quo is a local "digital marketing" freelancer at ₹2,000+/mo with no proof of bookings. BotBhai's edge: done-for-you, Telugu/Hindi, reminders tied to a real booking lock (`book_slot`), and no markup on Meta fees.

---

## 3. Unit economics

### 3a. WhatsApp fees from 1 Oct 2026 (India), and who pays

India rates from 1 Oct 2026 (all + 18% GST):

| Category | Rate | Note |
|---|---|---|
| Service (free-form replies inside the 24 h window) | 1,000 free per number per month, then ~₹0.115 | |
| Utility templates (reminders, alerts) | ~₹0.115 | Now charged even inside the window |
| Marketing | ~₹0.863 | Unchanged |
| Chats opened from Click-to-WhatsApp ads or a Page button | Free for 72 h | |
| Incoming messages | Free | |

- **A payment method is now mandatory.** Without one, even service replies stop delivering.
- BSP figures of ₹0.14–0.145 and ₹0.95–1.09 include their markup.
- Meta's developer page didn't list India among the October changes. Confirm the INR rate card in WhatsApp Manager at every onboarding.

**Typical salon bill (300 bookings a month):**

| Message | Count | ₹ |
|---|---|---|
| Day-before + 2-hour reminders (utility) | 600 | 70 |
| Owner alerts, batched into a daily digest (utility) | ~60 | 7 |
| Bot replies (service): 1,000 free + 1,500 paid | 2,500 | 173 |
| Review asks to completed visits (marketing) | 260 | 224 |
| Win-back, opt-in only (marketing) | 100 | 86 |
| **Total** | | **≈ ₹560 + GST ≈ ₹660/mo** (Lite with no marketing ≈ ₹290) |

**Who pays:** the salon, directly to Meta, on its own WABA and card. Kalpa Labs never fronts Meta fees, because that would bring credit risk, GST on pass-through and ban exposure on our account.

The proposal shows the estimate, and the monthly report shows actual spend (P1-M2-03). Two quests cut the bill:
- **WhatsApp Flows** booking takes about 6 service messages down to 2 or 3.
- **Batched owner alerts** go out as one daily digest.

### 3b. Our cost to serve per salon

| Item | Free tier | Per salon | Runs out |
|---|---|---|---|
| Netlify Functions | 300 credits/mo, **hard stop: all sites pause** | ~3–5 credits | Each prod deploy costs 15 credits, so cap deploys at 8/mo. Buy Personal ($9 ≈ ₹800) at ~10 clients |
| Supabase | 500 MB, no backups, pauses after 7 idle days | ~3–5 MB/mo | Size lasts to ~40 salons, but there are **no backups**. Nightly dump via Actions (P1-M2-07); Pro ($25 ≈ ₹2,200) at MRR ≥ ₹6,000 |
| Groq | free | ₹0 | Rate limits at ~50 busy clients |
| Voice (Pro only) | Sarvam gives ₹100 credit | Plivo ₹200/mo number + ₹0.38/min; STT ₹0.50/min; TTS ~₹1/min. About ₹2.5/min, so 300 min ≈ ₹900 | Priced into Pro |

**Gross margin:**
- Lite and Standard: ~95% on free tiers, ~85% once ₹3,000/mo of paid infrastructure is shared across 10 clients.
- Pro: ~80%.

**Break-even:** 1 client on free tiers, 2 Standard clients after the upgrades.

### 3c. Support load per client

| Phase | Akhil | Agents |
|---|---|---|
| Sale | ~90 min over 2 weeks | Visit list, pitch, demo config, proposal |
| Onboarding | 60–90 min (one Meta call with the owner, one go-live check) | Config, templates, 25 test chats, staff card |
| Month 1 | ~2 h | FAQ Grower, Health Monitor |
| Steady state | **30–45 min/month** | Weekly health report, monthly ROI report |

**Capacity:** Akhil has ~30 h a month. Selling and building take ~12 h, which leaves ~18 h for support, or **about 20–24 live clients**.

Beyond that he needs one of two things:
- Owner self-service commands on WhatsApp (P1-M2-04).
- A part-time onboarding assistant (₹8–10k/mo), once MRR passes ₹40,000.

---

## 4. Go-to-market

### Walk-ins are the main channel

`leads/hyderabad-leads.csv` has 142 "salon" rows:
- 24 are cosmetics shops, not salons.
- Only 13 have a phone number and 29 have an address.
- Only 9 score 80 or above.

So OpenStreetMap is a **map of where to walk**, not a call list. One commercial street has 8–15 salons.

Outreach rules:
- No cold calls.
- No scraping of Google Maps, Justdial or Instagram.
- A salon that publishes a WhatsApp number on its own site gets at most **one** intro with an opt-out line.

### Demo-to-close flow

1. **Plan (agents, Sunday).** Prospector picks a cluster of 6 salons within ~1 km from the CSV's lat/lon. Pitch Writer drafts a 60-word Telugu/English intro for each.
2. **Walk in (10–12 min each, 11:30 AM–1 PM, when salons are quiet).** Ask three questions:
   - How many WhatsApps come in after 9 PM?
   - How many no-shows did you have last Saturday?
   - Who answers the phone during a facial?
3. **Live demo on the owner's phone.** The owner texts the BotBhai demo number, which is on Kalpa Labs' own WABA. Because the owner starts the chat, replies are free service messages. They type "repu haircut kavali", pick a slot, book, and see the reminder and the dashboard. For visit 2, Demo Builder (`build.py`) loads their name and the prices from a photo of their price board, taken with permission.
4. **Leave-behind.** An A5 card with a QR code to the demo, the three loss numbers, and the founding offer.
5. **Close (visit 2, day 3–5).**
   - A one-page proposal using their numbers.
   - An agreement with a DPDP processor clause, deletion on exit and no lock-in.
   - 50% advance by UPI.
   - A refund promise: "live in 10 days or your advance back."
6. **Follow-ups.** Nudger on days 2, 5 and 10; at most 3, and it stops on "no". Objection Coach prepares answers on staff, ban fear, price and trust.

**Daily quota.**
- Mon–Fri: about 20 min a day. 5 min reviewing agent prep, 10 min of follow-ups, 5 min logging outcomes.
- Two days a week: the full hour becomes a 4-salon walk-in block, so about 8 visits a week.
- Expected funnel: 8 visits → 3 demos → 1 proposal a week, closing 25–35%.
- That is about **one salon every 2–3 weeks**: 3 founding salons by mid-Dec and 10 by about March.

### From 10 to 100

| Lever | Start |
|---|---|
| Referral: 1 month free for both sides | Salon #2 |
| Telugu case-study reel + one-pager from founding salons' metrics (`salon.md` §6) | Month 3 |
| Kalpa Labs' own Click-to-WhatsApp ads, ₹150–200/day around clusters (the demo bot is the landing page) | MRR ≥ ₹10,000 |
| Distributor and beauty-academy partners (1 month fee as commission) | Month 4 |
| Self-serve Lite signup (needs Meta Tech Provider status, P1-M3-05) | Month 5+ |
| Part-time onboarding assistant | MRR > ₹40,000 |

### When to open setups 2, 3, 4

These gates update `state.json` `active_setups`.

| Setup | Gate (all true) | Earliest | Why |
|---|---|---|---|
| **2 Gym** | ≥3 paying salons live ≥30 days; T01–T25 ≥22 pass; no quality drops; support ≤45 min/salon | BA work 15 Dec, demos 26 Dec | January resolution rush. `dueRenewals` already exists. 114 leads |
| **3 Exam kits** | ≥2 paying gyms or ≥8 salons; `pf.ba.examkits` pack done; **adult learners only** (DPDP: children need verifiable parental consent) | Mar 2027 | Biggest pool (414 leads), ₹4,999 ticket |
| **4 Real estate** | ≥10 clients; voice evals green; outbound only to consented Meta leads from a registered commercial number; housing special ad category | Jun 2027+ | Highest ticket but only 2 leads, plus heavy RERA/TRAI/Meta-housing compliance |

---

## 5. Build plan

Each quest takes ≤60 min of Akhil's time. Agents build. Akhil reviews and says "deploy". `M#`/`S#` codes are from `docs/requirements/salon.md` §4.

### Week 1 (13–19 Oct)

| ID | Quest | Akhil | Agent | Done-check |
|---|---|---|---|---|
| P1-W1-01 | Approve price ladder | 10 min | Update `setups/*/setup.meta.json`, READMEs | Tests green; new ladder shown |
| P1-W1-02 | MUST quick fixes: M1 confirm reply, M2 reminder flags, M3 IST, M5 "4pm", M6 "hair cut", M12 Tenglish/Telugu greeting, M14 home visit | 15 | `core/engine.js`, `functions/whatsapp.js`, `reminders.js`; make `_fake.js` mimic PostgREST replace | T05–T07, T12, T22, T23 pass; swarm 623/623 |
| P1-W1-03 | M7 `bb_owner_alert` utility template; M13 marketing opt-in gate | 5 | `templates.json`, `schema.sql` `marketing_opt_in` | Alert arrives after 25 h silence; no marketing without opt-in |
| P1-W1-04 | Kalpa Labs Meta Business portfolio + verification (Udyam; names must match) | 45 | Document checklist | Submitted |
| P1-W1-05 | Demo number: prepaid SIM (~₹250, **worth it**, unlocks every demo), WABA, display name | 40 | Demo client row + config | Second phone books a slot |
| P1-W1-06 | Cluster 1 visit sheet (SR Nagar/Ameerpet) | 5 | Filter out cosmetics, cluster by lat/lon, write pitches | 6 salons with map links |

### Weeks 2–4 (20 Oct – 9 Nov)

| ID | Quest | Akhil | Agent | Done-check |
|---|---|---|---|---|
| P1-W2-01 | **Slot engine phase 1 (per cal.diy, MIT).** New `core/slots.js` ports `slots.ts` + `date-ranges.ts`: structured hours, weekly off, holidays, special hours, "closing for today" (M4). `book_slot` stays the final lock | 10 | Replace `freeSlots()`/`slotMinutes()`; config in `setups/salon/bot.config.json`; MIT notice | T11, T13, T14 pass; race test passes |
| P1-W2-02 | **Shared inbox phase 1 (per wacrm, MIT).** `web/inbox.html` + `core/functions/inbox.js`: paused chats, reply from the salon number via Graph API, "resume bot". Add `assigned_to`, `status`, `human_until`, `notes` to `sessions`. Closes M9 and meets Meta's escalation-path rule | 15 (try on phone) | Build; per-client token, RLS | T17, T25 pass; staff replies logged `author='staff'` |
| P1-W2-03 | **Voice turn-taking fix (a2).** In `voice/agent.py`: VAD moves to `LLMUserAggregatorParams` (Silero `stop_secs=0.2`), add `LocalSmartTurnAnalyzerV3(stop_secs=1.5)`, set Sarvam TTS language te-IN/hi-IN per client. Plus M11: voice books via `book_slot` into `bookings` | 10 | Code + `voice/evals/*.yaml` in Actions | `pipecat eval` green; VAD non-null; no voice/WhatsApp double-book |
| P1-W2-04 | M8 bridal enquiry flow; M10 done/no-show via owner's 9 PM list; review asks only for completed visits | 10 | `engine.js`, `reminders.js` | T15 passes; no review ask to no-shows |
| P1-W2-05 | Sales kit: A5 card (Telugu + English), proposal, agreement + privacy notice + processor clause, objection sheet | 20 | Proposal Writer, Objection Coach | Approved, prices match §2 |
| P1-W2-06 | Manual billing (S8): invoice + UPI QR + paid flag (no GST under ₹20 lakh turnover) | 10 | `invoices` table + generator | Test invoice renders |
| P1-W3-01…06 | Walk-in blocks (2 a week × 3 weeks) | 60 each | Visit sheets, personalised demos, Nudger | ≥1 founding salon signed by 9 Nov |
| P1-W4-01 | Onboard founding salon #1 (checklist below) | 60 + 30 | Onboarding Ops, Config, Templates, QA | All 13 steps ticked |

### Onboarding checklist per client (target: live in ≤5 working days)

| # | Step | Who | Blocks go-live? |
|---|---|---|---|
| 1 | Agreement, privacy notice, 50% advance | Owner, Akhil | Yes |
| 2 | Salon's own Meta Business portfolio + Facebook Page | Owner (20-min call) | Yes |
| 3 | Add Kalpa Labs as **partner**. No passwords or OTPs ever shared | Owner | Yes |
| 4 | Number not used on any WhatsApp app → WhatsApp Manager → **display name approved** | Owner + Akhil | Yes |
| 5 | **Payment method** in WhatsApp Manager; INR billing (required by 31 Dec 2026) | Owner | Yes (no payment method means no delivery) |
| 6 | Business verification: GST, or Udyam, or business PAN + utility bill | Owner | **No.** Unverified accounts get 250 business-initiated users per 24 h, enough for reminders. Finish within month 1 |
| 7 | App + system-user token in the *salon's* portfolio; Akhil pastes it into Netlify env himself | Akhil | Yes |
| 8 | `node tools/create-templates.js salon <WABA_ID>` (+ owner alert; Telugu/Hindi later) | Agent | Reminders need approval |
| 9 | Config from the price-board photo: catalog + durations, hours, weekly off, holidays, review link | Agent; owner approves prices | Yes |
| 10 | T01–T25 on the client config (≥22 pass) + 10 live test chats | Agent + owner | Yes |
| 11 | Staff card: take over a chat, resume bot, mark done/no-show, add walk-in | Agent | No |
| 12 | Go live: counter QR standee, review link, record a 4-week baseline | Owner + Akhil | No |
| 13 | Day-3 and day-14 health checks | Agent; Akhil 5 min | No |

### Month 2 (10 Nov – 9 Dec)

| ID | Quest | Akhil | Agent | Done-check |
|---|---|---|---|---|
| P1-M2-01 | WhatsApp Flows booking form (Meta `book-appointment` example, MIT) in `core/functions/flow.js`; chat steps kept as fallback | 10 | Build + whatsapp-api-js webhook mocks | ≤3 service messages per booking |
| P1-M2-02 | **Slot engine phase 2:** service durations, 30-min grid, per-stylist capacity, breaks, walk-ins (S1, A7–A9) | 10 | `core/slots.js`, config `staff[]` | Keratin/bridal duration tests pass |
| P1-M2-03 | Message cost meter: `messages.template` + category; ₹ in the owner report | 5 | `adsbot.js` weekly summary | Within 10% of WhatsApp Manager |
| P1-M2-04 | Owner WhatsApp commands: daily list, close-the-day, leave, walk-in, holiday (S4, S5) | 5 | Parser, owner number only | Support < 45 min/salon |
| P1-M2-05 | **Shared inbox phase 2:** assignment, notes, phone PWA, unread badge (wacrm) | 10 | Port components | Receptionist replies in < 1 min |
| P1-M2-06 | a3 picks: extruct + ≤2 contact pages in `leadfinder/enrich.py`, email-validator; `seo/seo_bot.py` contrast/favicon/llms.txt; `.github/workflows/seo-lighthouse.yml` | 5 | Code + tests | Lighthouse SEO ≥0.9 |
| P1-M2-07 | Nightly Supabase backup via Actions (encrypted) | 10 | Workflow | Restore drill works |
| P1-M2-08 | Founding salons #2 and #3 | 60 × 6 | As above | 3 paying salons by 15 Dec |

### Month 3 (10 Dec – 9 Jan)

| ID | Quest | Akhil | Agent | Done-check |
|---|---|---|---|---|
| P1-M3-01 | Gym gate review on 15 Dec | 15 | Gatekeeper report | Go/no-go recorded |
| P1-M3-02 | Gym requirements pack (`pf.ba.gym`) + demo config | 10 | BA agent | MUST list ≤10 dev-days |
| P1-M3-03 | Gym walk-ins with a New-Year offer | 60 × 2 | Visit sheets from 114 gym leads | ≥1 gym proposal by 5 Jan |
| P1-M3-04 | Case study #1 (with the owner's consent) | 30 | Metrics SQL from `salon.md` §6 | Owner approves it |
| P1-M3-05 | Apply as Meta Tech Provider (embedded signup; Coexistence where offered in India) | 30 | App-review material | Submitted |
| P1-M3-06 | Spend check: Supabase Pro + Netlify Personal if MRR ≥ ₹6,000 | 10 | Cost Watcher | Done or deferred with a reason |
| P1-M3-07 | Voice for the first Pro client: client-paid Plivo number, inbound only | 20 | Configure, evals | ≥8 of 10 test calls handled end to end |

---

## 6. Agent swarm

Activate the salon team in `00-hq/agents/registry.js` now. Gym, exam-kit and real-estate teams wake when their gate opens. Five agents are new.

| id | Role | runs_as | Cadence | Validator |
|---|---|---|---|---|
| b1.salon.prospector / enricher / scorer | Visit clusters from OSM + own-site enrichment | code | weekly Sun | Hyderabad only; no Maps/Justdial/IG scraping; cosmetics shops dropped |
| b1.salon.pitch / demo / objections / proposal / nudger | Sales chain | claude | per visit; nudger daily | ≤80 words; no guarantees; max 3 follow-ups |
| b1.salon.onboarding / config / templates | Delivery checklist | human / claude / code | per signing | 13 steps ticked; 0 wrong prices |
| b1.salon.concierge / calendar / reminders / reporter | Live bot | code | event / hourly | QA swarm green; T01–T25 ≥22 |
| b1.salon.health / faqgrow | Client success | claude | weekly Fri | DB numbers only; owner approves answers |
| **b1.salon.costmeter** (new) | Meta spend per client by category | code | weekly Mon | Within 10% of WhatsApp Manager |
| **b1.billing** (new) | Invoices, UPI links, due reminders, dunning | code + claude | daily | Matches agreement; no suspension without Akhil |
| **b1.support.triage** (new) | Sorts owner requests into config / bug / question, drafts the fix, logs minutes | claude | daily | Closed or escalated in 24 h |
| **b1.gatekeeper** (new) | Computes setup gates (§4) and kill criteria (§7) | claude | weekly Mon | Data from Supabase/Sheet only; dated verdict |
| **pf.policy.whatsapp** (strengthened) | Task-scope, escalation path, opt-in by category, quality rating | claude | weekly Mon | Sampled chats contain no open-domain answers |

### Meta's 2026 AI-chatbot policy

Since 15 Jan 2026, WhatsApp's Business Solution terms bar "AI providers" whose general-purpose assistant is the main product. Businesses that use AI to serve their own customers (support, bookings, updates) are still explicitly allowed. The Business Messaging Policy also requires "prompt, clear, and direct escalation paths": an in-chat human, a phone number or a store visit.

What this means for BotBhai:
1. **Stay task-scoped.** Prices, booking, FAQ. The Groq LLM is used only for language and intent. Off-topic questions get a polite deflection plus the human option.
2. **The shared inbox is a policy requirement**, which is why it's in Weeks 2–4.
3. **Separate marketing opt-in**, and STOP is honoured immediately.
4. **Disclose the assistant on first contact.** Meta's policy page doesn't require it, but trust and DPDP notice do.
5. **Never market it as "ChatGPT on WhatsApp".** It is "your salon's booking desk".

---

## 7. Metrics & kill criteria

**Weekly (Gatekeeper, Mondays):**
- **Sales:** visits, demos, proposals and closes. Targets: visit→demo ≥35%, proposal→close ≥25%.
- **Product:** chat→booking ≥25%, unanswered <10%, p95 reply <10 s, no-shows ≤5–7%, opt-outs <2%, quality rating green on every number.
- **Money and time:** MRR, receivables older than 7 days, support minutes per client (≤45/mo), Meta spend vs estimate, Netlify credits used.

**Kill rules:**
- **31 Jan 2027:** fewer than 2 paying salons after ≥40 visits → pause salon outbound. Existing clients go on maintenance, and selling hours move to the next-best world (P0's call).
- **30 Apr 2027:** BotBhai MRR < ₹10,000, or support > 60 min per client per month → maintenance only, no new setups.
- **Any time:** a client number restricted twice, or a policy notice → no new onboardings until fixed.
- **Per setup:** no paying client 60 days after its gate opens → close that setup again.

---

## 8. What I need from Akhil

- [ ] Approve the price ladder and the founding offer (3 salons at ₹2,999 + ₹1,499/mo).
- [ ] Fix two weekly walk-in hours (suggested: Tue and Sat, 11:30 AM–12:30 PM).
- [ ] Create the Kalpa Labs Meta Business portfolio and submit verification with the Udyam certificate. Do it yourself and never share logins or OTPs in chat.
- [ ] Buy one prepaid SIM (~₹250) for the demo/sales number.
- [ ] Set up a UPI QR or current account in Kalpa Labs' name.
- [ ] Approve the agreement, privacy notice and processor clause before the first signing.
- [ ] Say "deploy" after green tests. Paste client tokens into Netlify yourself.
- [ ] Approve spends as they come up:
  - printing ₹300–500 (Week 2)
  - a BotBhai domain, ~₹800/yr (at the first signing)
  - Supabase Pro + Netlify Personal, ~₹3,000/mo (when MRR ≥ ₹6,000)

---

## 9. Sources

- Meta, WhatsApp pricing (per-message, 72 h free entry point, INR billing by 31 Dec 2026): https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing.md
- TelecomTalk, India rates from 1 Oct 2026 (service 1,000 free then ₹0.115; utility ₹0.115 in-window; marketing ₹0.8631; payment method mandatory): https://telecomtalk.info/whatsappbusiness-price-reveal-telegram-arattai-may-benefit/1012403/
- AiSensy, October 2026 update: https://m.aisensy.com/blog/whatsapp-pricing-update-october-2026/
- Go4whatsup, October 2026 change: https://www.go4whatsup.com/pricing/whatsapp-october-2026/
- *Conflict:* Meta's developer page (read 13 Oct 2026) doesn't list India among the October changes, while three Indian sources do. Verify on the WhatsApp Manager INR rate card.
- TechCrunch, general-purpose chatbot ban (15 Jan 2026): https://techcrunch.com/2025/10/18/whatssapp-changes-its-terms-to-bar-general-purpose-chatbots-from-its-platform
- respond.io, chatbot policy 2026: https://respond.io/blog/whatsapp-chatbot-policy-2026
- WhatsApp Business Messaging Policy: https://whatsappbusiness.com/policy/
- Chatarmin, messaging limits (portfolio-level, 250 unverified): https://chatarmin.com/en/blog/whats-app-messaging-limits
- Zoko, verification without GST: https://www.zoko.io/post/whatsapp-business-api-no-gst-number
- Chakra, Coexistence: https://chakrahq.com/article/whatsapp-coexistence-business-app-register-cloud-api/
- Codingclave, AiSensy pricing 2026: https://codingclave.com/blog/aisensy-pricing-india-2026
- Codingclave, salon software cost India 2026: https://codingclave.com/guides/salon-management-software-cost-india-2026
- Plivo India pricing: https://www.plivo.com/voice/pricing/in/
- Sarvam pricing: https://docs.sarvam.ai/api-reference-docs/pricing.md
- Netlify free plan 2026: https://netli.fyi/blog/netlify-free-plan-limits-2026
- Supabase free tier 2026: https://automationatlas.io/answers/supabase-free-tier-limits-2026/
- GST threshold for services: https://cleartax.in/s/gst-registration-limits-increased
- DPDP Rules 2025 (notified 13 Nov 2025, phased): https://www.hoganlovells.com/en/publications/indias-digital-personal-data-protection-act-2023-brought-into-force-
- Internal: `01-botbhai/research/a1-whatsapp-booking.md` (wacrm, cal.diy, whatsapp-api-js, Flows), `a2-voice.md` (VAD bug, smart-turn, Bolna), `a3-leads-seo.md` (extruct, Lighthouse CI, email-validator), `01-botbhai/botbhai/docs/requirements/salon.md`.

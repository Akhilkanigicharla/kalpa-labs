# P2 — JobCard (world b2): plan to first rupee and steady monthly income

Planning agent P2, 2026-10-13. Inputs: `00-hq/research/BRIEF.md`, `02-jobcard/README.md`, `00-hq/research/github/a4-jobcard.md` (A4), `a2-voice.md`, `01-studio/botbhai/core/functions/whatsapp.js`. Prices and policies below were checked on the web today (see Sources).

## 1. Verdict

JobCard makes money by selling AC and appliance technicians in Hyderabad a monthly subscription. A technician speaks a Telugu or Tenglish voice note after a job. JobCard turns it into a job card, a proper invoice PDF with a UPI QR code, and a reminder 6 months later to call the customer for the next service. **Do not build the Expo app first.** Week 1 is a demo and pre-sale. Weeks 2–4 are a **WhatsApp-only bot** that reuses BotBhai's webhook. The Play Store app comes in month 3, and only after 10 or more technicians are paying.

**Realistic income, by month:**

| Month | Low | Likely | High |
|---|---|---|---|
| 1 (Nov 2026) | ₹0 | ₹300 (3 founding members × ₹99) | ₹1,000 |
| 3 (Jan 2027) | ₹500 | ₹2,000 (about 14 paying) | ₹6,000 |
| 6 (Apr 2027, peak season) | ₹1,500 | ₹6,000 (about 40 paying) | ₹15,000 |
| 12 (Oct 2027) | ₹3,000 | ₹15,000 (about 100 paying) | ₹45,000 |

**Single biggest risk:** technicians try it once and drift back to paper and plain WhatsApp chats. Many of their customers pay cash and never ask for a bill, and myBillBook already sells a ₹399/year invoice app. JobCard only survives if the AMC and repeat-service reminders bring the technician visible extra jobs. That has to be proven in the Mar–Jun 2027 summer peak.

## 2. Customer and offer

**Who pays:**
- Independent AC/fridge/washing-machine technicians and 2–5 person repair shops in Hyderabad. They speak Telugu first, use an Android phone costing ₹8–15k, and get work from referrals, JustDial and word of mouth.
- Second wave: small authorised-service franchises that already use paper job cards.

**The pain:**
- They have no record of past customers, so repeat services (₹450–600 each) are lost.
- Handwritten or no bills look unprofessional to offices and apartment associations, which want a GST bill for AMC contracts.
- Typing on the phone is slow, so voice beats forms.

**Why they buy now:** the off-season (Oct–Feb) is when they have time to learn. The summer rush is when reminders pay off. Urban Company charges ₹499–599 for a foam/power-jet service in Hyderabad. **One extra repeat job a month pays for 3–4 months of JobCard.** That is the whole sales pitch.

**Price ladder** (Kalpa Labs is not GST-registered, so prices are flat, with no GST added):

| Plan | Price | What they get |
|---|---|---|
| Free | ₹0 | 10 job cards/month, Bill of Supply PDF with "Made with JobCard" footer, 20 voice minutes |
| Founding member (first 30 only) | ₹99/month for 3 months, then ₹149 | Everything in Pro, plus Akhil's personal setup |
| **Pro** | **₹149/month** or ₹1,490/year | Unlimited job cards, 150 voice minutes, GST tax invoice or bill of supply, own logo and UPI QR, 6-month AMC reminders, customer history, monthly CSV export |
| Team | ₹299/month | Pro for the owner plus 2 helper phones, shared customer list, AMC dashboard, 400 voice minutes |

Over-quota minutes are not sold in month 1–3. Users are asked to keep notes under 2 minutes, which caps STT cost.

**Competitors the technician already has:**

| Alternative | Price | Why JobCard still wins |
|---|---|---|
| myBillBook (Silver, Android) | ₹399/year; higher plans about ₹1,700–2,900/year | Typed GST billing for shops. No voice, no Telugu dictation, no service reminders |
| Vyapar | Mobile free; desktop from about ₹3,399/year + GST | Same as above. Built for traders' stock and accounts, not for field jobs |
| FieldWeb FSM | ₹400–500/month | Built for companies dispatching technicians, in English, form-heavy |
| Zoho Invoice / WhatsApp Business app | Free (Zoho caps invoices each year) | Free, but the technician must type everything and set reminders himself |

**Pricing logic:** ₹149 is more than myBillBook's yearly price, so **never pitch JobCard as "billing software."** Pitch it as "speak, and get the bill, the customer list and next season's repeat jobs." The free tier is there to beat "Vyapar is free." If month-2 interviews show ₹149 is too high, test ₹99 Pro for new sign-ups, not discounts for existing users.

## 3. Unit economics (per paying user per month)

Assumptions: a Pro user does about 40 jobs a month off-season and about 120 in peak, with notes of about 45 s.

| Cost line | Off-season | Peak | Notes |
|---|---|---|---|
| Sarvam STT (₹30/hour, billed per second) | 30 min = ₹15 | 90 min = ₹45 | Quota of 150 min caps it at ₹75 |
| LLM to extract fields as JSON (Sarvam-30B at ₹2.5 / ₹10 per 1M tokens) | under ₹1 | about ₹1 | About 1,500 input + 400 output tokens per note |
| WhatsApp bot replies (3 per job) | 120 msgs: free within 1,000/number/month | 360 msgs × ₹0.136 = ₹49 | Since 1 Oct 2026 Meta charges replies beyond 1,000/month at the utility rate (₹0.115 + 18% GST) |
| AMC reminder template to the technician | about 10 × ₹0.136 = ₹1.4 | ₹1.4 | Utility template |
| Supabase / Netlify / EAS | ₹0 on free tiers | ₹0 | See limits below |
| Payment fees | Razorpay web: about 2.4% + 1% subscription fee ≈ ₹5. UPI direct to Kalpa's account: ₹0 | same | Play Billing would take 15% = ₹22 |
| **Total cost** | **about ₹20–25** | **about ₹75–100 on the WhatsApp channel** | |

**Gross margin at ₹149:**
- Off-season: about 85%.
- Peak on the WhatsApp bot: about 40–50%. This is why the app (or PWA) must replace the bot for heavy users before summer, because app traffic does not use paid WhatsApp messages.
- Peak in the app: STT only, about ₹45, so about 70% margin.

**Fixed costs:** ₹0 while everything fits in free tiers.

**Break-even:**
- Supabase Pro ($25/month, about ₹2,200) needs about 18 Pro users to cover it.
- The Google Play developer fee ($25 one-time) is covered by the first month of 15 users.

**Where the free tiers run out first:**

| Limit | Free amount | When it hits |
|---|---|---|
| Supabase storage | 1 GB | Audio is about 100 KB per note, so roughly 100 user-months. Fix: keep audio 60 days in the cloud, then on the phone only |
| Supabase database | 500 MB | Not before about 2,000 users |
| Supabase pause rule | Pauses after 7 idle days | Keep it alive with a daily GitHub Actions ping. **Move to Pro before the first 20 paying users depend on it** |
| Meta free replies | 1,000 per number per month | Hits at about 8 active bot users |
| Sarvam free credit | ₹100 | Covers about 3 hours (240 demo notes). After that it's pay-as-you-go, at under ₹50 per paying user |
| EAS Build | 15 Android builds | Enough for month 3 |

**Spend triggers (say yes when these happen):**
- Sarvam top-up of ₹500 when the first 3 people pay.
- Play developer fee ($25) when 10 people are paying.
- Supabase Pro when 18 people are paying, or before Mar 2027, whichever comes first.

## 4. Go-to-market

### Validation decision: WhatsApp-only MVP or Google-Form concierge?

**Use the WhatsApp bot, after one week of demo and pre-sale.** A Google-Form concierge tests the wrong thing: typing into forms is exactly the pain we remove, and Akhil can't hand-process notes in 1 hour a day. Google Forms are used only for the waitlist, with a consent line.

**Week 1 gate:** 15 conversations, at least 6 people who say "I'd use this daily", and **at least 3 who pay ₹99 by UPI** for the founding month. If fewer than 3 pay, stop. Write up why in `02-jobcard/docs/interviews.md` and move the hour to another world.

### First 10 customers (about 20 min a day, plus two 60-minute field visits)

1. **Agent prep, day 1.** Build a 45-second screen-recorded demo: Akhil speaks a Telugu note, and a PDF invoice with a UPI QR comes back. Write a Telugu and English interview script (8 questions: jobs per week, how they bill today, how they remember repeat customers, GST customers, phone model, what they'd pay). Write a one-page Telugu flyer with a QR code to the waitlist form.
2. **Spare-parts counters (best channel).** Technicians visit refrigeration-spares shops almost daily.
   - Visit 2–3 shops in one cluster, such as the Ranigunj/Secunderabad and Abids-area spares markets or a large local spares dealer near home.
   - Ask the owner to let you stand at the counter for 45 minutes and to keep the flyer on the counter.
   - Offer the shop a free Team plan, plus a ₹50 UPI thank-you for each technician who pays for 2 months. Record it in writing as a referral fee, not a hidden commission.
3. **Technician WhatsApp groups.** Ask each interviewed technician and shop owner which groups they're in. **Post only with the admin's permission:** one message with the demo video, never repeated, never added to groups without asking. Respect group rules (Meta policy, no spam).
4. **Personal follow-up.** Each day, message 5 warm leads one-to-one. The agent drafts; Akhil sends from his phone. Follow up on day 2 and day 5, and stop after a "no."
5. **Onboarding call (10 min each).** Save the bot number, send the first voice note together, send the first PDF to a real customer. Founding members pay ₹99 by UPI QR to Kalpa Labs' current account and get a receipt.
6. **Daily quota:** 5 personal messages and 1 onboarding. Field visits happen twice a week inside the 60-minute quest.

### Urban Company partners

- They are a large, skilled pool, but UC's terms likely forbid moving UC customers off-platform. **Never pitch "take UC customers direct."**
- Pitch only for their own non-UC customers and family referrals, and tell them to check their partner agreement.
- They are a secondary channel, not the main one.

### From 10 to 100 customers

- **Referral built into the PDF:** every invoice footer says "Bill made by voice with JobCard". Each technician gets a code for one free month per paying referral.
- **Spare-parts shop network:** go from 3 to 15 shops across Kukatpally, Dilsukhnagar, Ameerpet, LB Nagar and Secunderabad. Reuse BotBhai's OpenStreetMap lead finder for *shops* only (business listings, not consumer data). No Justdial or Google Maps scraping.
- **YouTube/Instagram Reels in Telugu:** "AC technician bill in 10 seconds". Use real customers, with their permission.
- **Before summer (Feb 2027):** ask each user to import past customers so the March reminders fire. That is the moment JobCard proves its money.
- **Team plan for small service shops** with 3–8 technicians, sold through the owners already met at the counters.

## 5. Build plan (quests of 60 minutes or less)

Repo home: `02-jobcard/`. The A4 ADOPT picks are built in this order:
1. Sarvam STT over REST from an Edge Function.
2. `expo-print` HTML template with embedded Noto Sans Telugu.
3. `upiqrSync`.
4. Obytes template.
5. `expo-speech-recognition`.
6. `expo-sqlite` with an outbox.
7. PowerSync in phase 2.
8. RevenueCat if Play Billing is used.

**No AGPL invoice code is copied.**

### Week 1: demo and pre-sale

| id | Quest | CEO action | Agent action | Done when |
|---|---|---|---|---|
| b2.q01 | Approve plan + gate | Read section 1/4, say go (10 min) | Log decision in `02-jobcard/docs/decisions.md` | File committed |
| b2.q02 | Voice demo pipeline | Put BotBhai's Sarvam key into a Codespaces secret (5 min) | Write `02-jobcard/demo/voice_to_invoice.mjs`: audio → Sarvam STT (translate mode + original) → Sarvam-30B JSON (Zod schema from A4) → `02-jobcard/src/features/invoice/template.ts` HTML → PDF | 5 sample notes give correct totals; Telugu text renders |
| b2.q03 | Record real notes | Record 8 Tenglish notes with AC jargon ("R32 gas", "PCB", "1.5 ton") (15 min) | Run them through Sarvam and the Groq Whisper that BotBhai uses today; score field accuracy | `02-jobcard/docs/stt-eval.md` with accuracy for each engine |
| b2.q04 | Demo video + flyer | Screen-record the demo (15 min) | Write the Telugu/English script, flyer, and Google Form waitlist with DPDP consent text | Video under 45 s; flyer PDF |
| b2.q05 | Field visit 1 | 60 min at a spares counter, 6–8 talks | Turn voice memos into notes in `docs/interviews.md` | 6 or more interviews logged |
| b2.q06 | Field visit 2 / calls | 60 min | Same | 15 total; count of ₹99 payments |
| b2.q07 | **Go/no-go** | Decide (10 min) | Summarise evidence against the gate | Go only if 3 or more paid |

### Weeks 2–4: WhatsApp-only MVP

| id | Quest | CEO action | Agent action | Done when |
|---|---|---|---|---|
| b2.q08 | Second WhatsApp number | Add a spare SIM as a new number under the existing BotBhai Meta business; agent gives step list (45 min) | Prepare the checklist and 2 utility templates (AMC reminder, monthly summary) | Test message received |
| b2.q09 | JobCard webhook | — | Write `02-jobcard/bot/functions/jobcard.js`, modelled on `01-studio/botbhai/core/functions/whatsapp.js` (signature check, dedupe). Voice note → `02-jobcard/supabase/functions/transcribe-extract/index.ts` → reply with the parsed card for a "✅ / edit" check → PDF via headless render → send as document | 20 test notes; 0 wrong totals; reply under 30 s |
| b2.q10 | Supabase schema + RLS | Create the Supabase project (free) (10 min) | Write `02-jobcard/supabase/schema.sql`: technicians, customers, job_cards, invoices, amc_contracts, usage_minutes; RLS on; FY invoice series `JC/26-27/0001` | Policy tests pass |
| b2.q11 | Reminders + quota | — | Daily cron sends the technician an "these 5 customers are due" template with a `wa.me` link and prefilled Telugu text he sends himself; minute quota per plan | Unit tests; quota blocks at the limit |
| b2.q12 | CA check of invoice format | Send the sample PDFs to a CA friend (20 min) | Prepare questions: SAC 9987xx code (sources differ between 998715 and 998717), 18% rate, Bill of Supply wording, composition dealers | Written reply saved in `docs/decisions.md` |
| b2.q13 | Onboard founding members | 3 × 10-min calls | Write the onboarding checklist and the privacy notice (technician is the data fiduciary for his customers; Kalpa is the processor) | 3 or more technicians sending real notes |
| b2.q14 | Payment collection | Turn on the Razorpay account (free, no setup fee) or keep UPI QR (20 min) | Web payment link page on Netlify; renewal nudge messages | First ₹149 collected |

### Month 2: retention and a PWA

| id | Quest | CEO action | Agent action | Done when |
|---|---|---|---|---|
| b2.q15 | PWA "my customers" | — | Write `02-jobcard/web/` (Netlify): phone-OTP login, customer list, AMC due list, invoice history, mic-record → same Edge Function (moves heavy users off paid WhatsApp messages) | Lighthouse PWA check passes; works at 390 px |
| b2.q16 | Weekly health review | 15 min/week | Health agent reports active technicians, notes per technician, failed transcripts | Report every Monday |
| b2.q17 | Price test | Approve the variant | ₹99 vs ₹149 Pro for new sign-ups only | 20 or more sign-ups per arm, or decide on judgement |
| b2.q18 | Shop network to 10 | 2 visits | Shop referral tracker | 10 shops, referral codes live |

### Month 3: Android app (only if 10 or more are paying)

| id | Quest | CEO action | Agent action | Done when |
|---|---|---|---|---|
| b2.q19 | Scaffold app | — | Obytes template → `02-jobcard/src/`, `npx expo install --fix`, add `te.json`/`hi.json`, delete `features/feed` | `tsc` + Jest green in Codespaces |
| b2.q20 | Offline voice + local DB | — | `expo-speech-recognition` (`te-IN`, `persist: true`), `expo-sqlite` + outbox, `expo-print` + `expo-sharing` share to WhatsApp, local reminder notifications | Works in airplane mode; syncs later |
| b2.q21 | Play account + billing | Pay $25, verify identity (45 min) | RevenueCat + Play Billing for ₹149/₹299; web subscribers keep their plan by logging in. No in-app links to web payment | Internal test purchase works |
| b2.q22 | Closed test | Invite 12+ paying users as testers | Track 14 days of engagement | Production access granted |
| b2.q23 | Pre-summer import | Tell every user (template) | CSV/contacts import of past customers | 50%+ of users have 20+ customers saved by 28 Feb 2027 |

## 6. Agent swarm (registry style, adds to the lean `b2.*` team in `00-hq/agents/registry.js`)

```js
A({ id:"b2.research.interviews", name:"Technician Interview Synthesiser", unit:"b2", team:"research", mission:"Turn field notes into pains, willingness to pay, objections; update go/no-go.", trigger:{event:"after field visit"}, runs_as:"claude", tokens:4000, kpi:"Gate decided on evidence", validator:{checks:["counts match interviews.md","no customer names or phones stored"]} }),
A({ id:"b2.sales.pitch", name:"Telugu Pitch Writer", unit:"b2", team:"marketing", mission:"Scripts, flyer, group post, Reels lines in Telugu + English.", trigger:{cron:"weekly:tue"}, tokens:3000, kpi:"≥20% demo→trial", validator:{checks:["no income guarantees","prices match plan table","admin-permission line for groups"]} }),
A({ id:"b2.sales.nudger", name:"Follow-up Nudger", unit:"b2", team:"marketing", mission:"Daily list of 5 warm leads with drafted message; day 2/5 follow-ups.", trigger:{cron:"daily"}, tokens:800, kpi:"No warm lead silent >5 days", validator:{checks:["max 2 follow-ups","stops on no"]} }),
A({ id:"b2.sales.shops", name:"Spares-Shop Partner Manager", unit:"b2", team:"marketing", runs_as:"human", human_needed:true, mission:"Keep counter flyers and referral codes alive at partner shops.", trigger:{cron:"weekly:sat"}, tokens:500, kpi:"≥30% of sign-ups via shops", validator:{checks:["referral fee written and paid by UPI"]} }),
A({ id:"b2.dev.pipeline", name:"Voice→JobCard Pipeline Dev", unit:"b2", team:"tech", runs_as:"code", code:"02-jobcard/supabase/functions/transcribe-extract/index.ts", mission:"Sarvam STT + LLM JSON extraction + validation.", trigger:{event:"voice note"}, tokens:0, kpi:"≥90% fields right without edit", validator:{name:"STT Eval Tester", checks:["stt-eval set of 30 real clips re-run on every change","keys only in function secrets"]} }),
A({ id:"b2.dev.invoice", name:"Invoice Template Dev", unit:"b2", team:"tech", runs_as:"code", code:"02-jobcard/src/features/invoice/template.ts", mission:"GST Tax Invoice / Bill of Supply PDF with UPI QR and Telugu font.", trigger:{event:"job closed"}, tokens:0, kpi:"0 wrong totals", validator:{name:"GST Math Tester", checks:["CGST+SGST vs IGST cases","amount in words lakh/crore","series ≤16 chars per FY"]} }),
A({ id:"b2.dev.bot", name:"JobCard WhatsApp Bot", unit:"b2", team:"tech", runs_as:"code", code:"02-jobcard/bot/functions/jobcard.js", mission:"Receive notes, confirm card, send PDF, send due-list template.", trigger:{event:"WhatsApp message"}, tokens:0, kpi:"Reply <30 s", validator:{checks:["signature verified","dedupe on message id","task-specific bot only (Meta policy)"]} }),
A({ id:"b2.dev.app", name:"Expo App Builder", unit:"b2", team:"tech", runs_as:"planned", mission:"Obytes-based offline app from month 3.", trigger:{event:"10 paying users"}, tokens:20000, kpi:"Closed test passed", validator:{checks:["tsc + jest green","works offline"]} }),
A({ id:"b2.success.onboard", name:"Onboarding Coach", unit:"b2", team:"success", mission:"Checklist + first-note call script; flag users with 0 notes after 3 days.", trigger:{event:"sign-up"}, tokens:1000, kpi:"80% send a real note in 48 h", validator:{checks:["privacy notice shown and accepted"]} }),
A({ id:"b2.success.health", name:"Technician Health Monitor", unit:"b2", team:"success", runs_as:"code", mission:"Weekly active technicians, notes/tech, reminders sent, churn risk.", trigger:{cron:"weekly:mon"}, tokens:0, kpi:"Churn flagged 2 weeks early", validator:{checks:["numbers from database only"]} }),
A({ id:"b2.ops.cost", name:"STT & Message Cost Watcher", unit:"b2", team:"ops", mission:"Sarvam minutes, Meta charged messages, Supabase storage per user; warn at 50/75/90% of quota and free tier.", trigger:{cron:"weekly:sun"}, tokens:1500, kpi:"Cost/user ≤ ₹40 off-season", validator:{checks:["figures from provider dashboards"]} }),
A({ id:"b2.policy", name:"JobCard Policy Checker", unit:"b2", team:"validation", mission:"Play Payments policy, DPDP roles, GST invoice rules, WhatsApp policy, UC partner-terms caution.", trigger:{cron:"monthly"}, tokens:3000, kpi:"0 policy strikes", validator:{checks:["every claim has a source link","CA sign-off on invoice format"]} }),
```

## 7. Metrics and kill criteria

**Weekly numbers:**
- Interviews.
- Paid founding members.
- Weekly active technicians (1 or more notes).
- Notes per active technician.
- Share of cards accepted without edits.
- Reminders sent → repeat jobs reported.
- Paying users and churn.
- Cost per user.
- Referral share.

**Kill or pause rules:**
- **20 Oct 2026:** fewer than 3 people paid ₹99 after 15 interviews → pause b2, archive the notes.
- **30 Nov 2026:** fewer than 5 paying users, or under 50% of payers active weekly → pause.
- **31 Jan 2027:** fewer than 15 paying users, or monthly churn over 15% → no app build. Keep the bot running for existing users only.
- **30 Jun 2027 (after the first peak):** under ₹5,000/month recurring, or fewer than 30% of users reporting at least 1 repeat job from reminders → pause and move the hour to the best-performing world.

## 8. What I need from Akhil

- [ ] Say go on the Week 1 gate and the founding price of ₹99 (b2.q01).
- [ ] Put the existing Sarvam key into a Codespaces secret yourself. Never paste it in chat.
- [ ] Record 8 real Tenglish voice notes, and later collect 20 real ones from technicians (with their OK).
- [ ] Do two 60-minute field visits in Week 1 at spares counters you can reach easily.
- [ ] Get a spare SIM for the JobCard WhatsApp number. Confirm the BotBhai Meta business is verified and has a payment method.
- [ ] Find a CA contact for one invoice-format review.
- [ ] Decide on the UPI QR to Kalpa Labs' current account now; decide on Razorpay at the first ₹149.
- [ ] Approve later spends: Sarvam top-up of ₹500 (at 3 payers), Play fee of $25 (at 10 payers), Supabase Pro (at 18 payers or by Mar 2027).

**Play Store vs PWA decision:** WhatsApp bot, then PWA, then Play app. Play needs a $25 fee and, for new personal accounts, 12 testers opted in for 14 days. It also needs Google Play Billing for a digital subscription (15%) or the India alternative-billing program (only 4% lower, and it needs PCI-DSS certification). Selling on the web with Razorpay/UPI is allowed outside Play. Inside the Play app we must not link to web payment.

## 9. Sources

- Sarvam pricing (STT ₹30/hour; ₹100 free credit; Sarvam-30B ₹2.5/₹10 per 1M tokens): https://docs.sarvam.ai/api-reference-docs/pricing.md
- Google Play alternative billing in India (fee reduced by 4%; Play billing must still be offered): https://support.google.com/googleplay/android-developer/answer/13306652
- Google Play Payments policy (billing required for digital subscriptions; no steering; physical services exempt): https://support.google.com/googleplay/android-developer/answer/9858738
- Play enforcement in India (2024): https://www.dtnext.in/lifestyle/technology/google-begins-to-enforce-play-store-policies-in-india-to-remove-non-compliant-apps-771158
- Play closed testing (12 testers, 14 days): https://www.testerscommunity.com/blog/google-play-closed-testing-requirements-2026
- WhatsApp pricing changes (1 Oct 2026: 1,000 free replies/number/month, utility in window charged): https://baat.ai/blog/whatsapp-api-pricing-india
- WhatsApp India rates (utility ₹0.115, marketing ₹0.8631, + GST): https://montymobile.com/blogs/whatsapp-business-api-pricing-in-india-inr-rates-gst-and-the-2026-currency-migration-deadline
- Urban Company Hyderabad AC prices: https://www.urbancompany.com/hyderabad-ac-service-repair-uppal
- Urban Company partner commission share (28.3%): https://inc42.com/?p=571319
- myBillBook Silver ₹399/year: https://freetrial.mybillbook.in/silver-plan-for-android.html ; other plans: https://www.saasworthy.com/product/mybillbook/pricing
- Vyapar prices: https://www.itforsme.in/pricing/vyapar-india ; https://pricingsaas.com/companies/vyapar
- FieldWeb FSM prices: https://techjockey.com/detail/fieldweb
- Zoho Invoice free with limits: https://zoho.com/invoice/kb/general/invoices-creation-free.html
- Razorpay fees and subscriptions: https://razorpay.com/blog/razorpay-payment-gateway-pricing-explained/
- Supabase free tier: https://automationatlas.io/answers/supabase-free-tier-limits-2026/
- Expo EAS free plan: https://expo.dev/pricing.md
- Gemini free tier and data-use caveat (why we don't send customer data to free Gemini): https://agentdeals.dev/gemini-api-pricing-changes
- SAC 9987 for appliance repair: https://www.gimbooks.com/blog/maintenance-repair-installation-services-9987-hsn-code-gst-rate/amp/ ; https://busy.in/sac-code-998717/
- DPDP Rules 2025 phases (core duties from 13 May 2027): https://ssrana.in/articles/meity-notifies-final-digital-personal-data-protection-rules-2025/
- Internal: `00-hq/research/github/a4-jobcard.md`, `a2-voice.md`, `01-studio/botbhai/core/functions/whatsapp.js`

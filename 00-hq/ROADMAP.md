# 🗺️ Kalpa Labs · Roadmap to "done"

One list for the whole company. Order follows [PLAN.md](PLAN.md) §5 (BotBhai first, then the agent-only engines b5, b3, b7, b6, then b2 and b4).

- **Agent queue:** Claude builds these automatically in the **Build sprint** sessions (11:07 and 23:07 IST). Each sprint takes the first unticked items, builds them, runs tests, ticks them `[x]` with the commit, and logs the work in `00-hq/log/`.
- **CEO queue:** only Akhil can do these (accounts, decisions, people). The morning brief assigns them.
- **Rules for every item:** free tiers only (build mode), no secrets in the repo, licence rule from `research/BRIEF.md`, tests must pass, and the validator check must be met before ticking.
- **"Done"** = every agent item ticked, and every world has hit its first gate in its PLAN.md §7 or been killed by that rule.

Status key: `[ ]` todo · `[~]` started (see log) · `[x]` done · `[!]` blocked (reason in log)

---

## Agent queue

### Sprint 1 · BotBhai sell-ready (b1) and design system
- [x] **A01** b1 · P1-W1-02/03: verify the MUST list (M1 confirm reply, M2 reminder flags, M3 IST, M5 "4pm", M6 "hair cut", M7 owner alert, M12 Telugu greeting, M13 opt-in gate, M14 home visit) against `botbhai/docs/requirements/salon.md`; fix any gap with a regression test. Check: `bash botbhai/tools/test-all.sh` green. (done 2026-10-13, 14079ae)
- [ ] **A01b** b1 · Restyle every BotBhai screen to the Kalamkari system (`00-hq/design/`): the demo (`web/index.src.html` → `build.py` → republish artifact https://claude.ai/artifact/JYxrRm9PHrw2SCBRFRPjUi with the Artifact tool), SEO-bot site templates (`seo/seo_bot.py`, fix the WhatsApp-button contrast from a3), and smile cards (`tools/cards.py`). Check: all tests green; 390 px Playwright screenshots in light + dark, no overflow.
- [x] **A02** b1 · P1-W2-01: slot engine `core/slots.js` (structured hours, weekly off, holidays, special hours, "closing for today", service durations) ported from cal.diy logic (MIT, attribute). Check: new unit tests + all suites green. (done 2026-10-13, f0b8d27)
- [x] **A02b** b1 · NLU gaps from Deep Scan v2 (`01-botbhai/research/deep-scan-v2-chat.md`): Telugu-script booking words, "cancel" when nothing is booked, service named in the first message, FAQ mid-flow then re-ask (Rasa digression). Check: regression tests for each + all suites green. (done 2026-10-13, 14079ae)
- [ ] **A03** b1 · P1-W2-04: bridal enquiry flow; owner's 9 PM done/no-show list; review ask only after completed visits. Check: T15 passes; no review ask to no-shows.
- [ ] **A04** b1 · P1-W2-02: shared inbox phase 1 (`web/inbox.html` + `core/functions/inbox.js`): paused chats, reply as the salon, resume bot; `assigned_to`, `status` columns. Check: webhook tests extended and green.
- [ ] **A05** b1 · P1-W2-06: manual billing: `invoices` table, invoice generator ("Invoice", no GST, Udyam no., series KL/26-27/NNN), UPI QR, paid flag. Check: sample PDF renders.
- [x] **A06** b1 · P1-W2-03: voice turn-taking fix in `voice/agent.py` per research a2 (Silero stop_secs 0.2, smart-turn analyzer, Sarvam TTS language). Check: `voice/test_prompt.py` passes in a venv with pipecat. (done 2026-10-13, b487bcf; plus `voice/test_turns.py`)
- [ ] **A07** b1 · P1-W2-05: sales kit in `01-botbhai/docs/sales/`: A5 card (Telugu + English), proposal, client agreement with DPDP processor clause, privacy notice, objection sheet. Check: prices match PLAN.md §2.
- [ ] **A08** b1 · P1-W1-06: cluster-1 visit sheet (SR Nagar/Ameerpet) from `botbhai/leads/hyderabad-leads.csv`: 6+ salons, map links, personalised pitch. Check: file in `01-botbhai/docs/sales/`.
- [x] **A09** design · Kalpa design system "Kalamkari": `00-hq/design/DESIGN-SYSTEM.md` + `tokens.css` + free UI toolkit (licences checked). Check: the three files exist and the toolkit list names each licence. (done 2026-10-13, add0d08)
- [ ] **A10** design · b1: `01-botbhai/design/` brief + HTML mockups for the owner dashboard and shared inbox (phone first). Use shadcn/ui-style components on the Kalamkari tokens. Check: renders at 390 px with no horizontal scroll (Playwright screenshot).
- [ ] **A11** design · b5 + b3: calculator page and kit landing page mockups. Check: 390 px Playwright screenshot.
- [ ] **A12** design · b6: Ledger Peaks landing + dashboard + X-ray report mockups. Check: 390 px screenshot.
- [ ] **A13** design · b2 + b4: JobCard app screens (record → job card → invoice) and Tab Lifeboat popup/options. Check: screenshots.
- [x] **A14** design · HQ: Kingdom control room redesigned in the Kalamkari system and republished; copy in `00-hq/design/kingdom-control-room.html`. Check: page republished; light + dark at 390 px. (done 2026-10-13, add0d08)

### Sprint 2 · Agent-only engines (start now, 0 CEO minutes)
- [x] **A15** b5 · b5.W1.1: Astro site in `05-deals/site/`, `fin.ts` SIP/EMI/tax (new + old regime FY 2026-27, cite source), vitest fixtures ₹12.75L / ₹13L / ₹25L. Check: `npm test` green, `npm run build` ok. (done 2026-10-13, 6208eb4)
- [x] **A16** b5 · b5.W2.1: calculators salary, FD, PPF, HRA in English + Telugu with FAQ schema. Check: fixtures pass. (done 2026-10-13, 6208eb4)
- [ ] **A17** b5 · b5.W4.1: GST, gratuity, RD calculators + Kits call-to-action. Check: 10 calculators build.
- [ ] **A18** b5 · b5.W1.3: `05-deals/site/src/bot/post.py` Telegram poster from `queue.csv` (dry-run mode, ASCI disclosure enforced). Check: unit test.
- [ ] **A19** b3 · K-02: GATE 2027 kit v1 (xlsx + Apps Script for Sheets): syllabus × papers, topic weights, revision scheduler, mock analyser, Lite version. Check: 25-item QA checklist in `03-kits/docs/qa.md`.
- [ ] **A20** b3 · K-08: Tax + SIP kit v1 with in-sheet tests (₹12.75L / ₹13L / ₹25L → 0 / 26,000 / 3,19,800 new; 1,40,400 / 1,48,200 / 5,22,600 old). Check: fixtures pass in a Python check of the formulas.
- [ ] **A21** b3 · K-06: delivery function (Razorpay signature verify, order log, per-buyer stamped PDF with pdf-lib) built and tested with fake payloads only. Check: tests green; no secrets.
- [ ] **A22** b3 · K-04: 14 days of daily-question posts for the Telegram channel. Check: file in `03-kits/docs/`.
- [x] **A23** b7 · Q7.1–Q7.3: licence note, `.gitignore` data, pinned requirements, `src/data.py` (cache + validation), `src/costs.py` (2026 Indian charges with sources). Check: pytest green on synthetic data. (done 2026-10-13, 1e5e4d5)
- [x] **A24** b7 · Q7.5 + Q7.4 code: trials registry + gate (`src/gate.py`) with thresholds marked "pending CEO approval". Check: running without a log entry fails. (done 2026-10-13, 1e5e4d5)
- [ ] **A25** b7 · Q7.6: `.github/workflows/backtest.yml` (data from Actions cache, tear-sheet artifact). Check: workflow lints; green on push.
- [ ] **A26** b7 · Q7.9 + Q7.11: `src/paper.py` simulated next-open fills + `src/risk.py`. No broker calls. Check: dry run over 20 past days; forced breach blocked.
- [x] **A27** b6 · F-01 + F-02: price engine in `06-finops/src/price/` (genai-prices, INR via cached RBI/FBIL rate, paise), unknown-model guard. Check: tests with a7 fixtures. (done 2026-10-13, 9f5fda1)
- [ ] **A28** b6 · F-03: Supabase migration `06-finops/src/db/` (`usage_event`, `usage_daily`, OTel gen_ai fields, RLS). Check: SQL applies on a local Postgres.
- [x] **A29** b6 · F-05: importers (OpenAI, Anthropic, LiteLLM, Langfuse, generic CSV/JSONL). Check: 5 fixtures import with no rows lost. (done 2026-10-13, 9f5fda1)
- [ ] **A30** b6 · F-06: X-ray generator (2-page HTML/PDF: ₹ by feature/model/customer, savings rules, DPDP score). Check: synthetic X-ray renders.
- [ ] **A31** b6 · F-13: framework catalogue `dpdp-2023.json` (every duty cites section/rule), ISO 42001 IDs, Art. 50 checklist. Check: validator.
- [x] **A32** b6 · F-15: PII scan Action (Presidio + Indian mobile/UPI/IFSC/Aadhaar/PAN recognizers, counts + hashes only). Check: synthetic fixtures. (done 2026-10-13, 9f5fda1)
- [ ] **A33** b6 · F-04 copy + F-11 ingest API + F-12 dashboard + F-17 alerts. Check: per PLAN.md.

### Sprint 3 · Second engine
- [x] **A34** b2 · b2.q10: `02-jobcard/supabase/schema.sql` with RLS. Check: applies on local Postgres. (done 2026-10-13, e6e5ffc; `bash 02-jobcard/supabase/test.sh` adds RLS tests)
- [x] **A34b** b2 · Deep Scan v2: `02-jobcard/lib/invoice.mjs` (GST maths for unregistered/composition/regular, words, UPI, bilingual HTML for expo-print, English PDF) + `lib/parse.mjs` (transcript → job card). Check: `cd 02-jobcard && npm test`. (done 2026-10-13, e6e5ffc)
- [ ] **A35** b2 · b2.q09: `02-jobcard/bot/functions/jobcard.js` (modelled on BotBhai webhook; voice → job card) tested with fakes. Check: tests green.
- [ ] **A36** b2 · b2.q19 + b2.q20: Expo app scaffold (Obytes template, te/hi strings), offline voice, SQLite outbox, invoice share. Check: `tsc` + Jest green.
- [ ] **A37** b2 · b2.q11 + b2.q15: reminders/quota cron and the "my customers" PWA. Check: tests.
- [x] **A38** b4 · E2 + E3: WXT scaffold in `04-extensions/src/`, save/restore core with Playwright test. Check: CI green. (done 2026-10-13, ca75d3c; unit + Chromium e2e green locally, runs in the `Kalpa quality` workflow)
- [x] **A39** b4 · E6 + E7: OneTab/Session Buddy importers and auto-snapshots. Check: 1,000-tab fixture passes. (done 2026-10-13, ca75d3c; unit + Chromium e2e green locally, runs in the `Kalpa quality` workflow)
- [ ] **A40** b4 · E9 + E10: privacy policy/landing page and store screenshots. Check: files in place.
- [ ] **A41** HQ · Q-HQ-05 + Q-HQ-06: invoice template (shared with A05) and legal drafts (client agreement, privacy notice, terms). Check: drafts in `00-hq/docs/legal/`.
- [x] **A44** growth · Deep Scan v2 step 5: `enrich.py` reads schema.org data, SEO-bot WhatsApp-button contrast + favicon, Lighthouse CI workflow (`.github/workflows/lighthouse.yml`). Check: enrich + SEO tests green; `lhci autorun` passes. (done 2026-10-13, c109d4e)
- [x] **A43** HQ · Quality workflow `.github/workflows/quality.yml`: gitleaks + actionlint + every world's tests (BotBhai, b2 with Postgres RLS, b4 with Chromium e2e, b6, b7). Check: actionlint clean; gitleaks no leaks. (done 2026-10-13, ca75d3c)
- [x] **A45** b1 · Social Team add-on (`01-botbhai/botbhai/social/`): month plan, captions with Telugu line, ad-rule checks (ASCI/DMR/CCPA/RERA), branded images + Reels, WhatsApp approval, Instagram/Facebook publisher (official API, dry run default), analyst. Check: `python3 01-botbhai/botbhai/social/test_social.py` green. (done 2026-10-15, f90b9cd)
- [x] **A46** HQ · Repo features from the "5 GitHub Repos" Short: Superpowers skills vendored (MIT), Taskmaster-style task engine on ROADMAP.md (`00-hq/agents/tasks.js`), short-answers repo skill (from I Have ADHD, MIT), Awesome Agents mapped to worlds. Check: `node 00-hq/agents/tasks.test.js` green and `tasks.js validate` clean. (done 2026-10-15, d6543b8)
- [x] **A47** HQ · Kalpa marketing team for every world (`00-hq/marketing/`): brand profiles for HQ + b1–b7 in Kalpa colours and fonts, world-specific ad rules (finops, trading off, deals #ad, kits, extensions), engine generalised for links instead of WhatsApp. Check: `python3 00-hq/marketing/test_marketing.py` + `test-all.sh` green. (done 2026-10-15, cdc99f4)
- [~] **A42** HQ · update the Kingdom control room tasks and the agent registry from these plans (new quests, WORLD_SHARE proposal flagged for CEO approval). Check: `node 00-hq/agents/run.test.js` green. (Kingdom part done 2026-10-13: quests match this roadmap, Forge of agent builds, rest-day streak, v13; still to do: agent registry + WORLD_SHARE proposal)

---

## CEO queue (Akhil, ≤ 1 hour a day)

Free items first. 💰 = costs money, waits for the go-public decision.

- [ ] **C01** HQ · Q-HQ-01: read PLAN.md §1, §5a, §7 and reply "approved" or changes (15 min)
- [ ] **C02** b1 · b1c: Meta developer app + WhatsApp test number; send Claude the Phone number ID + WABA ID (never the token) (30 min)
- [ ] **C03** b1 · b1d: say "deploy"; set Netlify visitor access to public; paste GROQ/SARVAM keys into Netlify yourself (20 min)
- [ ] **C04** b1 · b1e: show the demo to one salon owner you know (20 min)
- [ ] **C05** b1 · b1f: pick 15 salons from the cluster sheet (A08) (15 min)
- [ ] **C06** HQ · Q-HQ-02: create an empty "Kalpa Ledger" Google Sheet (10 min)
- [ ] **C07** HQ · Q-HQ-03: add NIC codes on Udyam (free, 20 min)
- [ ] **C08** HQ · Q-HQ-04: free business UPI QR on the spare account (20 min)
- [ ] **C09** b3 · K-04: create the Telegram channel (10 min)
- [ ] **C10** b5 · b5.W1.2: connect GitHub to Cloudflare Pages, free (15 min)
- [ ] **C11** b6 · F-03: create a free Supabase project for Ledger Peaks (10 min)
- [ ] **C12** b7 · Q7.4 / Q7.8: approve gate thresholds (incl. proposed criterion 6, Deflated Sharpe ≥ 0.95; see `07-trading/research/deep-scan-v2.md` Step 2); sign capital rules (₹0 is fine)
- [ ] **C17** b5 · Ask a Telugu-speaking friend to read the 7 Telugu calculator pages (`05-deals/site`, build artifact in Actions) and mark awkward lines (20 min)
- [ ] **C18** b1 · Look at the sample Social Team posts (Kingdom/log link) and decide the add-on price (suggestion ₹999–1,499/month); say if you want it offered to the first salons (10 min)
- [ ] **C19** HQ · When each product has a live page, paste its real link into `00-hq/marketing/brands/<world>.json` (replaces `[add link]`), and decide which worlds get an Instagram account (you create them; 10 min per world)
- [ ] **C13** HQ · Q-HQ-06: decide the go-public date (unlocks the 💰 items below)
- [ ] 💰 **C14** b1 · demo prepaid SIM (≈₹250) and Meta Business verification
- [ ] 💰 **C15** b3/b6 · Razorpay KYC (₹199)
- [ ] 💰 **C16** b4 · Chrome Web Store ($5); b2 · Play Console ($25); domain

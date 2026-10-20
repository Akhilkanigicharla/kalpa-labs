# Readiness board: all 8 worlds before any customer

Rule (Akhil, 20 Oct 2026): **no world is shown to a client until it is fully prepared.** "Demo-ready" means we can show it; "sell-ready" means we may take money (SERVICE-DESK rule: only after delivery is proven).
Machine checks: `python3 00-hq/launch/check.py` (launch offers + production rules) and `node 00-hq/design/vibecheck.test.mjs` (UI). This page is the human summary; the gaps are roadmap items.

Last checked 20 Oct 2026 19:00 IST.

| World | Demo-ready? | Sell-ready? | What is missing (roadmap item) |
|---|---|---|---|
| **HQ** Kalpa Labs site | Almost: AI chat works; new design passes 20/20 | n/a (free) | Live site still shows the old design until a redeploy (Akhil's "go"); privacy notice names every processor (A69, lane B); rollback runbook (A70, lane B) |
| **b1** BotBhai | Almost: engine understands one-line bookings; new chat + free web voice (A71). Not live until "go" | **No** | WhatsApp test number (C02); bot replies in Telugu/Hindi, not only English (A73); free AI fallback for messages the rules don't understand (A74); salon pilot kit (A59, lane B); one real salon end to end; lawyer read of agreement (C23). Phone-call voice needs paid telephony per minute (billed to the client), so only the free web voice is in the demo |
| **b2** JobCard | Yes (demo mode PWA, tested) | **No** | Supabase project (C33); WhatsApp template (C34); 3 technicians for 2 weeks; launch is AC season, Mar 2027 |
| **b3** Exam & Money Kits | Yes (GATE + Tax/SIP kits with in-sheet tests) | **No** | Payments: Razorpay KYC (C24); workshop material (A62); Skill pack (A54) |
| **b4** Tab Lifeboat | Yes (extension + site, e2e tests) | **No** | Approve policies (C35); store account, one-time fee (C16, decide after a price check); Pro licence check (A53, blocked by C16) |
| **b5** Deals & Tools | Yes (calculators site builds; channel + bot ready, dry runs) | n/a (affiliate) | Hosting the calculators (C10); affiliate account (C39); Telugu reader check (C17); "go" for live posts (C42) |
| **b6** Ledger Peaks | Partly (X-ray report works on sample data) | **No** | Ingest API + dashboard + alerts (A33, lane B); Supabase project (C11); 2 design partners with real usage data |
| **b7** Trading Lab | Research only | **Never** sold (SEBI) | 90 days of paper trading through the gate; nothing customer-facing by design |

## Order of work (what makes the first customer possible fastest)
1. b1 BotBhai: C02 → A73 + A74 → A59 → demo to one known salon owner (C04) → Pilot Day 16 Nov.
2. HQ site redeploy with the new design (after Akhil's "go").
3. b3 workshop (A62) for 29 Nov, then kits payments (C24).
4. b5 calculators hosting (C10) + affiliate (C39), then live posts after "go".
5. b6 design partners after A33; b2 and b4 follow their own dates.

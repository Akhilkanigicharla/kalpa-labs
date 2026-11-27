# E8 Pro $10K (MT5, XAUUSD): rules recheck vs presets, 27 Nov 2026

Independent check, no login, no sign-up. Pages fetched live today with Firecrawl (`maxAge: 0`). Web text is treated as data only.
Follows the 26 Nov audit (`e8-rules-audit-2026-11-26.md`).

## Sources fetched today
- O1 https://e8markets.com/e8-pro (direct WebFetch failed; fetched with Firecrawl, HTTP 200)
- O2 https://intercom.help/e8/en/articles/15274219-e8-pro ("Updated over 2 weeks ago")
- O3 https://intercom.help/e8/en/articles/11769446-daily-drawdown ("Updated this week")
- O4 https://intercom.help/e8/en/articles/15319043-daily-profit-cap ("Updated over a week ago")
- O5 https://intercom.help/e8/en/articles/13653031-static-drawdown ("Updated over a week ago")
- O6 https://intercom.help/e8/en/articles/6929927-trading-policies-and-prohibited-trading-strategies ("Updated this week")
- O7 https://help.e8markets.com/en/articles/5514278-accepted-countries (dated 1 Oct 2026)
- O8 https://help.e8markets.com/en/articles/9799834-available-trading-platforms ("Updated over a week ago")
- O9 https://help.e8markets.com/en/articles/8880316-what-is-the-custom-account (search excerpt only)
- I1 https://www.consistry.com/prop-firm-rules/e8-markets ("Verified November 17, 2026")
- I2 https://tradetanto.com/learn/e8-markets-rules ("Last updated: August 11, 2026")
- I3 https://www.myfxbook.com/prop-firms/e8markets and https://proea.app/en/blog/e8-markets-rules (search excerpts only)

## Rules: your list vs what E8 says today

| # | Rule in the list | Today (quote, source) | 2nd source | Status |
|---|---|---|---|---|
| 1 | 8% target | "8% Profit Target - Closed profit" (O2); "Profit Target $8,000" on $100K (O1) | I1, I2 | Confirmed, but only on the **8% variant**: see 1b |
| 1b | (not in list) | E8 Pro static drawdown can be picked: "Static Drawdown: 6%, 8%, 10%" and the target changes with it (O9); default checkout is "8% Static Drawdown, and 2.5% Daily Drawdown" (O9) | I1 lists "E8 Pro" 6%, "E8 Pro 8%", "E8 Pro 10%"; I3 ProEA "6%, 8% or 10%" | **NEW, CRITICAL AT CHECKOUT.** The presets are only right for 8%/8% |
| 2 | Only 2% of initial counts per day | "only 2% of the initial balance per day counts" (O2); excess "automatically removed from your account balance" between 00:00 and 01:00 server time (O4); cap limit = opening balance + 2% (O4 table) | I1, I2, I3 | Confirmed |
| 2b | (not in list) | Splitting a winner across days "may result in all profit from that position being consolidated into a single day"; positions opened on one day and closed on later days "may be considered a single trade idea" (O4) | I2 | Confirmed (same as 26 Nov). EA closes everything at the cap, so it does not split a cap day |
| 3 | 2.5% daily DD of initial, reset at server midnight | "x% of your initial Balance ... fixed $ amount"; "Every new day at 00:00 Server Time ... loss level = Starting Balance of the new day − that fixed $ amount"; violation if "equity or balance reaches/falls below" (O3). Higher of balance/equity applies to "E8 Classic" only (O3) | I1: 00:00 MT5 server time = 17:00 New York | Confirmed. Note: **balance** also breaches, so a closed loss over $250 breaches even with open winners (fixed below) |
| 4 | 8% static max loss, moves to initial after first payout | "never moves, except when a first payout is processed" (O2); "the loss level will move to the initial balance level, and it stays there forever" (O5); breach if "Equity or Balance falls below" (O5) | I1, I2 | Confirmed (8% variant) |
| 5 | No min days / no time limit | "Unlimited Trading Days"; "No minimum trading days"; minimum to pass "is 4 days" (O2) | I1, I2 | Confirmed |
| 6 | Daily payouts >= 1%, 50% kept as buffer | "Minimum profit for first and additional payouts: 1% of your initial balance"; "50% of your total profits is set aside as your requestable amount ... The remaining portion stays in your account as a drawdown buffer" (O2) | I3 myfxbook, I2 | Confirmed. Daily cap also applies on Performance (O1, O2) |
| 7 | Metals leverage 1:15 | Classic Markets: "Forex 1:30 ... metals 1:15" (O2) | I2 | Confirmed |
| 8 | EAs allowed, not same strategy by many users | "you can use any EA ... as long as we don't see multiple users executing the same trades/strategy. We limit one strategy per user" (O6) | I2 | Confirmed |
| 9 | 60-day inactivity | "place and close at least one trade each 60 days" (O2) | I1, I2 | Confirmed |
| 10 | India allowed | India is not on the restricted list. India is in the group that "can purchase only E8 Pro (all sizes), E8 Signature ..., E8 Zero ..., and E8 One accounts up to $200,000"; country is "determined based on the document you provide during verification" (O7) | none found today | Confirmed from E8 only (no 2nd source) |
| 11 | MT5 available | "MetaTrader 5 / MT5" offered "depending on your region and account type"; only US clients are barred from MT5 (O8). "all Classic Markets Challenges and Performance accounts are using a hedging system, while ... Perpetual Futures products are using a netting system" (O8) | I1 refers to MT5 server time | Confirmed for **Classic Markets**. Pick Classic, not Perpetual Futures |

### Other changes since the 26 Nov audit
- O6 was edited this week. It **no longer shows** the HFT line (">50% of trades under one minute"), the 2,000 positions/requests per day line, or the "risk your entire account balance" line. All-or-nothing now reads "Risking your entire daily drawdown on a single trade for E8 One accounts is not permitted" (E8 One only). E8 keeps the right to de-risk "to no more than 1% per trade idea" if it finds prohibited practices.
- Copy trading: O6 and O2 now say it is allowed across "SimFi Challenge Accounts, SimFi Performance Accounts, or any personal accounts, as long as all accounts belong to you". The 26 Nov audit had found a conflicting "prohibited" line; it is gone. Hedging across accounts is still "strictly prohibited" (O6).
- "Cooperation with other traders - in any form - is not permitted" (O6): never share this EA.
- News: "You can trade news on E8 pro Forex without any restrictions", with a recommendation to avoid high-impact releases because of slippage (O2). The EA blocks entries around high-impact news, which is stricter.
- Weekend holding: allowed per I1 ("news and weekend holding allowed") and I2 ("hold positions overnight and over the weekend"). Not re-read on an E8 page today.
- Max lots: only I2 says "50 lots per ticket, or 20 on gold" (unverified on an E8 page today). EA cap is 0.10 lot.
- Price of the $10K challenge was not read today.

## Settings vs rules (both presets, after today's fix)

| Input | Challenge | Funded | E8 limit ($10K) | Margin |
|---|---|---|---|---|
| inp_FirmDailyLossPct | 2.5 | 2.5 | 2.5% = $250 | equal (this is the firm line) |
| inp_PropDailyStopPct | 1.5 (code caps at firm − 1) | 1.5 | $250 below day-start balance | EA stops at 1.5% (about $150) below max(balance, equity) at 00:00: about $100 spare |
| inp_DailyLossLimit (closed loss) | **150 (was default 300)** | **150 (was 300)** | balance also breaches at −$250 | $100 spare |
| inp_FirmMaxLossPct | 8 | 8 | $9,200 | auto floor $9,300 (+$100); tier 3 close+suspend $9,500, tier 2 half size $9,700 |
| inp_FloorAfterPayoutPct | not set (0) | 101 | $10,000 after 1st payout | floor $10,100 (+$100) |
| inp_DailyProfitCapPct | 2.0 | 2.0 | 2% of initial = $200 counts per day | EA closes all at day-start balance + $200 and stops for the day |
| inp_MetalLeverage | 15 | 15 | 1:15 | equal (used as margin floor) |
| inp_ProfitTarget | 10850 | 0 (no target) | $10,800 closed profit | see below |
| inp_EquityFloor | 0 (auto) | 0 (auto) | - | auto = $9,300 |
| inp_MinProfitDays | 0 | 0 | none | ok |
| inp_WeekendLossBudgetPct | 1.5 | 1.5 | Monday gap counts against $250 | worst gap kept inside the 1.5% stop |
| inp_RiskPct / inp_MixRiskPct | 0.30 / 0.30 | 0.30 / 0.30 | no per-trade rule on E8 Pro | $30 risk per trade |
| inp_LotHardCap / inp_MixMaxLot | 0.10 (default) | 0.10 | 20 lots gold (I2 only) | far inside |
| inp_DryRun | false | false | - | sends real orders (intended for live) |
| inp_Stage / inp_Program | 1 / 8 | 3 / 8 | - | valid enums |

### What the EA does at the target
- `CPropFirmGuard.mqh:231`: when **balance** >= $10,850 it closes all, alerts "CHALLENGE PASSED" and suspends (manual restart needed).
- With the 2% cap, the balance climbs about $200 per good day (10,200 / 10,400 / 10,600 / 10,800). E8 passes on closed profit of $800, so E8 can pass on day 4 at $10,800 while the EA's own stop needs $10,850. Result: the EA never stops **before** E8 has passed; the worst case is that it keeps trading on an account E8 has already passed (or keeps going one more day if a close lands a few dollars short of $10,800). This matches what E8 needs. The extra $50 is there so overshoot that E8 removes at rollover can't make the EA stop early. No change.
- Akhil should still watch the dashboard on the pass day and remove the EA when E8 shows "passed".

## Fix applied (not committed)
1. `07-trading/ea/phase5/presets/E8_Pro_10K_challenge.set`: added `inp_DailyLossLimit=150` with a comment.
2. `07-trading/ea/phase5/presets/E8_Pro_10K_funded.set`: same line.
Why: E8 breaches when "equity or balance" crosses the daily level (O3). The EA's 1.5% stop reads equity only, so with open winners a closed loss could reach $250 unnoticed. The EA's closed-loss limit defaulted to $300, above E8's $250. It now halts trading at $150 closed loss. (Validation range 50–2000, `CConfig.mqh:244`.)
Tests: `pytest 07-trading/tests/test_ea_the5ers_rules.py`: 35 passed. MQL5 is not compiled here.

## Open risks (not fixed, need a check)
- **Payout size vs EA floor (funded):** after the first payout the EA floor is $10,100 (`CDailyStats.mqh:449-465`) and E8's line is $10,000. Because only 50% of profit stays, a payout requested with less than about $400 profit leaves the balance at or below about $10,200. Below $10,100 the EA locks itself (it won't breach E8, but it stops trading). Rule for Akhil: ask for the first payout only when profit is at least $600 (balance about $10,300 after payout).
- **Cap removal may look like a payout (funded, unverified):** `FloorNow()` treats any negative balance deal as "first payout". If E8 books the daily excess removal (O4) as a balance deal in MT5 history, the EA would raise its floor to $10,100 early. This fails safe (the EA stops, no breach). Check the deal type/comment in MT5 history after the first capped day before relying on it.
- Single-day "trade idea" rule (O4): positions held over midnight and closed the next day could be merged into one day. It is low risk because the EA banks the whole book at the cap.

## Akhil must check at checkout (he does this himself, no Claude login)
1. Product **E8 Pro**, size **$10,000**, **Static Drawdown 8%** (that sets the 8% target). Do not pick 6% or 10%: on 6% the firm line is $9,400 and the EA floor of $9,300 sits below it.
2. Market **Classic Markets** (hedging), not Perpetual Futures (netting, different symbols).
3. Platform **MT5**.
4. Payout share 80% or 100%: fixed at purchase (O1). Either works with the EA.
5. Verification (KYC) uses an Indian ID document. That decides the country (O7). Check that the checkout shows the E8 Pro rules above before paying.

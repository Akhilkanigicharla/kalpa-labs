# E8 Pro $10K (1-step, MT5, XAUUSD) - rules audit vs EA_XAUUSD + presets

Date: 26 Nov 2026 (IST). Independent auditor run, no login anywhere. Sources fetched today.

Sources
- S1 E8 help centre, E8 Pro: https://intercom.help/e8/en/articles/15274219-e8-pro
- S1b Daily profit cap: https://intercom.help/e8/en/articles/15319043-daily-profit-cap
- S1c Daily drawdown: https://intercom.help/e8/en/articles/11769446-daily-drawdown
- S1d Static drawdown: https://intercom.help/e8/en/articles/13653031-static-drawdown
- S1e Payout: https://intercom.help/e8/en/articles/13653464-payout-share-request-from-e8-static
- S1f Prohibited strategies: https://intercom.help/e8/en/articles/6929927-trading-policies-and-prohibited-trading-strategies (served via help.e8markets.com)
- S1g Leverage: https://intercom.help/e8/en/articles/5514982-how-much-leverage-do-you-offer
- S1h Product overview: https://intercom.help/e8/en/articles/13106558-all-product-overviews-e8-one-vs-e8-zero-vs-e8-pro-vs-e8-signature
- S1i News (E8 Trader account, older): https://help.e8markets.com/en/articles/9185497-can-i-trade-news-on-e8-trader-account
- S2 e8markets.com/e8-pro (fetched via Firecrawl cache 25 Nov 2026; direct fetch is bot-blocked 403)
- S3 tradetanto.com/learn/e8-markets-rules (updated 11 Aug 2026)
- S3b tradingfinder.com/props/e8-markets/rules (modified 15 Apr 2026)
- S3c propvator.com/blog/e8-markets-weekend-holding-rule (30 Jun 2026)
- propfirmmatch.com E8 Pro 10K page: fetch failed (client error), not used.

## Rules vs EA

| # | Rule | Official wording + URL | 2nd / 3rd source | EA handles? (file:line) | Gap | Fix / applied? |
|---|---|---|---|---|---|---|
| 1 | Profit target 8% | S1: "8% Profit Target - Closed profit" | S2 "Profit Target $8,000" (on $100K); S3 "8% profit target" | Preset `inp_ProfitTarget=10850` (8.5%); checked on BALANCE, CPropFirmGuard.mqh:231 | None: $50 buffer over $10,800 is deliberate (excess above cap removed at rollover) | None needed |
| 2 | Daily profit cap 2% of initial balance; excess removed 00:00-01:00 server | S1: "only 2% of the initial balance per day counts"; S1b: excess "automatically removed from your account balance"; cap limit = day-start balance + 2% (example $101,000 -> $103,000); splitting a winner across days "may result in all profit from that position being consolidated into a single day" | S2 "Daily profit cap $2,000"; S3 same; S1h "2% Daily profit cap" | CGuardCoordinator.mqh:505-521 closes all + stops for the day at the cap | MEDIUM: line was measured from day base = max(balance, equity) at 00:00; with floating profit carried over midnight the EA line sat above E8's balance-based line, so realised profit could be stripped | APPLIED: cap now measured from `DailyStats.GetStartBalance()` (falls back to day base). Residual LOW: overnight/H4 holds that bank big profit later could be "consolidated" by E8; normal strategy, not split on purpose, but watch |
| 3 | Daily drawdown 2.5% of initial balance (fixed $250 on $10K), hard breach, equity or balance | S1: "must not lose more than 2.5% of your initial balance in a single day"; S1c: fixed $ amount from initial balance, level re-based each day "at 00:00 Server Time", Classic uses higher of balance/equity; breach if "equity or balance" touches | S2 "Daily drawdown $2,500" (on $100K); S3 "measured against your starting balance for that day" | Day base = max(balance, equity) at 00:00 server (CDailyStats.mqh:156); stop 1.5% (CConfig.mqh `DailyStopPct=min(1.5, 2.5-1)`); FastSafetyCheck CGuardCoordinator.mqh:494-504 every tick | None for intraday. EA line is above the strictest reading while day base < $16,667. Basis for Pro (balance vs max(bal,eq)) is UNVERIFIED on E8 pages; EA uses the stricter one | None needed |
| 3b | Weekend gap counts against Monday's daily limit | (follows from 3 + weekend holding allowed) | - | WeekendRiskCut CGuardCoordinator.mqh:569-640 limits worst gap loss to `inp_WeekendLossBudgetPct` (default 3.0%) | HIGH: 3% worst-case gap budget > 2.5% firm daily; a stop-jumping Monday gap could breach in one tick | APPLIED: `inp_WeekendLossBudgetPct=1.5` in both E8 presets |
| 4 | Static max loss 8% of initial ($9,200), equity or balance | S1d: "does not move up, or trails"; breach if "Equity or Balance falls below" | S2 "Static Drawdown $8,000"; S3 static, 8% below initial | Auto floor = size x (1 - 7%) = $9,300 (CConfig.mqh EquityFloor); FastSafetyCheck :481; EquityGuard tier3 close+suspend at floor+$200 = $9,500, tier2 half size at $9,700 | None in challenge | None |
| 4b | After first payout the loss level moves to the initial balance for good | S1d: "the loss level will move to the initial balance level, and it stays there forever" | S2 "locks at your initial balance"; S3 same | Funded preset used auto floor $9,300 and validation capped `inp_EquityFloor` at account size | HIGH (funded only): after payout E8 line = $10,000 but EA floor $9,300 -> EA could breach without stopping; and the input could not be set above $10,000 | APPLIED: validation upper bound now 2x account size (CConfig.mqh); funded preset comment: set `inp_EquityFloor=10100` after first payout. Note EquityGuard tier3 = floor+$200 -> EA halts below $10,300 equity; buffer then = retained 50% of profit. Akhil must change the input after the payout (CEO action) |
| 5 | Min trading days / time limit | S1: unlimited; "minimum is 4 days" because of the cap | S2 "No consistency rule or minimum profitable days"; S3 "no deadline and no minimum number of trading days" | Preset `inp_MinProfitDays=0` | None | None |
| 6 | Inactivity: place and close 1 trade every 60 days | S1: "at least one trade every 60 days" | S3 60 days; S3b says 90 days (older, superseded) | No code. EA can halt itself (tier3 lock, target lock, manual) | LOW: a halted funded account could be closed after 60 days | CEO calendar reminder; not coded |
| 7 | News trading | S1: "permitted without restrictions" in challenge and Performance; S1i (older "E8 Trader" page): 5 min before/after blackout | S2 FAQ silent; S3 "unrestricted"; S3b permitted | CMSNREngine.mqh:314 blocks entries +/-120 min around high-impact USD news; :430 NewsDerisk cuts book; official 2026-27 US schedule backup | None (EA is stricter than E8, also covers the 5-min window if it applied) | None |
| 8 | Weekend / overnight holding | S1h: weekend "Yes" | S3, S3b, S3c: allowed on Pro | Allowed, sized by Friday cut (see 3b) | See 3b | Applied (3b) |
| 9 | EAs; same EA as other users banned | S1f: "any EA ... as long as we don't see multiple users executing the same trades/strategy"; same EA "may lead to the termination" | S3 "one strategy per user"; S3b "cannot run identical strategies across multiple accounts" | Own EA, private code | MEDIUM (policy): never sell/share this EA to anyone trading E8; "one strategy per user" is UNVERIFIED on E8's own pages (only S3/S3b) | Do not run it on a second E8 evaluation at the same time (see 10) |
| 10 | Copy trading | S1: allowed across accounts you own; S1f: copying between two E8 evaluation accounts "is prohibited" | S3b same | N/A | LOW: E8 pages conflict; running the same EA on 2 E8 evaluations = identical trades | One E8 account per EA until E8 confirms in writing |
| 11 | HFT: <=50% of trades held under 1 minute | S1f: "cannot hold more than 50% of your trades for under one minute" | S3, S3b same | Swing entries, min SL 30 pips / $1.50 mix, max 3 main trades/day; only emergency/cap closes can be fast | None expected | Check hold times in the first live week log |
| 12 | Hedging across accounts; all-or-nothing; martingale | S1f: cross-account hedging "strictly prohibited"; "Risking your entire account balance on a single trade is not permitted" | S3 same | One account; 0.30% risk/trade; streak sizing 1.5x after a win, 0.75x after a loss (anti-martingale); `inp_AllowOpposite=true` = long+short in the same account | None found. Same-account hedge rules sit in a separate E8 article that was blocked (UNVERIFIED) | Set `inp_AllowOpposite=false` if E8 confirms it counts as hedging |
| 13 | Max lots / limits | S1f: 2,000 positions and 2,000 server requests per day; "maximum allocation limit for each product" | S3 "50 lots per ticket, or 20 on gold"; S3b 20 lots XAUUSD | `inp_LotHardCap=0.10`, `inp_MixMaxLot=0.10` | None | None |
| 14 | Leverage metals 1:15 | S1 and S1g: Metals 1:15 (E8 Pro) | S3 1:15 metals | Preset `inp_MetalLeverage=15`, margin floor CPositionSizer.mqh:236 | None | None |
| 15 | Payouts: daily, 1% min profit, 50% kept as buffer, 80%/100% share | S1e: "50% is your payout, and 50% is kept in the account as a buffer"; "minimum profit requirement of 1%" | S2 same; S3 same + $100 minimum | Manual (Akhil) | None in code | None |
| 16 | Consistency rule | S1: "NO consistency rules" | S2, S3 same | n/a | None | None |

## Preset integrity
- Every name in both E8 presets matches a declared input (CConfig.mqh, CMixEngine.mqh:32). No silent-ignore lines.
- Enums: `inp_Stage=1` = STAGE_STEP1, `3` = STAGE_FUNDED; `inp_Program=8` = PROGRAM_CLASSIC (8%). Valid.
- `inp_DryRun` is not in the presets and defaults to `true` (CConfig.mqh:103): the EA will only log orders until it is set to `false` on the live chart. Intentional until "go", but it must be a launch checklist item.
- `inp_DailyLossLimit` default $300 (3%) is above E8's $250, but the 1.5% equity stop always fires first; harmless.

## Edits made (not committed)
1. `EA_XAUUSD/Guards/CGuardCoordinator.mqh` ~505-512: daily profit cap measured from day-start balance.
2. `EA_XAUUSD/Core/CConfig.mqh` EquityFloor validation: upper bound 1x -> 2x account size (for after the E8 Pro first payout).
3. `presets/E8_Pro_10K_challenge.set`: added `inp_WeekendLossBudgetPct=1.5`.
4. `presets/E8_Pro_10K_funded.set`: added `inp_WeekendLossBudgetPct=1.5` + post-payout floor note.

Tests: `pytest 07-trading/tests` = 280 pass, 1 fail (`test_lab.py::test_data_folder_is_git_ignored`, a git-ignore check, unrelated to these files). MQL5 not compiled here (no compiler): compile in MetaEditor before use.

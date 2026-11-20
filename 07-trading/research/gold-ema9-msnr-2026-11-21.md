# A308 · Akhil's gold plan: sell to $3,100, then buy, with 9 EMA + MSNR (21 Nov 2026)

Akhil (21 Nov 2026, 02:22 IST): "Gold sell trade bot untill 3100 and from there buy trade strategy
using 9ema and malayasia stargety … find a funded account which allow algo trading bot and which
was real to withdraw".

Code: `07-trading/research/gold_ema9_msnr.py` (tests: `tests/test_gold_ema9_msnr.py`, 6 pass).
Raw numbers: `reports/gold-ema9-msnr-2026-11-20.json` (UTC date of the run).
Paper (forward test from 21 Nov, no orders sent): `paper/gold-ema9-msnr/`, daily in `paper-trade.yml`.

## The rules (fixed before any result was seen)
- **Side:** short while gold closes above **$3,100**, long at or below (Akhil's level).
- **Trigger:** close below the 9 EMA with the EMA falling, and the bar wicks into a **fresh** MSNR
  resistance (A level from closes, or a flipped V level) and closes back below it. Longs mirror this.
- **Trade:** enter next bar's open; stop past the wick + 0.25 ATR; target 2R; max 48 hours.
- **Costs:** $0.40 per round trip (Micro Gold commission + 1 tick).
- Tested on 2.3 years of free hourly GC=F (Jul 2024 → 20 Nov 2026) and 21 years of daily data.

## Results

| Version (hourly) | Trades | Win % | Avg R | Random entries | Chance it's luck |
|---|---|---|---|---|---|
| **Akhil's rule ($3,100 level)** | 1,057 | 36% | **−0.003R** | −0.067R | 7% |
| Akhil's rule, shorts only | 711 | 36% | +0.015R | | |
| Akhil's rule, since the 29 Jan 2026 peak ($5,318) | 398 shorts | 35% | +0.002R | | |
| 9 EMA + MSNR, both sides, no level | 1,591 | 34% | −0.04R | −0.062R | 25% |
| Side from the daily 9 EMA instead of $3,100 | 1,047 | 37% | **+0.025R** | −0.070R | **1.6%** |
| Daily bars, 2005–2026 (both / daily EMA) | 687 / 682 | 35% | 0.00R / +0.008R | | 58% / 25% |

What it means in plain words:
- The MSNR + 9 EMA trigger does better than random entries (random loses about 0.07R a trade after costs),
  so the entries are not useless.
- But **after costs it only breaks even**. Even in the 34% fall since January, shorting at MSNR levels
  made +0.002R a trade, which is zero.
- The $3,100 level is a price forecast, not a tested edge. The data cannot tell us whether gold reaches it.
- Letting the daily 9 EMA pick the side is the only version clearly better than luck, and it is still tiny:
  +0.025R × 1,047 trades = +26R in 2.3 years, before tax.

## Topstep 50K Combine, simulated on every weekly start (116 starts)
Rules used: +$3,000 target, $2,000 max loss trailing the end-of-day high, best day ≤ 50% of profit,
max 50 Micro Gold. Fees $49/month + $29/month TopstepX API, $149 activation, then a first payout
needs 5 winning days of ≥ $150 (50% of profit, 90% split).

| Version, $400 risk a trade | Pass | Reach 1st payout | Average net $ per attempt | Random entries |
|---|---|---|---|---|
| Akhil's rule | 23% | 9% | **−$49** | −$77 (5% payout) |
| Both sides | 23% | 6% | −$38 | −$55 |
| Daily-EMA side | 31% | 4% | −$99 | −$55 |

Every version loses money on average once all fees are counted. Passing about 1 time in 4 comes from
the variance of a break-even strategy, not from skill: random entries pass 20%+ too.

## Funded firms that allow bots and really pay (checked 21 Nov 2026)

| Firm | Bots | Real withdrawals | India | Blocker |
|---|---|---|---|---|
| FTMO | Allowed | Yes | Accepts | **On RBI Alert List** (rbi.org.in, list updated 22 Oct 2024) |
| FundedNext | Allowed | Yes | Accepts | **On RBI Alert List** (added 22 Oct 2024) |
| **Topstep** (CME futures, Micro Gold MGC) | Allowed via TopstepX API ($29/mo) | Yes, 90% split | Not on its ineligible or XFA-only lists (help.topstep.com, read 21 Nov) | **Orders must come from your own device: no VPS, VPN or remote server.** A cloud bot (our rule: nothing on Akhil's PC) breaks Topstep's rule. Not on RBI Alert List (forex list; CME gold futures are not forex), but foreign futures by an Indian resident is a FEMA/LRS grey area: get a CA's view. |
| **Darwinex Zero** (UK, FCA-regulated group) | Allowed, MT5 | Yes: 15% performance fee on real allocated capital | Appears to accept India (third-party lists; confirm at sign-up) | Slow: you build a track record, then capital is allocated. ~$38/month. CFD/forex route, not on RBI Alert List, but also not RBI-authorised (no foreign firm is). Same FEMA grey area. |
| Hindustan Funded / Greenwick (Indian, MCX) | Banned / needs written approval | Yes | Yes | From A305 |

Nobody can make "a bot on a funded account, run from the cloud, legal in India, that pays" clean today.
The closest real options are:
1. **Topstep + Micro Gold**, bot on Akhil's own laptop through the TopstepX API. Legal grey area: ask a CA first.
   ₹10,000 ≈ $108 at ₹92.66 = about 1.4 months of Combine + API, and not enough for the $149 activation.
2. **Darwinex Zero**: slow but regulated, and the cloud MT5 bot is allowed.
3. **Own money on MCX Gold Petal** through a SEBI broker API (fully legal, bots allowed, real risk).

## Decision rule
No fee is paid until the forward paper test (`paper/gold-ema9-msnr/state.json`) shows the rule earning
over 30+ trades. Until then the backtest says it breaks even, and the fees make it lose.

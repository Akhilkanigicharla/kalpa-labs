# Kalpa Nifty Bot · Strategy v1 (13 Nov 2026)

Paper trading only until all go-live conditions are met (section 6). Not investment advice.

## 1. The answer in 5 lines
1. **Core:** a trend rule on the Nifty 50. Hold NIFTYBEES when Nifty is above its level of a few months ago; otherwise park the money in a liquid ETF (about 4.7% a year).
2. **Tested like a fund tests:** walk-forward (settings picked on 3 past years, traded on the next 1 year), costs, stress at double costs + a one-day delay, overfitting checks (PBO, deflated Sharpe). All 19 tries are logged, so nothing is cherry-picked.
3. **Result on 15 years of real data:** ₹1 → ₹3.83 (9.4% a year), worst fall −16%. Just holding Nifty: ₹1 → ₹4.39 (10.4%), worst fall −38%. **A smoother ride, not more money.**
4. **News, the Fed, US yields, the rupee, oil, India VIX and elections were all tested as trading rules. None improved the bot**, so they run as a daily **World Check** that alerts you but does not trade.
5. **The biggest edge found is mixing assets:** Nifty + gold + US Nasdaq-100 (in rupees). This is what big trend funds do. It is the next build, done the way Indian rules and taxes allow.

## 2. The four layers
| Layer | What it does | Status |
|---|---|---|
| 1. Trend core | 100% NIFTYBEES when the trend is up, 0% when down. Lookback 63–252 days, re-picked by the same walk-forward rule every day | Passes 5 of 6 gate checks; fails only the stress check (Sharpe 0.62 vs holding ~0.68 at 2× costs + 1-day delay) |
| 2. Cash yield | Idle money in a liquid ETF (LIQUIDBEES 4.69%/yr since 2003 after 0.69% fee; Mirae 0.15%, Kotak 0.19% fee copies are cheaper) | In the backtest and the paper bot |
| 3. Safety (Akhil chose "Up to 100%") | 20% protective stop on each buy; new buys pause at a 20% fall from peak (alert); KILL file from the phone; under 10 orders/sec; daily broker login (SEBI) | Built, 103 tests green |
| 4. World Check (alerts only) | Pre-market and post-close snapshot: S&P 500, Nasdaq, Nikkei, Hang Seng, US 10-year yield, dollar index, USD/INR, Brent oil, US VIX, India VIX; 4 risk flags; Fed/RBI/Budget/election calendar; latest Fed + RBI press headlines | Built, runs daily |

## 3. Results (Feb 2011 – Jul 2026, out-of-sample, after costs, before tax)
| Strategy | ₹1 became | Per year | Worst fall | Sharpe |
|---|---|---|---|---|
| Trend bot, up to 100% (chosen) | ₹3.83 | 9.4% | −15.7% | 0.86 |
| Trend bot, max 20% (old draft rules) | ₹2.28 | 5.7% | −2.6% | n/a (mostly cash) |
| Just hold Nifty | ₹4.39 | 10.4% | −38.4% | 0.68 |
| Liquid ETF only | ₹1.99 | 4.7% | 0% | – |

Notes: Nifty data is the price index (dividends of roughly 1–1.5%/yr not included, which helps "hold" a little). The bot sells more often, so after tax (20% short-term on equity ETFs) the gap to "hold" is wider.

## 4. Tested and NOT used as trading rules
Fixed before testing (no tuning afterwards), each halves the position when on:

| Rule | On how often | Result |
|---|---|---|
| Global trend: S&P 500 below its 200-day average | 19% of days | ₹3.74, worst −16.0%: no better |
| Fear: India VIX in its top 20% of the past year | 17% | ₹3.50, −15.3% |
| Dollar squeeze: US 10Y +0.5 pts and USD/INR +2% in 3 months | 5% | ₹3.74, −18.7% |
| Oil shock: Brent +30% in 3 months | 7% | ₹3.47, −19.7% |
| 2 or more of the above | 12% | ₹3.56, −18.7% |

Why: the trend rule already steps out of falling markets; these signals mostly say the same thing, later.
**Event days cut both ways:** election results days were +17.7% (2009), +1.1% (2014), −0.7% (2019) and −5.9% (2024). Budget days were mostly small (largest +4.7% in 2021). Selling before events would have missed 2009 to save 2024. So events are alerts, not trades.
**News headlines:** there is no free archive of past Indian market news to test a news-trading rule fairly, so news is shown to you, not traded. It can become a rule only after it passes the same gate on paper.

## 5. The diversification finding (next build)
Daily returns barely move together: Nifty–gold 0.03, Nifty–Nasdaq-100 0.23.

| 12-month trend rule, fixed in advance | 2011–2018 | 2019–2026 | Whole period, worst fall |
|---|---|---|---|
| Nifty only | 6.0%/yr | 4.0%/yr | −23.5% |
| Nifty + gold + Nasdaq-100 | 10.3%/yr | 15.9%/yr | −14.3% |
| Hold an equal mix of all three | 12.5%/yr | 20.6%/yr | −21.8% |
| Hold Nifty | 9.3%/yr | 11.5%/yr | −38.4% |

It works in both halves, so it is not one lucky period. But be careful: part of the gain is the Nasdaq's unusual run and the rupee falling from 45.8 to 94.2 per dollar (4.5%/yr).
**Real-world limits checked today:**
- The Nasdaq ETF (MON100) trades at a premium of up to 19% (April 2026) because RBI's overseas limit stops new units, so the bot must not trade it. Nasdaq-100 FoFs (Navi 0.23%, Kotak 0.31% total cost) are open, but they are mutual funds: buy monthly, not by bot.
- Gold ETF (GOLDBEES) is tradable by the bot.
- Tax: equity ETF 20% short-term / 12.5% after 12 months; gold ETF slab rate short-term / 12.5% after 12 months.

**Next build (v2):** a bot sleeve trading NIFTYBEES + GOLDBEES with the trend rule (fully gate-tested first), plus a simple monthly SIP plan for the Nasdaq FoF. Each part must pass the gate before paper money moves.

## 6. Daily routine and the road to real money
- **16:15 IST every weekday:** the bot decides from today's close; a simulated fill at the next open; `paper/track-A/summary-A.txt` and `worldcheck.txt` are updated in the repo (readable in the git app).
- **To stop new buys from the phone:** add an empty file `07-trading/paper/track-A/flags/KILL`.
- **Real money only when ALL are true:** 90 paper days (day 1 = 13 Nov 2026); the gate passes all 6 checks (today 5/6); broker API + whitelisted static IP + daily 2FA login (SEBI retail algo rules); Akhil types "go" and sets the keys himself. Start at ₹5,000–10,000 that you can fully afford to lose.
- **Stop rule (PLAN.md K4):** if after 12 months live the bot earns less than a Nifty index fund after tax, stop and move the money to the index fund.

Sources: research notes `07-trading/research/nifty-etf-bot-2026-11-13.md`, trial log `07-trading/research/trials.csv` (T0001–T0019); LIQUIDBEES returns (anandrathi.com, 1 Jun 2025); ETF fees (groww.in); MON100 premium (businesstoday.in Apr 2026, business-standard.com Dec 2024); Nasdaq FoF costs (winvesta.in); ETF tax (jainam.in, zerodhafundhouse.com); RBI MPC dates (rbi.org.in + 5paisa.com); FOMC dates (federalreserve.gov + fedratecalc.com); election day 2024 (angelone.in); volatility-managed portfolios (Moreira & Muir 2017; Cederburg et al. at lehigh.edu).

## 7. 5-minute intraday bot (Akhil, 13 Nov 2026)
Built: `src/intraday.py` (signal on a bar's close, fill at the next bar's open; stop counted first if a bar touches both;
forced exit 15:15; max 2 trades a day; full Indian intraday costs + slippage; long and short). 7 tests.

Test on all free 5-minute data (NIFTYBEES, 60 sessions, 18 Aug – 13 Nov 2026, ₹5,000):

| Strategy | Trades | Before costs | Costs | Net |
|---|---|---|---|---|
| Opening-range breakout (1× / 2× range target) | 102 / 92 | +₹76 / +₹118 | ₹530 / ₹478 | −₹453 / −₹359 |
| VWAP trend (0.3/0.6% · 0.4/0.8%) | 47 / 45 | −₹32 / +₹8 | ₹244 / ₹233 | −₹276 / −₹226 |
| RSI bounce (0.4% · 0.6%) | 83 / 72 | −₹374 / −₹384 | ₹431 / ₹374 | −₹805 / −₹758 |

All rejected. Costs (about ₹5 per round trip on ₹5,000) are 4–6× the best edge found. This matches SEBI's July 2024 study:
71% of individual intraday traders lost money in FY23, 80% of those with more than 500 trades a year.
60 days is too short to prove anything either way, so the bot runs on paper daily and saves its own 5-minute history
(Actions cache). Real-money intraday also needs an always-on server with a static IP and a live broker feed.

## 8. "Best strategy out there" for 5-minute trading: Stocks-in-Play breakout (13 Nov 2026)
Akhil: real money; use pre-market sector volume, news, sentiment, the whole chart, best candle, entry and exit.
- Picked the best-documented retail 5-minute method: Zarattini, Barbon & Aziz (2024, SSRN 4729284). It uses abnormal
  opening volume as the news/sentiment signal, trades the first 5-minute candle's breakout, stop 10% of ATR, exit at close.
  In US stocks 2016–2023 it reported 41.6%/yr vs ~15% for the S&P 500 (cxoadvisory summary).
- India test (51 Nifty stocks, 60 sessions, Indian intraday costs 0.106% per round trip + slippage):
  top 3 by volume −3.7%; top 5 −3.7%; top 3 in the busiest sector −2.9%; all 51 −6.0%; 10-minute range worse (−5.6% to
  −6.6%); Nifty +5.7%. Losing in both halves of the data. Before costs the top-3 broke even: volume filtering helps, but not
  enough to pay Indian costs over this period.
- Data trap found and fixed: Yahoo shows 0 volume on the 09:15 bar for ~85% of days for NSE stocks; ranking uses the 09:20 bar.
- News reading: a study of a business newspaper's intraday tips in India found no significant returns (Kolte et al. 2024).
- **Decision: no real money on any intraday strategy until one passes on our own longer history.** All run on paper daily.

## 9. Kronos AI candlestick model (video: David Arias CFA, 13 Nov 2026)
Open-source foundation model for candlesticks (arXiv 2508.02739, MIT). Tested only on data after its release:
Nifty +13.4% / +12.8% (two seeds) vs +2.4% holding, worst fall about half; but Bank Nifty, the independent check, failed
(direction right 47.3% vs 53.7% "always up"; +6.3% vs +9.7% holding). **Mixed: paper only** (`paper/kronos/`, daily 16:15).
Today's call (13 Nov close): predicted −0.09% -> liquid ETF.

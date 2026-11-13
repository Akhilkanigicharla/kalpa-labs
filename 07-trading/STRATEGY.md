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

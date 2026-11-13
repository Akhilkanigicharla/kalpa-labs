# A275: intraday, 10–15 trades a day, ₹10,000 at 5x (14 Nov 2026)

Akhil: "I want intraday, 10 to 15 trades per day, success rate for each trade, total trades, profit and loss."
Script `a275_intraday_many_trades.py`; results `a275_results.csv` (picked on days 1–30, tested on days 31–60) and
`a275_high_frequency.csv` (tight targets that reach ~10 trades a day, all 60 days). Trade lists in `data/a275/` (git-ignored).

Setup: 5-minute bars, 18 Aug – 13 Nov 2026 (60 trading days, Yahoo's free limit), 20 liquid Nifty stocks + NIFTYBEES,
one trade at a time, ₹50,000 position (₹10,000 × 5 MIS), next-bar entry + 0.02% slippage, stop assumed first if a bar hits
both, all closed by 15:15, every NSE intraday charge. Charges average **₹52 per round trip** on ₹50,000.

## ~10 trades a day (all 60 days)
| Strategy | Target / stop | Trades/day | Success rate | Avg win | Avg loss | Charges | Net P&L | Net/day | Best day | Worst day | Green days |
|---|---|---|---|---|---|---|---|---|---|---|---|
| VWAP snap-back | 0.2% / 0.2% | 11.3 | 46.2% | +₹36 | −₹158 | ₹35,466 | −₹46,313 | −₹772 | +₹109 | −₹1,749 | 5% |
| EMA 9/21 + VWAP | 0.2% / 0.2% | 9.9 | 41.0% | +₹36 | −₹157 | ₹31,145 | −₹46,346 | −₹772 | −₹135 | −₹1,752 | 0% |
| VWAP snap-back | 0.3% / 0.2% | 9.3 | 39.0% | +₹84 | −₹157 | ₹29,086 | −₹35,160 | −₹586 | +₹429 | −₹1,599 | 8% |
| EMA 9/21 + VWAP | 0.3% / 0.2% | 8.9 | 34.7% | +₹84 | −₹157 | ₹27,995 | −₹39,320 | −₹655 | +₹94 | −₹1,536 | 5% |
| Volume-spike momentum | 0.2% / 0.2% | 8.6 | 41.7% | +₹36 | −₹155 | ₹26,829 | −₹38,623 | −₹644 | +₹128 | −₹1,487 | 2% |
| RSI(2) scalp | 0.2% / 0.2% | 8.3 | 49.4% | +₹36 | −₹157 | ₹25,996 | −₹30,761 | −₹513 | +₹184 | −₹1,314 | 7% |

At ~10 trades a day the ₹10,000 account is gone in **13 to 20 trading days**. Charges alone (~₹500/day) are 5% of the
account every day. A 0.2% target on ₹50,000 is ₹100 before charges and about ₹36 after; a 0.2% stop costs about ₹157.

## Best settings per strategy (picked on days 1–30, tested on days 31–60)
Wider targets (1%) give only 2–7 trades a day. Every one still lost on the test days: EMA cross −₹40/day (41.8% success),
RSI(2) −₹77/day, volume spike −₹154/day, ORB −₹212/day, VWAP snap-back −₹460/day.

## Verdict
No intraday strategy tested makes money after charges at this size, and 10–15 trades a day loses fastest.
Same finding as `aggressive-5k-2026-11-13.md` (306 stock/strategy combos). Not built as a money bot. Research only.

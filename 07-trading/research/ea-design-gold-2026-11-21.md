# A311 · Akhil's "XAUUSD Institutional EA" design (The5%ers High Stakes), backtested (21 Nov 2026)

Source: Akhil's upload (sections 1–9; the text stops inside section 9). Code `research/ea_design_gold.py`,
tests `tests/test_ea_design_gold.py`, numbers `reports/ea-design-gold*.json`.

## Fact checks on the design
- **Daily loss:** the doc says The5%ers High Stakes has no daily drawdown limit. Wrong: High Stakes terminates at
  **5% daily loss**. The doc's own 3% daily stop keeps it safe anyway.
- **Target:** step 1 is 8% (some sources say 10%), step 2 is 5%; max loss 10%. EAs are allowed (no HFT, arbitrage or tick scalping).
- **India:** The5%ers is not named on the RBI Alert List seen 21 Nov, but RBI says the list isn't exhaustive, and
  MetaTrader 4/5 themselves are on it. Legal grey area: get a CA's view before paying.
- **5-minute history:** only 60 days are free here; a longer download was blocked, so the M15/M5 test is short.

## Results
| Version | Period | Trades | Result |
|---|---|---|---|
| As written (H4 → H1 → M15 → M5) | 60 days | 1 | +1.6R (one win; no evidence) |
| As written, setup on H1 | 2 years | 0 | never trades |
| All $ numbers turned into ATR multiples (fixed in advance) | 60 days / 2 years | 1 / 0 | still almost never trades |

Why: 6 filters must all agree. H4 regime is "on" only 26% of the time, and with the H1 trend, the session,
the rejection candle and the "$30 room" rule, 1,700 London/NY 15-minute bars shrink to 1 trade.

## Which filters cost the trades (2 years, setup on H1, ATR-scaled; explains the design, not a pick)
| Removed | Trades/month | Avg R | Earlier / later half | Profit on $10K | Worst drop | The5%ers fail |
|---|---|---|---|---|---|---|
| room rule | 0.3 | +0.62 | +1.41 / +0.31 (7 trades) | +$330 | 0.8% | 0% |
| rejection + room | 1.0 | +0.20 | +0.37 / +0.09 | +$440 | 2.3% | 0% |
| + H1 agreement | 3.1 | +0.09 | +0.04 / +0.14 | +$595 | 6.0% | 0% |
| + pullback rule | 4.1 | +0.08 | +0.02 / +0.14 | +$690 | 6.7% | 0% (33% reach 8%) |

Reading: the design's risk side works (0.75% risk, 3% daily stop, never broke The5%ers' 5% daily or 10% max
loss in any start). The entry side is too strict to trade, and when loosened it earns about +0.1R a trade,
around $300 a year on $10K: an 8% target takes ~2.5 years at that pace.

# A330 · Long-history check of every gold idea (21 Nov 2026)

Akhil asked for hedge-fund-grade checks and live trading in India. Everything before this was tested on 2 years of hourly data. This note tests on 22–26 years of daily data, with the methods quant funds use:
- recipes fixed before the test, with no tuning to the data
- placebo (random) entries
- a Sharpe ratio adjusted for how many versions were tried (deflated Sharpe)
- double costs

## Results

| Test | Data | Result | Verdict |
|---|---|---|---|
| Gold trend following (AQR-style 1/3/6/12-month, 10% vol) | 2000–2026 | Sharpe 0.33, 2.3% a year, worst drop −30%; holding gold beat it (Sharpe 0.74); deflated-Sharpe probability 0.58 | Weak |
| Same recipe on 13 markets The5%ers offers | 2000–2026 | Sharpe 0.17, 1.2% a year, −32% worst drop; negative with double costs; 2010s and 2020s about zero | Weak |
| Same recipe on an India-tradable basket (Nifty, Bank Nifty, MCX gold, silver, crude, copper, USD/INR) | 2004–2026 | Sharpe 0.18, 1.4% a year, −42% worst drop; last 2 years +12% a year | Weak |
| MSNR fresh_v + QM (the mix's main earners) on daily bars, 10 markets × 4 setups | 1998–2026 | Average edge over random entries −0.01R; 21 of 40 beat random | No general edge |

Daily MSNR setups that beat random entries by a clear margin in both halves of the data:
- gold fresh_v short
- Nifty fresh_v long and short
- USD/JPY QM long
- oil QM long

These are 5 or 6 out of 40, about what luck alone would produce, so they are candidates to watch, not proof.

## What this means

No public technique tested gives a large, proven edge on its own after costs. The 2-year intraday mix (+0.10R a trade over random) is still the best result we have. Its daily-bar version does not hold up over 25 years, so the intraday result may be partly this period's regime. The 6-month forward test (A324) is the deciding test. No real money should go in before it passes.

## India (sources fetched 21 Nov 2026)

- **RBI:** residents may deal in forex only with authorised persons and on authorised electronic trading platforms. Using unauthorised ones is liable to penal action under FEMA.
- **RBI Alert List:** it names prop firms, for example FundedNext and Smart Prop Trader. The5%ers is not confirmed either way; not being on the list does not mean a firm is authorised.
- **The legal live route** is an Indian exchange (NSE/MCX) through a SEBI-registered broker's API.
- **SEBI's retail algo framework** has been in force since 1 Apr 2026. API orders must come from a static IP whitelisted by the broker.
- **Dhan's trading API** is free and covers MCX.
- **MCX Gold Petal** (1 g lot, ₹1 tick) allows small position sizes.

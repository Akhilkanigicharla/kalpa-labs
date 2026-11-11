# Currency pairs in the Trading Lab (A210, 11 Nov 2026)

Akhil asked to connect OctaFX; that was refused (RBI Alert List, ED case). He said "yes currency" to the lawful alternative.

## What was checked on 11 Nov 2026
- RBI A.P. (DIR Series) Circular No. 25, 10 Oct 2026, and SEBI circular of 5 Nov 2026 (read via taxguru.in, tradingqna.com/Zerodha, moneylife.in; RBI's own page not fetched, so treat the exact wording as second-hand): rupee currency derivatives on NSE/BSE are for hedging a real foreign-currency exposure. Up to USD 5 million (all pairs and exchanges together) a trader need not show documents, but the exposure must exist.
- So a bot that only speculates on USDINR is NOT a clean, lawful product for Akhil today. Kalpa has no foreign-currency income or bills yet.
- Cross-currency futures (EURUSD etc.) and whether they need an exposure: unverified. Liquidity: unverified.

## What we built
- `src/data.py`: `FX_PAIRS` (USDINR, EURINR, GBPINR, JPYINR) map to Yahoo `=X` spot rates. Spot rate, not NSE futures prices; costs in the tear-sheet are the equity model, so results are indicative only.
- `backtest.yml`: one tear-sheet per pair, research only.
- `src/live.py`: `Guard.run_once` refuses every currency pair, even if someone adds it to the universe.

## When this could change
If Kalpa starts earning in dollars (extension sales, affiliate payouts), hedging that income with USDINR futures through the SEBI-registered broker becomes a real use. Akhil decides then, after a CA confirms.

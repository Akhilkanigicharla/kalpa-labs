# A309 · Every MSNR playlist setup on gold, tested robustly (21 Nov 2026)

Akhil: "Build it very robust, did you malaysh[ian]" + the MSNR playlist (Sujith Surya, 36 videos).
Code `research/msnr_gold_robust.py` (tests `tests/test_msnr_gold_robust.py`); raw numbers in `reports/msnr-gold-robust-*.json`.

**Did A308 use the playlist?** Partly: A/V levels from closes, fresh first touch and flips. A309 adds the rest that
can be coded from the playlist mapping (`research/msnr-2026-11-20.md`): storyline, QM, equal-low sweep, key-level width.
Session models (Asia range, 30-minute breaker blocks) still need intraday history we don't have for free, and the
videos themselves can't be read from the cloud (YouTube bot check), so the rules come from the open-source MSNR scripts.

## What was tested: 384 versions
4 setups (fresh level, QM, equal-low sweep, A308 rejection) × buy/sell × 1h, 4h, daily × key level 2/5 × storyline on/off
× 9 EMA on/off × $3,100 rule on/off. Gold futures GC=F: hourly Jul 2024 → 20 Nov 2026, daily 2005 → 2026.

## Pass rules (fixed before results)
Later data (1h/4h from 1 Sep 2025, daily from 2019) must have ≥ 30 trades and ≥ +0.10R per trade at **double** costs;
the earlier data must also be positive; it must beat matched random entries after correcting for testing 384 versions
(Benjamini-Hochberg q < 0.10); and the same setup with the other key-level width must also be positive.

## Result: 0 of 384 pass
- Not one version beats random entries once the 384 tries are accounted for (best q = 0.19).
- 62 versions made ≥ +0.10R on the later data, but random entries made money in the same falling market too.
- **Akhil's rule (9 EMA + $3,100), closest:** 1h fresh-level shorts, +0.27R (175 trades, double costs) vs +0.13R random,
  and the earlier data only +0.03R. 4h fresh-level shorts (key level 5): +0.33R vs +0.06R random, 126 trades, q 0.28.
- Best overall: daily fresh-level **buys** (+0.69R vs +0.27R random). That is buying dips in gold's 2019–2026 bull market.
- QM, sweeps and the A308 rejection trigger: nothing usable on gold.

Matches the independent MSNR study (Sean Solano Paul 2026, gold/silver/crypto: no edge vs random entries).

## What runs now (paper only, no orders)
The three versions closest to passing under Akhil's rule were picked **before** any forward data existed and are
paper-tested every weekday from 21 Nov 2026 in `paper/msnr-gold-robust/state.json`, next to A308's rule.
A version earns real-money talk only after 30+ forward trades averaging ≥ +0.10R.

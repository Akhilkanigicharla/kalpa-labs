# A250: Kronos-small as a probability forecaster (28 Nov 2026)

Rules fixed before running: `research/kronos_brier.py` docstring. Scores: `src/kronos_score.py` (tests: `tests/test_kronos_score.py`).
Runs: GitHub Actions `kronos-brier.yml` run 46079270150 (all 4) + one local re-run of Nifty daily (identical numbers, so it is reproducible).
Raw rows + JSON: `research/kronos_brier/`. Lower Brier / log-loss = better. Random walk = 0.250 / 0.693.

| Market | Bars (out of sample) | Brier Kronos / RW / base | Log-loss Kronos / RW / base | Direction hit | After costs vs hold | Random signals beat it | Pass |
|---|---|---|---|---|---|---|---|
| Nifty daily | 322 (1 Aug 2025 – 25 Nov 2026) | 0.285 / 0.250 / 0.251 | 0.797 / 0.693 / 0.695 | 54.0% | +13.8% vs +5.2% | 0.8% | no |
| Bank Nifty daily | 322 | 0.334 / 0.250 / 0.249 | 0.955 / 0.693 / 0.691 | 46.0% | +0.0% vs +15.0% | 31% | no |
| Nifty 15-min | 1,098 (23 Sep – 27 Nov 2026) | 0.346 / 0.250 / 0.252 | 1.036 / 0.693 / 0.696 | 50.2% | −10.1% vs +9.5% | 0% | no |
| Bank Nifty 15-min | 1,098 | 0.342 / 0.250 / 0.254 | 1.002 / 0.693 / 0.701 | 48.7% | −10.3% vs +11.9% | 0% | no |

## Verdict
- Kronos's sampled P(up) is **worse than a coin flip on every market** (Brier and log-loss above the random walk): its 20 samples agree too often, so it is confidently wrong. This matches the independent BTC test in `video-kronos-candlestick-model.md`.
- The only good number is the Nifty daily *money* result (+13.8% vs +5.2%), already seen in A261. It does not repeat on Bank Nifty or on 15-min bars, so treat it as likely luck in one market and window.
- Decision by the pre-set bar: **no new Kronos paper run** (15-min or Bank Nifty). The existing A261 daily paper run keeps going to its 90 days; it must not get real money on this evidence.
- Limits: daily window ~1.3 years; 15-min only ~2 months (yfinance keeps 60 days); 0.06% per side costs are an assumption; one seed.

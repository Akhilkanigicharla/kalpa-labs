# A358 · Frozen config in the live paper runner + the NIFTYBEES Oct 2010 move (28 Nov 2026)

## 1. Runner trades only a frozen config
- `python -m src.livetrade.runner --trial <id>` loads the trial's `frozen_config` from `research/trials.csv`
  and trades exactly those params. It never re-picks them. It refuses if the trial is not frozen, if the
  strategy or symbol differs, or if the rule code changed since the freeze (`trials.verify_frozen`).
- No `--trial` → paper refuses (exit 2), unless `--learning` is passed. Learning = today's daily paper
  track (params re-picked every day). Its summary says "LEARNING track … never counts towards live".
- The state file remembers its trial. A learning state and a trial state can't mix (use a new `--out`).
- Live needs `--trial`, `GATE_PASS_<track>` must name that trial, and only paper days logged **under
  that trial** count towards the 90 days. So the 90 learning days in `paper/track-A/` can never unlock live.
- Dhan Cloud (`deploy/dhan-cloud/main.py`): reads `KALPA_TRIAL_NIFTY` / `KALPA_TRIAL_GOLD` and the
  registry from GitHub; refuses if either is missing.
- `paper-trade.yml` legs now pass `--learning` (same behaviour as before, now labelled).

## 2. NIFTYBEES 6–7 Oct 2010: a bad tick, not a split
Yahoo `NIFTYBEES.NS` closes, fetched today, next to `^NSEI`:

| Date | NIFTYBEES close | move | Nifty 50 move | volume (units) |
|---|---|---|---|---|
| 5 Oct 2010 | 62.10 | | | 3,210 |
| 6 Oct 2010 | **52.50** (= day low) | −15.5% | +0.7% | 2,470 |
| 7 Oct 2010 | 61.62 | +17.4% | −1.1% | 10,390 |

The price snaps straight back and the index did not move, so it is one wrong close on a thin day,
not a split (a split never snaps back). The same check also finds **5 Feb 2010** (49.20 → 54.50 → 48.21,
+10.8% then −11.6%, Nifty −2.6% then +0.9%). Nothing else in 2009–2026.

`data.repair_spikes` misses both (its limit is 40%). New:
- `data.index_mismatch(etf, index, tol=0.08)`: closes that move > 8% away from the index and snap back
  the next day. A move the index also made is never flagged. Uses the next day, so history cleaning only.
- `data.drop_index_mismatch(...)`: drops them and lists the dates.
- Runner guard (decision day only, no look-ahead): if the traded ETF's one-day move differs from the
  signal series' move by more than 8%, it refuses to trade that day.

Not done here (separate item if wanted): running `drop_index_mismatch` inside gate/tournament backtests
that read NIFTYBEES closes. Today's paper leg reads its signal from `^NSEI`, so it is not affected.

Tests: `tests/test_a358_frozen_runner.py` (9), updated `test_livetrade.py`, `test_dhan_cloud.py`.

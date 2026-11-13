# Kalpa b7 live bot on Dhan Cloud (₹10,000)

**What it does:** every trading morning at 09:20 IST it runs the ₹10,000 plan from `research/a163-nifty-gold-10k-2026-11-13.md` with real Dhan orders:
- ₹5,000 **Nifty trend** (NIFTYBEES): holds Nifty when the 63-day trend is up, sells to cash when it turns down, 20% protective stop.
- ₹5,000 **gold held** (GOLDBEES): bought once, kept.

Backtest 2012–2026 after all costs: **10.4% a year**, worst fall −12.4%, worst calendar year −4.7%, about 4 trades a year. On ₹10,000 that is about **₹1,040 a year**. Past results are not a promise; the paper run is the real test.

**Why Dhan Cloud (checked on Dhan's own FAQ, 14 Nov 2026):** no static IP needed there; it can place live orders; it syncs the access token itself (no daily login); it runs on a schedule; Python 3.11; installs `requirements.txt`. Trading APIs are free; Dhan Cloud itself is pay-per-use (see its Estimator; this bot runs ~1 minute a day).

## Safety built in (all tested: `python -m pytest -q`, 172 tests)
- ₹10,000 hard maximum in code; each leg can only touch its own ETF and its own ₹5,000.
- Every buy has a stop; if the saved stop is ever lost, it is rebuilt from Dhan's average cost.
- Daily / weekly / monthly loss caps and a drawdown pause; one trade per ETF per day; whole units only.
- An order whose reply is lost is looked up by its ID, **never sent twice**.
- Phone kill switch: add an empty file `07-trading/paper/track-A/flags/KILL` in the GitHub app → no new buys.
- It refuses (no order at all) unless every rule below holds.

## Rules before real money (your rules, CLAUDE.md + A153)
1. The GitHub paper run has logged **90 trading days** (it runs every weekday at 16:15 IST; started 13 Nov 2026).
2. You sign off the gate: Dhan Cloud global variable `KALPA_GATE_PASS` = `yes`.
3. You say go: global variables `LIVE_TRADING` = `YES` and `KALPA_GO` = `go`.
Changing rule 1 is your decision only (the number is `PAPER_DAYS_MIN` in `src/livetrade/runner.py`).

## Your steps (laptop, ~20 min, once)
1. Dhan account with ₹10,000 added (free demat).
2. web.dhan.co → profile → **DhanHQ / Dhan Cloud** → create a strategy → upload `upload/kalpa-b7-dhan-cloud.zip` (entry file `main.py`).
3. Schedule: weekdays **09:20 IST**.
4. Global variables: `LIVE_TRADING=YES`, `KALPA_GO=go`, `KALPA_GATE_PASS=yes` (only when rule 1 is met). If Dhan's token variable has an unusual name, set `KALPA_TOKEN_VAR` to that name.
5. Never paste your token anywhere else, including chat.

Rebuild the zip after code changes: `./build.sh` (Claude does this).

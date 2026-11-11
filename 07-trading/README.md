# 🔮 Trading Lab · world b7 (The Market Maze)

**What it is:** Backtesting + 90-day paper trading on legal Indian venues. Research only, no tips.
**Status (13 Oct 2026):** Lab core built (data, Indian costs, gate, trials registry; 24 tests green). Paper only. No real money until the gate passes and the CEO signs capital rules.
**Price:** Not sold. Earns ₹0 in year 1 by design.

## What's in this folder

| Label | File or folder | What it holds |
|---|---|---|
| 📋 Plan | [PLAN.md](PLAN.md) | Verdict, customer, unit economics, go-to-market, quests, kill rules, what's needed from Akhil |
| 🔎 Research | [research/](research/) | GitHub repos checked, cloned and run: adopt / learn / avoid |
| 📝 Docs | [docs/](docs/) | Decisions, requirements, sales material |
| 🎨 Design | [design/](design/) | UI design brief and mockups (filled by the build sprints) |
| 💻 Code | [src/](src/) | `data.py` (cached daily bars + validator), `costs.py` (2026 Indian charges with sources), `strategies.py`, `backtest.py`, `metrics.py` (PSR, DSR, PBO), `gate.py`, `trials.py` |
| 🧪 Tests | [tests/](tests/) | `cd 07-trading && python -m pytest -q` (synthetic data only) |
| 🧾 Paper + risk | [src/paper.py](src/paper.py), [src/risk.py](src/risk.py) | `python -m src.paper --symbol NIFTYBEES --days 20`: next-open fills, delivery costs, §5a rules (pending sign-off), no broker calls |
| 📈 Tear-sheet | [src/tearsheet.py](src/tearsheet.py) | `python -m src.tearsheet --symbol ^NSEI` (or `--synthetic`); runs in `.github/workflows/backtest.yml`, HTML artifact `tearsheet` |
| 🛡️ Live-ready layer (A153) | [src/live/](src/live/), [src/crypto_tax.py](src/crypto_tax.py) | `python -m src.live.runner --track A\|B --mode paper --synthetic`: strategy (bars after the decision time are invisible) → Live Guard → FakeBroker, ledger + Telegram-ready summary vs buy-and-hold after costs and tax, win rate / payoff / expectancy. Real adapters (FYERS, Dhan, Delta India, CoinDCX) are stubs. Output in `data/live/` (git-ignored) |
| 🧬 Ensemble | [src/ensemble.py](src/ensemble.py) | Darwinian weighting across strategies (method: chrisworsey55/atlas-gic, MIT): only strategies with gate verdict `paper` are eligible (others weight 0); weights from rolling out-of-sample Sharpe (past bars only), 0.3–2.5, top quarter ×1.05, bottom ×0.95 each bar; combined target = weighted average, sent through `run_paper` → Live Guard → FakeBroker. `run_paper_ensemble(...)`, paper only. Not wired into any workflow; today no strategy has passed the gate, so it holds cash |
| 📒 Trials | [research/trials.csv](research/trials.csv) | Every trial must be logged here before the gate will run it |

## Going live (track A ETF bot, track B crypto bot)
Live mode refuses to run until **every** line is true. Capital: ₹5,000 to start, ₹10,000 hard max (code refuses more).
1. **Paper 90 days** with `--mode paper` (the runner counts them in `data/live/out/state-<track>.json`).
2. **Gate pass:** the strategy gets verdict `paper` from `gate.py` on real data, logged in `research/trials.csv`; Akhil then creates `data/live/GATE_PASS_<track>` himself.
3. **Keys as secrets, set by Akhil only:** broker/exchange API keys as environment secrets (`FYERS_CLIENT_ID`/`FYERS_ACCESS_TOKEN`, `DHAN_*`, `DELTA_API_KEY`/`DELTA_API_SECRET`, `COINDCX_*`). Claude never sees, logs or types them.
4. **Track A only:** a **static IP whitelisted** at the broker (SEBI rule since 1 Apr 2026; e.g. Oracle free VM reserved IP, Akhil's call) and a **2FA login every trading day** (no overnight sessions).
5. **Akhil types go:** `LIVE_TRADING=YES` in the server env **and** the file `data/live/GO` containing `go`. Kill switch: create `data/live/KILL` (blocks all buys; `--flatten` sells everything).
Then the adapter for the chosen broker still has to be built and tested (today they raise `NotImplementedError`). Own money only, no tips to anyone (SEBI).

## Research reports
- [research/a8-trading.md](research/a8-trading.md)
- [research/deep-scan-v2.md](research/deep-scan-v2.md): top 35 repos, engine bake-off, gate calibration, Nifty 50 dry run

## Licence note (Q7.1)
`src/` is our own code. Only permissive libraries are dependencies (bt MIT, quantstats Apache-2.0, pandas/numpy/scipy BSD, yfinance Apache-2.0); see [NOTICE](NOTICE). Never copy code from GPL (freqtrade, backtrader), AGPL (backtesting.py, pypbo, OpenAlgo) or Commons-Clause (vectorbt, pybroker) projects. Market data lives in `07-trading/data/` (git-ignored) and is never committed or redistributed.

## Next steps
See this world's lines in [../00-hq/ROADMAP.md](../00-hq/ROADMAP.md): agent tasks run automatically in the build sprints, CEO tasks show up in the morning brief.

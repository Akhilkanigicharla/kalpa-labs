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
| 📈 Tear-sheet | [src/tearsheet.py](src/tearsheet.py) | `python -m src.tearsheet --symbol ^NSEI` (or `--synthetic`); runs in `.github/workflows/backtest.yml`, HTML artifact `tearsheet` |
| 📒 Trials | [research/trials.csv](research/trials.csv) | Every trial must be logged here before the gate will run it |

## Research reports
- [research/a8-trading.md](research/a8-trading.md)
- [research/deep-scan-v2.md](research/deep-scan-v2.md): top 35 repos, engine bake-off, gate calibration, Nifty 50 dry run

## Licence note (Q7.1)
`src/` is our own code. Only permissive libraries are dependencies (bt MIT, quantstats Apache-2.0, pandas/numpy/scipy BSD, yfinance Apache-2.0); see [NOTICE](NOTICE). Never copy code from GPL (freqtrade, backtrader), AGPL (backtesting.py, pypbo, OpenAlgo) or Commons-Clause (vectorbt, pybroker) projects. Market data lives in `07-trading/data/` (git-ignored) and is never committed or redistributed.

## Next steps
See this world's lines in [../00-hq/ROADMAP.md](../00-hq/ROADMAP.md): agent tasks run automatically in the build sprints, CEO tasks show up in the morning brief.

# TradingAgents (MIT/UCLA "AI hedge fund"): what b7 takes from it

Checked 18 Oct 2026 (IST). Source video: AI Pathways, "MIT Researchers Built An AI Hedge Fund (Here's How To Use It)" (youtube.com/watch?v=w-8XSCgwzHw, 24 Sep 2026, transcript read in full). Repo: https://github.com/TauricResearch/TradingAgents. Paper: arXiv 2412.20138. Research and engineering notes only, not investment advice.

## Verdict: ADOPT as a research input, never as a signal

| Check | Finding |
|---|---|
| Licence | Apache-2.0 (repo LICENSE). We call it as a library; nothing copied into a sold product. |
| Health | 111.7k stars, 21.5k forks, v0.7.0 released 16 Oct 2026, CI gate, 493 commits (repo page, 18 Oct 2026). |
| Models | Any provider, incl. **OpenRouter** (`llm_provider=openrouter`, `OPENROUTER_API_KEY`), Ollama, OpenAI-compatible. Quick tier (analysts, debaters, trader) and deep tier (research + portfolio managers) can use different models. |
| Markets | Anything Yahoo Finance covers: `RELIANCE.NS`, `.BO`, crypto `BTC-USD`. Benchmark per region. |
| Honesty features | Point-in-time data (no look-ahead), SEC filings "as filed", decision memory scored after the holding window, `backtest` over a ticker × date grid. Their own README: LLM runs are non-deterministic and "not intended as financial, investment, or trading advice". |
| Cost | Code is free; every run makes many model calls (the video: ~100k tokens, about $1.26 on a paid model). On OpenRouter free models one run can use a large share of the ~50 requests/day free quota. |

## How it maps to our n8n Trading Desk

| TradingAgents role | Kalpa agent | What we added (18 Oct) |
|---|---|---|
| Market, fundamentals, news, sentiment analysts | Pulse (live news via Firecrawl/Brave), Quant | Quant skill `bull-bear-debate` step 2 |
| Bull researcher vs bear researcher, research manager | Quant | `bull-bear-debate` steps 3–6 (one rebuttal round to save quota) |
| Trader (turns view into a plan) | Quant | `bull-bear-debate` step 7: paper plan card |
| Aggressive / conservative / balanced risk team, portfolio manager | Guard | Guard skill `three-angle-risk-review` with our hard limits |
| Decision memory / reflection | `07-trading/src/trials.py` + `research/trials.csv` | Already ours; the lab gate stays the final word |

## Rules (from 07-trading/PLAN.md and CLAUDE.md rule 4)
1. Paper only. No broker keys anywhere. Nothing from this tool places an order.
2. Year-1 markets: NSE/BSE cash delivery only. The workflow refuses other tickers.
3. A TradingAgents rating is one input. A plan still needs Guard's APPROVE FOR PAPER, then the lab gate (walk-forward, costs, PBO), then 90 days of paper.
4. Never publish or share a rating as a tip (SEBI). Education content made from a run must say "research only" and contain no buy/sell call.
5. At most one run a week on free models, analysts `market,news,fundamentals`, 1 debate round, 1 risk round.

## How to run (when Akhil wants one)
1. Akhil adds repo secret `OPENROUTER_API_KEY` (GitHub → Settings → Secrets and variables → Actions). Claude never sees it.
2. GitHub → Actions → "b7 TradingAgents research (manual)" → Run workflow → ticker (default `NIFTYBEES.NS`).
3. Download the `tradingagents-…` artifact: `complete_report.html` + logs. Give the report to Quant's `bull-bear-debate` as input data.

Workflow: `.github/workflows/tradingagents.yml` (pinned to commit `c4544913`, v0.7.1, since 21 Nov 2026; was `e8f5503e`, v0.7.0).

## Update 21 Nov 2026 (Akhil's reel, @kaamchor_ai, showing v0.7.1)
- Pin moved v0.7.0 → **v0.7.1** (tag `c4544913`, released 27 Oct 2026, Apache-2.0, checked with `git ls-remote` + the CHANGELOG).
- Why it matters for us:
  - **#1488:** a model's date like `2024-7-5` could compare as later than a filing made after the run date, so SEC EDGAR served future filings. That is look-ahead bias, now fixed.
  - **#1548:** decisions are scored only on final closes, and they settle across long market holidays (Diwali, Holi).
- Checked here: installs clean in Python, `import tradingagents` = 0.7.1, the CLI still has `--ticker --date --analysts --save --no-show`. No workflow change was needed beyond the pin.
- **Verdict unchanged:** a research input, never a signal; paper only; at most one run a week on free models; LLM look-ahead bias still applies (arXiv 2504.14765). The reel's "har agent = 1 kaam" idea is already our n8n Trading Desk (Pulse, Quant, Guard).

## First full run, 21 Nov 2026 (Akhil: "Run")
- **OpenRouter free quota was already used up** that day (429, shared with the n8n agents).
- So the workflow got a `provider` choice: **google** (the `GEMINI_API_KEY` secret, now the default) or openrouter.
- Gemini models on the free key:
  - 2.5 Flash is closed to new users (404).
  - 3.8 Flash answered "high demand" (503).
  - **3.5 Flash-Lite worked for all agents.**
- Also fixed: `set -o pipefail`. Before, `tee` hid a failed run as "success".
- **Result for NIFTYBEES as of 20 Nov:** HOLD.
  - The trend is strong, but it is overbought (RSI 76.84), so add only on a pullback to ~284.79, stop 276.43.
  - Every figure matches the 19 Nov close in our own Yahoo data (point-in-time, no look-ahead).
  - Report: `07-trading/reports/tradingagents/NIFTYBEES-2026-11-20.md`.
- SEC EDGAR returned 403 for an Indian ETF (expected; it falls back to Yahoo).

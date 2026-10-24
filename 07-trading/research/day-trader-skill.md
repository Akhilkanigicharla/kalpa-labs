# Day Trader Skill (Jakeschincariol): vetted 24 Oct 2026

**Answer first:** **TRY LATER, ideas only.** It is clean MIT code, but it trades **US stocks through Alpaca**, and b7 is **paper only, Indian venues, no tips** (SEBI rule in `CLAUDE.md`). So we don't install it to trade. We borrow three of its ideas into our own lab instead.

- **Repo:** https://github.com/Jakeschincariol/day-trader-skill
- **Stars, licence, dates:** 936 stars, MIT, created and last pushed 20 Oct 2026, 205 forks, 8 open issues. Source: GitHub search API, 24 Oct 2026.
- **Seen in:** an Instagram reel ("Claude just changed trading"), sent by Akhil.
- **Checked:** README plus a read-only clone at commit `3d0f4ef` (20 Oct 2026). **No code was run**, and none was copied into this repo.

## What it is

11 skills, each one SKILL.md plus a single Python standard-library script (about 13,100 lines in total, with a unittest suite):

| Skill | What it does |
|---|---|
| `trader-scanner` | Scans about 5,900 US symbols (Nasdaq Trader list) for opening-range breakouts, flags and oversold bounces |
| `trader-news` | Yahoo Finance RSS for your watchlist |
| `trader-entry`, `trader-exit` | Bar-by-bar entry signal; stop and target set before entry |
| `trader-timemachine` | Replays a setup over simulated sessions plus past instances (60 days of 5-minute bars). The README calls it "a simulation, not a prediction" |
| `trader-risk` | Checks each order against your limits and returns **PASS** or **BLOCK** |
| `trader-budget` | Sizes a position from budget and max loss per trade |
| `trader-broker` | Builds order tickets for **Alpaca's MCP server**. `ticket.py` never calls a broker itself. An order needs a risk PASS, plus a typed "yes", plus Claude's Allow click. Paper is the default (`ALPACA_PAPER_TRADE=true`) |
| `trader-alerts`, `trader-analyst`, `trader-pelosi` | Price alerts; SEC EDGAR earnings facts; US House trade disclosures |

## Security check (read-only)

- **Network:** only public data hosts appear in the code: Yahoo Finance, SEC / data.sec.gov, House Clerk, Nasdaq Trader, NYSE, Stooq. No analytics or telemetry endpoint was found.
- **Processes:** one `subprocess.run`, in `trader-pelosi/ptr.py`, which calls the local `pdftotext` tool on a PDF. No `eval`/`exec`, no hooks folder, no binaries.
- **Credentials:** none for data. The SEC tools want a name and email in the `SEC_USER_AGENT` header. The broker example wants Alpaca keys in environment variables ("never in chat").
- **Risk for us:** the broker skill exists to place orders, and its README also covers an Interactive Brokers connector. Connecting any broker would break the b7 paper-only rule. **Never install `trader-broker` and never add a broker MCP.**

## Why not adopt it as-is

1. **Wrong market.** It is built for US equities, New York time, US data and FINRA PDT rules. b7 works on NSE/BSE, with Indian costs in `07-trading/src/costs.py`.
2. **Day trading.** Our gate (`src/gate.py`) and research found intraday edges too weak after Indian costs (`research/deep-scan-v2.md`).
3. **SEBI.** b7 gives no tips and trades on paper only. The scanner, entry and Pelosi skills read like signals, so we must not publish their output.
4. **New.** The repo is 4 days old and has one commit.

## What we borrow (ideas, written in our own code)

| Idea | Where it would go | Status |
|---|---|---|
| Risk **PASS/BLOCK fingerprint**: a paper order runs only if the risk check passed that exact order today | `07-trading/src/risk.py` + `src/paper.py` | Proposed (new roadmap item, not built) |
| **Plan-before-entry**: stop, target and max loss are written before any paper entry, then logged | `src/paper.py` trade log | Proposed |
| **"Time machine" replay**: Monte-Carlo resamples of past instances of a setup, giving an odds range, not a forecast | complements `src/metrics.py` (PSR/DSR/PBO) | Proposed |

## If Akhil still wants to try it (learning only, no money)

In a **cloud** Claude Code session, not on the PC (rule 2), and **without** the broker skill:

```text
/plugin marketplace add Jakeschincariol/day-trader-skill
/plugin install day-trader-skill@day-trader-skill
```

Then use only the scanner, time machine, risk and budget skills, on US symbols, as a demo. Don't paste Alpaca or any broker keys anywhere.

**Next step:** say "build the risk gate" and the next build sprint will add the PASS/BLOCK fingerprint to our paper trader, with tests (about 1 sprint).

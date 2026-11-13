# Brief for the trading-bot session: Akhil's 4 videos (14 Nov 2026)

Written by session 01CYFoi2 for any session that can't open YouTube. Facts come from the video pages,
the videos' own descriptions and pinned comments, a transcript, and the GitHub repo pages, read on 14 Nov 2026.
Kalpa's own test numbers are marked **[Kalpa test]**.

## 1. Revelio Trading: "He turned $400 into $200M, so I stole his Strategy" (21 Oct 2026, 13 min)
- **Topic:** the Turtle Traders. In 1983 Richard Dennis bet he could teach beginners to trade in two weeks. The rules were later made public (Curtis Faith, "The Original Turtle Trading Rules", free PDF 2003; "Way of the Turtle", 2007).
- **Video's test:** the rules on 5 markets (NQ/Nasdaq, ES/S&P 500, gold, silver, Bitcoin) for about 11 years, "adapted for today's traders", plus a day-trading version that closes each trade the same day (needs 30-min candles or smaller).
- **Free indicator:** "Turtle Breakout - Revelio" on TradingView, https://www.tradingview.com/script/Hd9ebcRm-Turtle-Breakout-Revelio/ (not in TradingView search; some commenters report Pine syntax errors).
- **Author's numbers since 2016 (pinned comment):** Bitcoin +17,683%, Turtle +1,743%, Nasdaq +589%, Turtle without Bitcoin +429%, silver +318%, gold +289%, S&P 500 +280%.
- **A commenter's check, which the author did not dispute:** holding all five equally (rebalanced) gives about 28%/yr against about 31%/yr for Turtle. Turtle runs at about 1.6–2x leverage. Without Bitcoin it is about 17% vs 16%. So it beats holding only barely, and only with leverage. Another commenter points out survivorship bias: the markets were chosen because they did well.
- **Original Turtle rules (from a comment, matching Faith's PDF):**
  - System 1: 20-day breakout, 10-day exit, skip the next signal after a winner.
  - System 2: 55-day breakout, 20-day exit.
  - Pyramid every 0.5N, up to 4 units; at most 6 units in closely related markets.
  - Cut position size 20% after a 10% loss.
- **[Kalpa test]** `turtle` (long only, closes only, entry 20/55, exit 10/20) is in `src/strategies.py`. It was run through the same walk-forward as Track A, with idle cash earning 4.7% (trials T0025–T0027):

  | Market | Turtle (yr / worst fall) | tsmom | Buy & hold |
  |---|---|---|---|
  | Nifty | 2.2% / −20.6% | 9.1% / −15.7% | 10.5% / −38.4% |
  | Bank Nifty | 8.8% / −29.2% | 6.2% / −25.3% | 12.2% / −47.9% |
  | GOLDBEES | 6.2% / −19.0% | 8.1% / −35.7% | 10.6% / −27.4% |

  **Verdict:** not better for Track A (Nifty trend + gold held). Possible follow-up: Turtle as the gold-leg timer, since it has the smallest fall (−19%). This needs a full gate run first.

## 2. Hamza Editz: "Free GitHub RDP Cloud PC for unlimited days, 16 GB RAM" (22 Sep 2026)
- Uses GitHub Actions runners as a remote desktop.
- **Do not use.** GitHub's Additional Product Terms forbid using GitHub-hosted runners for "any other activity unrelated to the production, testing, deployment, or publication of the software project". Misuse can end jobs, disable repos or suspend the account. Kalpa's paper-trading workflows are fine because they run our own repo's code.

## 3. Corey Ganim: "make money with Claude + free GitHub repos" (11 Nov 2026, 25 min)
- **Method:** one master prompt, then in order: find popular repos → pick an offer → ICP → offer brief → leads → ads/UGC videos.
- **Repos it found:**
  - TastyIgniter: MIT, 3.9k stars, Laravel/PHP 8.3+, restaurant online ordering + table booking.
  - Dograh: BSD-2, 6.1k stars, self-hosted voice AI (Vapi/Retell alternative). Twilio/Vonage/Telnyx/Plivo/Asterisk; bring your own LLM, speech-to-text and text-to-speech.
  - Chatwoot: MIT core plus a separate `enterprise` folder, 39.8k stars, omnichannel inbox.
- **Offer picked in the video:** a commission-free direct-ordering site for restaurants at a flat monthly fee.
- **India data:** Swiggy/Zomato charge 16–30%; Rapido and ONDC-based apps charge 8–15%.
- **Not trading.** It is logged for Akhil as C85; no build without his yes.

## 4. Miles Deutscher: "I Tested The Viral Claude Day Trader Repo (11 Free Skills)" (12 Nov 2026, 14 min)
- **Repo:** https://github.com/jakeschincariol/day-trader-skill (MIT, ~7.5k stars, last commit 20 Oct 2026). US stocks only.
- **Data:** free sources only (Yahoo Finance, Nasdaq Trader symbol lists, SEC EDGAR, House Clerk), no signup.
- **The 11 skills:**
  1. `/trader-scanner`: opening-range breakouts, flags, oversold bounces across thousands of charts
  2. `/trader-news`: breaking-news monitor
  3. `/trader-entry`: watches a setup bar by bar for the entry
  4. `/trader-exit`: stop and target set before entry
  5. `/trader-timemachine`: replays the rest of the session 10,000 times from the stock's own last 60 days of 5-min bars, plus every past day the same setup fired
  6. `/trader-risk`: blocks trades over your limits
  7. `/trader-budget`: position size from budget and max loss per trade
  8. `/trader-broker`: Alpaca MCP, paper by default, never sends an order without the user's yes
  9. `/trader-alerts`: price, stop and opening-bell alerts
  10. `/trader-analyst`: earnings summaries
  11. `/trader-pelosi`: US Congress trade disclosures
- **Related repo:** https://github.com/tradermonty/claude-trading-skills (MIT, ~4.1k stars, updated 13 Nov 2026).
  - Free or yfinance-only skills: market-breadth-analyzer, uptrend-analyzer, position-sizer, trader-memory-core, signal-postmortem, macro-regime-detector.
  - Risk and backtest skills: drawdown-circuit-breaker (TRADING_ALLOWED / COOLDOWN / HALTED from losing streaks and weekly/monthly drawdown), backtest-expert, manifoldbt-backtester.
- **For Kalpa:**
  - We already have the replay/bootstrap test, risk caps, paper-first and the 90-day rule.
  - Kalpa's own 60-day tests of 5-min opening-range breakout on Nifty 50 stocks lost money after costs (research/aggressive-5k-2026-11-13.md).
  - New task **A273**, the India "insider tracker": SEBI PIT insider disclosures + NSE bulk/block deals, then a "buy after insider buying" test through the gate (placebo + walk-forward) before any paper run.
  - No third-party code is copied or run without review and Akhil's OK (repo rule).

## Rules that still apply to anything from these videos
- Paper first, with 90 paper days.
- Live only with all of: LIVE_TRADING=YES, a GO file, a GATE_PASS file, and Akhil's "go".
- Martingale is banned.
- Every new idea is logged in `research/trials.csv`.

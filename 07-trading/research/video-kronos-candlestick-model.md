# Video: "Open Source Kronos AI: Candlestick Trading Model Tested in AI Agents" (David Arias, CFA)

Shared by Akhil, 13 Nov 2026: https://youtu.be/0Qv1W4qTWQ4
Frames/transcript: **not watched**. YouTube blocked the cloud download ("confirm you're not a bot"); title and author come from YouTube's oEmbed. Facts below come from Kronos's own repo, Hugging Face cards and paper, plus one independent test.

## What Kronos is (checked 13 Nov 2026)
- Open-source foundation model for candlesticks (OHLCV), from Tsinghua University; paper arXiv 2508.02739, accepted at AAAI 2026.
- Trained on 12B+ K-line records from 45 exchanges. Code: https://github.com/shiyu-coder/Kronos (MIT). Models on Hugging Face (NeoQuasar/*, MIT):
  - Kronos-mini 4.1M params (context 2048), Kronos-small 24.7M, Kronos-base 102.3M (context 512). Kronos-large 499M is **not** public.
- Simple API: `KronosPredictor(model, tokenizer, max_context=512).predict(...)` returns the next N candles; `predict_batch` for many symbols. Fine-tuning pipeline uses Microsoft Qlib.
- Licence check: MIT, OK to use in b7 with attribution (CLAUDE.md rule 3).

## Claims vs evidence
- Authors' own benchmark: RankIC +93% vs the best time-series foundation model, +87% vs the best non-pretrained model. Not independently verified.
- Independent test (Thorsten Meyer, May 2026, Kronos-small on 5-minute BTC, out of sample): no better than a Brownian-motion baseline (Brier 0.189 vs 0.188, not significant); log-loss about twice as bad (confident, wrong tails). He did not put it in his live bot.
- The authors call their backtest pipeline a demonstration, not a trading system.

## What it means for b7 (Akhil's own money, SEBI rules in CLAUDE.md)
- Worth testing, not trusting: add Kronos-small as one **signal candidate** in the existing backtest → paper-trade ladder, never straight to live money.
- Fits free infra: 24.7M params runs on CPU in GitHub Actions/Codespaces; nothing installed on Akhil's PC.
- Pass bar before any paper run: beats a naive baseline (random walk / buy-and-hold) on Nifty/Bank Nifty daily and 15-min data, out of sample, after costs and slippage, over 2+ years; Brier/log-loss reported, not just returns.
- Roadmap: A250 (lane A, trading).

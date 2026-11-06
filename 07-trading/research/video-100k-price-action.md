# Video notes: "Claude Tested 100,000 Price Action Strategies" (AI Pathways, 28 Oct 2026)

Shared by Akhil, 7 Nov 2026. https://youtu.be/z97PnFIPoFg (17 min). Read from the auto-translated transcript; on-screen prompts and charts were not visible. The video's claims are **unverified**, and the creator sells a paid community and 1:1 calls. No repos or tools are named in the transcript, so this note keeps the **method**.

## Their method (worth copying)
- Data: ~5 years of 1-minute bars, US index futures NQ and ES; ~300 million simulated trades.
- 100,000 rule variants: the rules "as taught" plus 40,000 random mixes in between.
- Real costs in every trade.
- Funnel: enough trades → profit after costs → Sharpe above 0.5. Only ~8% of variants passed (8,310 of 100k).
- **Last 2 years held back** and tested once at the end (out-of-sample).
- Each concept compared against **random lines** on the chart, so "works" means "better than chance".
- Built as 5 separate prompts/layers: 1 data + rules as settings, 2 engine with costs, 3 funnel, 4 final hold-out test, 5 dashboard.

## Their findings (unverified, US futures only)
1. Higher timeframes win: on 4-hour charts ~45% of variants profitable in the hold-out vs ~9% on 1-minute; costs ate ~40% of profit on 1-minute.
2. Win rate barely relates to profit (correlation 0.27).
3. Support/resistance beats random lines slightly; more touches did **not** make a level stronger.
4. "Flip zones" (old resistance becomes support) were the strongest level idea (~11 points better than random).
5. Waiting for a confirmation candle helped on NQ; a plain hard stop beat "close beyond stop"; waiting for a "sweep" lost money.
6. Only setup that survived the hold-out on both markets: **4-hour Change of Character**, enter on the candle close, stop beyond the last swing, target = 1× risk. Their read: a mean-reversion idea.
7. Only trading the New York session and skipping trades in the direction of the 3-day move both helped.

## What we take for b7 (Akhil's own money, NSE, paper first)
- Same 5-layer harness on **Nifty / Bank Nifty** data, with Indian costs (brokerage, STT, exchange fees, GST, stamp duty, slippage) and a 2-year hold-out, compared against random lines.
- Treat their "4h Change of Character" as a hypothesis to test on NSE, not a strategy to trade.
- Stop-loss and daily loss cap stay mandatory (CLAUDE.md rule 4). Nothing trades real money until backtest + paper runs pass.
- Roadmap: A168.

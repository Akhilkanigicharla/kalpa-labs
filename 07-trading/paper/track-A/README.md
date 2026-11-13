# Track A paper bot (Nifty ETF trend) · PAPER ONLY

Runs every weekday at 16:15 IST (`.github/workflows/paper-trade.yml`). Pretend money: ₹5,000.

- `summary-A.txt`: today's one-screen report (what it did, bot vs just holding NIFTYBEES, fall from peak, paper days /90).
- `worldcheck.txt`: World Check (global markets, US yields, rupee, oil, India VIX, Fed/RBI/Budget dates, Fed + RBI headlines). Alerts only.
- `ledger-A.csv`: one row per day. `state-A.json`: the bot's memory between days.
- **Stop buying from your phone:** in the git app, add an empty file `flags/KILL` and push. Delete it to resume.
- Rules (Akhil chose "Up to 100%", 13 Nov 2026): up to 100% in NIFTYBEES when the trend is up, liquid-ETF rate on idle cash,
  20% protective stop, new buys pause at a 20% fall from peak.
- Live money needs ALL of: 90 paper days, the gate passing (today: 5 of 6), a broker API + static IP, and Akhil's "go".
  Not investment advice.

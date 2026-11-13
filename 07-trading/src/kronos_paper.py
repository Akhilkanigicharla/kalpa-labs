"""Kronos daily signal for NIFTYBEES (PAPER ONLY). Akhil approved running Kronos, 13 Nov 2026.

Rule (fixed before testing): after the close, Kronos-small reads the last 400 daily Nifty 50
candles and predicts tomorrow's close (mean of 10 samples). Predicted above today's close ->
hold NIFTYBEES from the next open; otherwise the liquid ETF (4.7%/yr). Costs on every switch.

Out-of-sample test (Kronos weights were released 9 Sep 2025, so only data from 1 Aug 2025 on):
315 days to 12 Nov 2026: seed 0 +13.4% (worst -8.6%), seed 1 +12.8% (worst -5.6%) vs holding
Nifty +2.4% (worst -15.6%); fill at next open +17.2%; random signals beat it before costs in
1.8% of 5,000 tries; ahead of holding in both halves. Only ~1.3 years, one market family:
PAPER until 90 days and Akhil's go. Trades every ~3 days -> short-term tax applies.

Bookkeeping, no look-ahead: a decision made after day t's close is filled at day t+1's open
and earns open(t+1) -> open(t+2), which is booked on the run of day t+2.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

VENDOR = Path(__file__).resolve().parents[1] / "vendor" / "kronos"
MODEL = ("NeoQuasar/Kronos-small", "901c26c1332695a2a8f243eb2f37243a37bea320")
TOKENIZER = ("NeoQuasar/Kronos-Tokenizer-base", "0e0117387f39004a9016484a186a908917e22426")
LOOKBACK, SAMPLES = 400, 10
CASH_RATE = 0.047
SWITCH_COST = 0.0006          # per side of a switch (0.12% round trip, conservative for ETF delivery)
Predictor = Callable[[pd.DataFrame], float]


def kronos_predictor(seed: int = 0) -> Predictor:
    """Load the pinned Kronos model (needs torch). Returns f(last 400 daily bars) -> next close."""
    import torch
    sys.path.insert(0, str(VENDOR))
    from model import Kronos, KronosPredictor, KronosTokenizer  # vendored MIT code
    torch.manual_seed(seed)
    np.random.seed(seed)
    tok = KronosTokenizer.from_pretrained(TOKENIZER[0], revision=TOKENIZER[1])
    mdl = Kronos.from_pretrained(MODEL[0], revision=MODEL[1])
    p = KronosPredictor(mdl, tok, device="cpu", max_context=512)

    def f(bars: pd.DataFrame) -> float:
        x = bars.tail(LOOKBACK)
        nxt = pd.Series([x.index[-1] + pd.offsets.BDay(1)])
        out = p.predict(x.reset_index(drop=True), pd.Series(x.index), nxt, pred_len=1, T=1.0, top_p=0.9,
                        sample_count=SAMPLES, verbose=False)
        return float(out["close"].iloc[0])
    return f


def prepare(daily: pd.DataFrame) -> pd.DataFrame:
    df = daily.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].copy()
    idx = pd.DatetimeIndex(df.index)
    df.index = idx.tz_localize(None) if idx.tz is not None else idx
    df["volume"] = df["volume"].replace(0, np.nan).ffill().fillna(1.0)
    df["amount"] = df["volume"] * df["close"]
    return df.dropna()


def step(daily: pd.DataFrame, state_path: Path, predict: Predictor, capital: float = 5_000.0) -> dict:
    """One paper run after the close. Idempotent per bar date."""
    df = prepare(daily)
    if len(df) < LOOKBACK:
        raise ValueError(f"need {LOOKBACK} daily bars, got {len(df)}")
    st = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else \
        {"capital": capital, "equity": capital, "hold": capital, "decisions": [], "booked": []}
    today = df.index[-1]
    if st["decisions"] and st["decisions"][-1]["day"] == str(today.date()):
        return {**st, "skipped": True}
    opens = df["open"]
    # book every decision whose open(t+1) -> open(t+2) is now known
    for dec in st["decisions"]:
        if dec.get("booked"):
            continue
        t = pd.Timestamp(dec["day"])
        later = opens.index[opens.index > t]
        if len(later) < 2:
            continue
        o1, o2 = opens[later[0]], opens[later[1]]
        prev = st["decisions"][st["decisions"].index(dec) - 1]["long"] if st["decisions"].index(dec) > 0 else False
        r = (o2 / o1 - 1) if dec["long"] else (1 + CASH_RATE) ** (1 / 252) - 1
        r -= SWITCH_COST if dec["long"] != prev else 0.0
        st["equity"] *= 1 + r
        st["hold"] *= o2 / o1
        dec["booked"] = True
        st["booked"].append({"day": str(later[1].date()), "ret": r})
    pred = predict(df)
    close = float(df["close"].iloc[-1])
    st["decisions"].append({"day": str(today.date()), "close": close, "pred": pred, "long": bool(pred > close)})
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(st, indent=1), encoding="utf-8")
    return st


def summary(st: dict) -> str:
    d = st["decisions"][-1]
    cap = st["capital"]
    eq, hold = st["equity"], st["hold"]
    wins = sum(1 for b in st["booked"] if b["ret"] > 0)
    lines = [f"Kalpa b7 · Kronos daily signal · PAPER · {d['day']} · Rs {cap:,.0f}",
             f"Nifty close {d['close']:,.2f}, Kronos predicts {d['pred']:,.2f} ({d['pred'] / d['close'] - 1:+.2%}) -> "
             f"{'HOLD NIFTYBEES' if d['long'] else 'LIQUID ETF'} from tomorrow's open",
             f"Paper equity Rs {eq:,.2f} ({eq / cap - 1:+.2%}) vs holding NIFTYBEES Rs {hold:,.2f} ({hold / cap - 1:+.2%}); "
             f"booked days {len(st['booked'])}, up days {wins}",
             f"Paper days: {len(st['decisions'])}/90. Out-of-sample test: +13% vs +2% (Aug 2025-Nov 2026). Paper only. Not advice."]
    if st.get("skipped"):
        lines.insert(1, "Already done today (no new bar). No action.")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Kronos daily paper signal for NIFTYBEES")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--capital", type=float, default=5_000.0)
    a = ap.parse_args(argv)
    import yfinance as yf
    d = yf.Ticker("^NSEI").history(period="3y", auto_adjust=True)
    st = step(d, a.out / "state.json", kronos_predictor(0), a.capital)
    text = summary(st)
    (a.out / "summary.txt").write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

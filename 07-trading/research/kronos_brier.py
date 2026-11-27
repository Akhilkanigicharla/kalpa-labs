"""A250: Kronos-small probability test (Brier + log-loss vs random walk and base rate) + returns after costs.

Rules fixed BEFORE running (28 Nov 2026):
- Model: pinned Kronos-small + tokenizer (same revisions as src/kronos_paper.py), vendored MIT code.
- Out of sample only: weights released 9 Sep 2025, so test bars start 1 Aug 2025 (daily) or the last
  60 days yfinance allows (15-min, all after the release).
- Lookback 400 bars. K independent samples per bar (sample_count=1 each, T=1.0, top_p=0.9), seed 0.
- P(up) = (samples above today's close + 0.5) / (K + 1). Target: next bar's close > this close.
- Money rule: long when P(up) > 0.5, else cash; filled at the next open, earns open(t+1) -> open(t+2);
  0.06% per side on every switch (daily cash 4.7%/yr; intraday cash 0).
- Pass bar: lower Brier AND log-loss than both baselines AND more money than holding after costs.
Run: python -m research.kronos_brier --symbol ^NSEI --interval 1d   (from 07-trading/)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from src import kronos_score as ks
from src.kronos_paper import MODEL, TOKENIZER, VENDOR, prepare

LOOKBACK, COST_SIDE = 400, 0.0006
ROOT = Path(__file__).resolve().parents[1]


def load(symbol: str, interval: str) -> pd.DataFrame:
    import yfinance as yf
    t = yf.Ticker(symbol)
    d = t.history(start="2023-06-01", auto_adjust=True) if interval == "1d" else \
        t.history(period="60d", interval=interval, auto_adjust=True)
    if d.empty:
        raise SystemExit(f"no data for {symbol} {interval}")
    return prepare(d)


def sampler(seed: int = 0):
    import torch
    sys.path.insert(0, str(VENDOR))
    from model import Kronos, KronosPredictor, KronosTokenizer
    torch.manual_seed(seed)
    np.random.seed(seed)
    tok = KronosTokenizer.from_pretrained(TOKENIZER[0], revision=TOKENIZER[1])
    mdl = Kronos.from_pretrained(MODEL[0], revision=MODEL[1])
    return KronosPredictor(mdl, tok, device="cpu", max_context=512)


def run(df: pd.DataFrame, test_idx: list[int], k: int, pred, batch: int = 64) -> pd.DataFrame:
    """Return one row per test bar: p_up, up, ret. Each bar's window is repeated k times."""
    jobs = [i for i in test_idx for _ in range(k)]
    closes = {i: [] for i in test_idx}
    t0 = time.time()
    for s in range(0, len(jobs), batch):
        chunk = jobs[s:s + batch]
        xs = [df.iloc[i - LOOKBACK + 1:i + 1].reset_index(drop=True) for i in chunk]
        xt = [pd.Series(df.index[i - LOOKBACK + 1:i + 1]) for i in chunk]
        yt = [pd.Series([df.index[i + 1]]) for i in chunk]
        out = pred.predict_batch(xs, xt, yt, pred_len=1, T=1.0, top_p=0.9, sample_count=1, verbose=False)
        for i, o in zip(chunk, out):
            closes[i].append(float(o["close"].iloc[0]))
        if s == 0:
            print(f"  first batch {time.time() - t0:.1f}s, {len(jobs)} samples to go", flush=True)
    c, o = df["close"].to_numpy(), df["open"].to_numpy()
    rows = []
    for i in test_idx:
        ret = o[i + 2] / o[i + 1] - 1 if i + 2 < len(df) else np.nan
        rows.append({"time": df.index[i], "close": c[i], "p_up": ks.prob_up(np.array(closes[i]), c[i]),
                     "up": float(c[i + 1] > c[i]), "ret": ret})
    print(f"  done in {time.time() - t0:.0f}s", flush=True)
    return pd.DataFrame(rows).set_index("time")


def main(argv=None) -> int:
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--interval", default="1d", choices=["1d", "15m"])
    ap.add_argument("--samples", type=int, default=20)
    ap.add_argument("--out", type=Path, default=ROOT / "research" / "kronos_brier")
    a = ap.parse_args(argv)
    df = load(a.symbol, a.interval)
    if a.interval == "1d":
        test = [i for i, t in enumerate(df.index) if t >= pd.Timestamp("2025-08-01") and i >= LOOKBACK and i < len(df) - 1]
        cash = (1.047) ** (1 / 252) - 1
    else:
        test = list(range(LOOKBACK, len(df) - 1))
        cash = 0.0
    if not test:
        raise SystemExit("no test bars")
    up = (df["close"].shift(-1) > df["close"]).astype(float)
    base = float(up.iloc[:test[0]].mean())
    print(f"{a.symbol} {a.interval}: {len(test)} test bars {df.index[test[0]]} -> {df.index[test[-1]]}, base rate {base:.3f}")
    preds = run(df, test, a.samples, sampler(0))
    a.out.mkdir(parents=True, exist_ok=True)
    tag = f"{a.symbol.strip('^').lower()}_{a.interval}"
    preds.to_csv(a.out / f"{tag}.csv", float_format="%.6g")
    p, y, r = ks.frame_from(preds)
    rep = ks.report(f"{a.symbol} {a.interval}", p, y, r, base, COST_SIDE, cash)
    rep.update({"from": str(df.index[test[0]]), "to": str(df.index[test[-1]]), "samples": a.samples})
    (a.out / f"{tag}.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    print(json.dumps({k: rep[k] for k in ("brier", "log_loss", "return_after_costs", "return_hold", "passes")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

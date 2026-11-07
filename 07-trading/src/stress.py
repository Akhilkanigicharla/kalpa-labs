"""A168: honest stress test for trading ideas from Akhil's videos (paper only).

Method (copied from the "100,000 strategies" video, made stricter for NSE):
  variants of a rule  ->  enough trades  ->  profit after Indian costs  ->  Sharpe > 0.5  (train)
  -> the last 2 years are held back and looked at ONCE  (hold-out)
  -> every idea is compared with random switching that trades just as often  ("better than chance?")
  -> PBO (probability of backtest overfitting) and DSR across all variants tried.

First idea tested: a regime rotation between NIFTYBEES and GOLDBEES (3rd video's core idea,
Indian version): hold the index ETF while it is in an uptrend and calm, otherwise hold gold.
Intraday ideas (4-hour Change of Character, session bias, sweep-then-reclaim) need years of
intraday bars that no free source gives; see A168 notes.
Research code only. Not advice; paper trading only.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from . import costs, metrics
from .strategies import regime_filter

ANN = 252


@dataclass
class PairResult:
    returns: pd.Series
    gross: pd.Series
    held: pd.Series      # weight in asset A (the rest is in asset B)
    cost: pd.Series
    trades: int

    @property
    def total_cost(self) -> float:
        return float(self.cost.sum())


def run_pair(close_a: pd.Series, close_b: pd.Series, weight_a: pd.Series, *, delay: int = 1,
             cost_mult: float = 1.0, capital: float = 100_000.0) -> PairResult:
    """Fully invested in A and/or B. A switch sells one and buys the other (both legs charged)."""
    if delay < 1:
        raise ValueError("delay must be >= 1 (delay 0 would look ahead)")
    if cost_mult <= 0:
        raise ValueError("zero-cost runs are not allowed")
    idx = close_a.index.intersection(close_b.index)
    a, b = close_a.reindex(idx), close_b.reindex(idx)
    w = weight_a.reindex(idx).fillna(0.0).clip(0.0, 1.0)
    held = w.shift(delay).fillna(w.iloc[0])  # start in the first target mix (day-0 return is 0, no look-ahead)
    ra, rb = a.pct_change().fillna(0.0), b.pct_change().fillna(0.0)
    gross = held * ra + (1 - held) * rb
    change = (held.shift(-1).fillna(held.iloc[-1]) - held).abs()
    first = pd.Series(0.0, index=idx); first.iloc[0] = 1.0           # initial buy of the starting mix
    buy_side, sell_side = costs.delivery_side_rates()
    dp = costs.rate("dp_per_scrip_sell") / capital
    cost = cost_mult * ((buy_side + sell_side) * change + dp * (change > 1e-9) + buy_side * first)
    trades = int((change > 0.01).sum())
    return PairResult(gross - cost, gross, held, cost, trades)


regime = regime_filter  # one definition, shared with the paper bot (parity)


GRID = [{"trend": t, "vol_cap": v} for t in (50, 100, 150, 200, 250) for v in (None, 0.15, 0.20, 0.25)]


def _sharpe(r: pd.Series) -> float:
    return float(metrics.sharpe(r))


def random_switch_sharpes(close_a, close_b, n_switches: int, draws: int, seed: int = 0) -> np.ndarray:
    """Sharpe of random A/B switching with the same number of switches (the 'chance' baseline)."""
    rng = np.random.default_rng(seed)
    idx = close_a.index.intersection(close_b.index)
    n, out = len(idx), []
    k = max(1, n_switches)
    for _ in range(draws):
        cuts = np.sort(rng.choice(np.arange(1, n), size=min(k, n - 1), replace=False))
        w = np.zeros(n); state = float(rng.integers(0, 2)); last = 0
        for c in list(cuts) + [n]:
            w[last:c] = state; state = 1 - state; last = c
        out.append(_sharpe(run_pair(close_a, close_b, pd.Series(w, index=idx)).returns))
    return np.array(out)


def funnel(close_a: pd.Series, close_b: pd.Series, *, holdout_years: int = 2, min_trades: int = 6,
           min_sharpe: float = 0.5, random_draws: int = 300, grid: list[dict] | None = None) -> dict:
    grid = grid or GRID
    idx = close_a.index.intersection(close_b.index)
    a, b = close_a.reindex(idx), close_b.reindex(idx)
    h = holdout_years * ANN
    if len(idx) <= h + 300:
        raise ValueError("not enough history for a hold-out")
    train_end, holdout_start = idx[-h - 1], idx[-h]
    rows, train_returns = [], {}
    for g in grid:
        w = regime(a, **g)                                    # signals from the full series (past-only)
        res = run_pair(a, b, w)
        tr, ho = res.returns.loc[:train_end], res.returns.loc[holdout_start:]
        trades_train = int((res.held.loc[:train_end].diff().abs() > 0.01).sum())
        key = f"trend={g['trend']},vol_cap={g['vol_cap']}"
        train_returns[key] = tr
        rows.append({"variant": key, "trades": trades_train, "train_total": float((1 + tr).prod() - 1),
                     "train_sharpe": _sharpe(tr), "holdout_total": float((1 + ho).prod() - 1),
                     "holdout_sharpe": _sharpe(ho), "switches_all": res.trades})
    df = pd.DataFrame(rows)
    enough = df[df.trades >= min_trades]
    prof = enough[enough.train_total > 0]
    ok = prof[prof.train_sharpe > min_sharpe]
    best = (ok if len(ok) else df).sort_values("train_sharpe", ascending=False).iloc[0]
    rand = random_switch_sharpes(a.loc[:train_end], b.loc[:train_end], int(best.trades), random_draws)
    matrix = pd.DataFrame(train_returns)
    bh_a = run_pair(a, b, pd.Series(1.0, index=idx)).returns
    return {
        "stages": {"variants": len(df), "enough_trades": len(enough), "profitable": len(prof), "sharpe_ok": len(ok)},
        "survivors_profitable_in_holdout": int((ok.holdout_total > 0).sum()),
        "best": best.to_dict(),
        "best_vs_random_pct": float((rand < best.train_sharpe).mean() * 100),
        "pbo": float(metrics.pbo_cscv(matrix)),
        "dsr_best": float(metrics.dsr(train_returns[best.variant], n_trials=len(df))),
        "n_trials": len(df),
        "train_end": train_end, "holdout_start": holdout_start,
        "buy_hold_a_holdout_total": float((1 + bh_a.loc[holdout_start:]).prod() - 1),
        "table": df,
    }


def _jumps(close: pd.Series, limit: float = 0.25) -> list[str]:
    """One-day moves above `limit`: an ETF almost never does this, so it is a data error (unadjusted split)."""
    r = close.pct_change().dropna()
    return [f"{d:%d %b %Y} {v:+.0%}" for d, v in r[r.abs() > limit].items()]


def verdict(rep: dict) -> tuple[bool, list[str]]:
    """PASS only if every gate holds; returns the failed gates in plain words."""
    best, fails = rep["best"], []
    if rep.get("data_problems") or any(rep.get("jumps", {}).values()):
        fails.append("DATA PROBLEM: results not trusted until the price series is fixed")
    if best["train_sharpe"] <= 0.5: fails.append("train Sharpe not above 0.5")
    if best["holdout_total"] <= 0: fails.append("lost money in the hold-out")
    if rep["best_vs_random_pct"] < 95: fails.append("not better than 95% of random")
    if rep["pbo"] >= 0.5: fails.append("PBO 0.5 or more (likely overfit)")
    if rep["dsr_best"] <= 0.95: fails.append("Deflated Sharpe not above 0.95")
    return (not fails), fails


def report_md(rep: dict, a: str, b: str, source: str) -> str:
    s, best = rep["stages"], rep["best"]
    ok, fails = verdict(rep)
    lines = [
        f"# Stress test: {a} ⇄ {b} regime rotation ({date.today():%d %b %Y})",
        "",
        f"Paper only. Not advice. Data: {source}. Indian delivery costs (STT, stamp, exchange, GST, DP) on every switch.",
        "",
        "## Funnel (train period)",
        f"- Variants tried: **{s['variants']}** → enough trades: **{s['enough_trades']}** → profitable after costs: "
        f"**{s['profitable']}** → Sharpe > 0.5: **{s['sharpe_ok']}**",
        f"- Train ends {rep['train_end']:%d %b %Y}; hold-out starts {rep['holdout_start']:%d %b %Y} (looked at once).",
        "",
        "## Best variant",
        f"- {best['variant']}: train Sharpe {best['train_sharpe']:.2f}, train return {best['train_total']:+.0%}, "
        f"hold-out return {best['holdout_total']:+.0%} (buy-and-hold {a}: {rep['buy_hold_a_holdout_total']:+.0%}).",
        f"- Better than **{rep['best_vs_random_pct']:.0f}%** of random switching with the same number of trades.",
        f"- Survivors still profitable in the hold-out: **{rep['survivors_profitable_in_holdout']} of {s['sharpe_ok']}**.",
        f"- PBO (chance the best in-sample pick is overfit): **{rep['pbo']:.2f}**; Deflated Sharpe of best: **{rep['dsr_best']:.2f}**.",
        "",
        "## Data checks",
        *([f"- ⚠ {p}" for p in rep.get("data_problems", [])] + [f"- ⚠ {k}: one-day move {j}" for k, js in rep.get("jumps", {}).items() for j in js]
          or ["- Clean: no gaps, no impossible prices, no one-day jumps above 25%."]),
        "",
        "## Verdict",
        ("**PASS**: goes to 90 days of paper trading." if ok else "**FAIL**: " + "; ".join(fails) + ". Not traded, not even on paper."),
        "",
        "## Verdict rule",
        "Moves to paper trading only if: Sharpe > 0.5 in train, profitable in the hold-out, better than 95% of random, "
        "PBO < 0.5 and DSR > 0.95. Real money needs 90 days of paper results and Akhil's decision.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="A168 stress test (paper only)")
    p.add_argument("--a", default="NIFTYBEES"); p.add_argument("--b", default="GOLDBEES")
    p.add_argument("--out", default="reports"); p.add_argument("--synthetic", action="store_true")
    args = p.parse_args(argv)
    if args.synthetic:
        from . import data
        a = data.synthetic_prices(3000, seed=1, regime_days=120, regime_drift=0.3)["close"]
        b = data.synthetic_prices(3000, seed=2, mu=0.07, sigma=0.12)["close"]
        source = "synthetic (test run)"
    else:
        from . import data
        # yfinance returns only ~1 month when no start is given, so always ask for the full history
        da = data.get_daily(args.a, start="2006-01-01", refresh=True, strict=False)
        db = data.get_daily(args.b, start="2006-01-01", refresh=True, strict=False)
        problems = [f"{args.a}: {p}" for p in data.validate(da)] + [f"{args.b}: {p}" for p in data.validate(db)]
        jumps = {args.a: _jumps(da["close"]), args.b: _jumps(db["close"])}
        a, b = da["close"], db["close"]
        both = a.index.intersection(b.index)
        source = (f"Yahoo Finance daily bars via yfinance ({args.a}.NS, {args.b}.NS), "
                  f"{both[0]:%d %b %Y} to {both[-1]:%d %b %Y}, {len(both)} common trading days")
    rep = funnel(a, b)
    if not args.synthetic:
        rep["data_problems"], rep["jumps"] = problems, jumps
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    path = out / f"stress-{args.a}-{args.b}-{date.today():%Y-%m-%d}.md"
    path.write_text(report_md(rep, args.a, args.b, source), encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

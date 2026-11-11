"""Darwinian ensemble across the lab's strategies. PAPER ONLY. Research code, not advice.

Method credit: chrisworsey55/atlas-gic (MIT licence), "Darwinian weights" in
architecture/autoresearch.md. Re-implemented here from the written description; no code
copied. Their rule, used unchanged:
  * every member starts at weight 1.0, clamped to [0.3, 2.5];
  * each update, the top quartile by score gets weight x 1.05, the bottom quartile x 0.95;
  * the decision layer combines member inputs as sum(w_i * x_i) / sum(w_i).

Kalpa changes:
  * Score = rolling out-of-sample Sharpe of each member's net daily returns (after Indian
    delivery costs, from backtest.run). The score used at bar t only sees returns up to
    bar t-1, so a new bar can never change an earlier weight (no look-ahead).
  * Only strategies whose gate.py verdict is "paper" are eligible. A failed or missing
    gate verdict means weight 0, always.
  * Combined target = weighted average of member target weights (each in [0, 1]), so it
    stays long-only, no leverage, in [0, 1].
  * run_paper_ensemble() sends that target through the existing live runner, which means
    sizing caps -> Live Guard -> FakeBroker. There is no live path in this module.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd

from . import backtest, strategies, trials
from .metrics import ANN

W_MIN, W_MAX, W_START = 0.3, 2.5, 1.0
UP, DOWN = 1.05, 0.95
DEFAULT_WINDOW = 126          # ~6 months of daily bars for the rolling Sharpe
NAME = "ensemble"


# ---------------------------------------------------------------- eligibility
def _verdict_str(v) -> str:
    return str(getattr(v, "verdict", v) or "").strip().lower()


def eligible(members, verdicts: Mapping[str, object]) -> list[str]:
    """Members whose gate verdict is 'paper'. Accepts gate.Verdict objects or plain strings."""
    return [m for m in members if _verdict_str(verdicts.get(m)) == "paper"]


def verdicts_from_trials(path: Path | None = None) -> dict[str, str]:
    """Latest recorded gate verdict per strategy from research/trials.csv (blank = not run)."""
    out: dict[str, str] = {}
    for r in trials._read(path or trials.REGISTRY):
        if r.get("verdict"):
            out[r["strategy"]] = r["verdict"]
    return out


# ---------------------------------------------------------------- Darwinian rule
def darwin_step(weights: Mapping[str, float], scores: Mapping[str, float]) -> dict[str, float]:
    """One atlas-gic update. Members with no finite score keep their weight.

    With n scored members, k = max(1, n // 4) go up and k go down. Needs n >= 2;
    a lone member has nobody to be compared with and stays where it is.
    """
    new = {m: float(min(max(w, W_MIN), W_MAX)) for m, w in weights.items()}
    scored = sorted((m for m in new if m in scores and np.isfinite(scores[m])), key=lambda m: (scores[m], m))
    n = len(scored)
    if n < 2 or scores[scored[0]] == scores[scored[-1]]:
        return new
    k = max(1, n // 4)
    for m in scored[:k]:
        new[m] = max(W_MIN, new[m] * DOWN)
    for m in scored[-k:]:
        new[m] = min(W_MAX, new[m] * UP)
    return new


def combine(targets: Mapping[str, float], weights: Mapping[str, float]) -> float:
    """sum(w_i * x_i) / sum(w_i) over members with weight > 0; 0.0 (cash) if none."""
    num = den = 0.0
    for m, w in weights.items():
        if w > 0 and m in targets and np.isfinite(targets[m]):
            num += w * min(max(float(targets[m]), 0.0), 1.0)
            den += w
    return num / den if den > 0 else 0.0


# ---------------------------------------------------------------- series
def member_frames(close: pd.Series, members, params: Mapping[str, dict] | None = None):
    """(targets, net_returns) DataFrames, one column per member."""
    params = params or {}
    tgt, ret = {}, {}
    for m in members:
        w = strategies.weights(m, close, **params.get(m, {}))
        tgt[m] = w.reindex(close.index).fillna(0.0).clip(0.0, 1.0)
        ret[m] = backtest.run(close, tgt[m]).returns
    return pd.DataFrame(tgt, index=close.index), pd.DataFrame(ret, index=close.index)


def rolling_sharpe(returns: pd.DataFrame, window: int = DEFAULT_WINDOW) -> pd.DataFrame:
    """Score usable at bar t = annualised Sharpe of returns over the `window` bars ending t-1.

    The shift(1) matters: backtest.run books the cost of a trade on the bar before the
    position changes, and on the series' last bar it cannot know that yet. Using only
    bars up to t-1 keeps every score fixed once printed.
    """
    past = returns.shift(1)
    mu = past.rolling(window, min_periods=window).mean()
    sd = past.rolling(window, min_periods=window).std(ddof=1)
    return (mu / sd.where(sd > 0)) * np.sqrt(ANN)


def ensemble_path(close: pd.Series, members, verdicts: Mapping[str, object], *,
                  params: Mapping[str, dict] | None = None, window: int = DEFAULT_WINDOW,
                  update_every: int = 1) -> tuple[pd.DataFrame, pd.Series]:
    """Darwinian weights per bar (failed-gate members are 0) and the combined target series."""
    members = list(members)
    ok = eligible(members, verdicts)
    w_hist = pd.DataFrame(0.0, index=close.index, columns=members)
    if not ok:
        return w_hist, pd.Series(0.0, index=close.index)
    targets, rets = member_frames(close, ok, params)
    scores = rolling_sharpe(rets, window)
    w = {m: W_START for m in ok}
    combined = np.zeros(len(close))
    for i, ts in enumerate(close.index):
        if i % max(1, update_every) == 0:
            w = darwin_step(w, scores.iloc[i].to_dict())
        for m in ok:
            w_hist.iat[i, members.index(m)] = w[m]
        combined[i] = combine(targets.iloc[i].to_dict(), w)
    return w_hist, pd.Series(combined, index=close.index)


def ensemble_weights(close: pd.Series, *, members=(), verdicts=None, params=None,
                     window: int = DEFAULT_WINDOW, update_every: int = 1) -> pd.Series:
    """Strategy-shaped function (close -> target weight in [0, 1]) for the live runner."""
    return ensemble_path(close, members, verdicts or {}, params=params, window=window,
                         update_every=update_every)[1]


# ---------------------------------------------------------------- paper run through Live Guard
@contextmanager
def _registered():
    """Expose the ensemble to strategies.weights() for one call, then remove it again."""
    had = NAME in strategies.REGISTRY
    strategies.REGISTRY[NAME] = (ensemble_weights, {})
    try:
        yield
    finally:
        if not had:
            strategies.REGISTRY.pop(NAME, None)


def run_paper_ensemble(bars: pd.DataFrame, *, track: str, members, verdicts: Mapping[str, object],
                       capital: float, out: Path, flags: Path, asof=None,
                       params: Mapping[str, dict] | None = None, window: int = DEFAULT_WINDOW,
                       update_every: int = 1, **kw) -> dict:
    """Paper-only: combined target -> live.runner.run_paper (risk sizing -> Live Guard -> FakeBroker)."""
    if str(kw.pop("mode", "paper")).lower() != "paper":
        raise ValueError("ensemble is paper only")
    from .live import runner
    p = {"members": tuple(members), "verdicts": dict(verdicts), "params": dict(params or {}),
         "window": window, "update_every": update_every}
    with _registered():
        return runner.run_paper(bars, track=track, strategy=NAME, capital=capital, out=out, flags=flags,
                                asof=asof, params=p, **kw)

"""A247: no-repaint and no-look-ahead checks for a strategy's weights (paper only).

From the DaviddTech validation checklist (research/videos-2026-11-13.md), checked on the web
28 Nov 2026:
- Repaint = a signal on a closed bar changes when more bars arrive. The "truncation test":
  run the rule on data ending at bar N, run it again with more data, and bar N must not change
  (abctradinggroup.com "Repainting Explained"; LuxAlgo "Repaint-safe Engineering": a signal,
  once emitted, is permanent).
- Look-ahead = the rule reads information that did not exist at decision time. Here: scramble
  every bar AFTER bar N; the weights up to bar N must not move (LuxAlgo "Bias Taxonomy";
  joor0x "Look-ahead traps"). Fills after the signal are enforced separately by delay >= 1 in
  backtest.run and gate.walk_forward.
Both checks compare the whole prefix, not just its last bar, so centred windows, shift(-k),
pivots drawn into the past and full-history normalisation are all caught.
Research code, paper only, not advice.
"""
from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

TOL = 1e-9


def _cuts(n: int, checkpoints: int) -> list[int]:
    lo = max(2, n // 10)
    return sorted(set(np.linspace(lo, n - 2, checkpoints).astype(int).tolist())) if n > lo + 2 else []


def _w(fn: Callable[[pd.Series], pd.Series], close: pd.Series) -> np.ndarray:
    return fn(close).reindex(close.index).fillna(0.0).to_numpy(dtype=float)


def repaint_bars(fn: Callable[[pd.Series], pd.Series], close: pd.Series, *,
                 checkpoints: int = 8) -> list[pd.Timestamp]:
    """Cut dates where the weights on already-closed bars differ from the full-history run."""
    full = _w(fn, close)
    bad = []
    for t in _cuts(len(close), checkpoints):
        part = _w(fn, close.iloc[:t + 1])
        if np.abs(part - full[:t + 1]).max() > TOL:
            bad.append(close.index[t])
    return bad


def lookahead_bars(fn: Callable[[pd.Series], pd.Series], close: pd.Series, *,
                   checkpoints: int = 8, seed: int = 0) -> list[pd.Timestamp]:
    """Cut dates where changing only FUTURE bars moved a weight on or before the cut."""
    rng = np.random.default_rng(seed)
    full = _w(fn, close)
    bad = []
    for t in _cuts(len(close), checkpoints):
        alt = close.copy()
        alt.iloc[t + 1:] = alt.iloc[t + 1:].to_numpy() * rng.uniform(0.5, 1.5, len(close) - t - 1)
        if np.abs(_w(fn, alt)[:t + 1] - full[:t + 1]).max() > TOL:
            bad.append(close.index[t])
    return bad


def check_strategy(strategy: str, close: pd.Series, grid: list[dict] | None = None, *,
                   checkpoints: int = 8) -> dict:
    """Run both checks on every config of a registered strategy. ok=True only if all are clean."""
    from .strategies import param_grid, weights
    out = {"repaint": {}, "lookahead": {}}
    for p in grid or param_grid(strategy) or [{}]:
        fn = lambda c, p=p: weights(strategy, c, **p)  # noqa: E731
        key = ",".join(f"{k}={v}" for k, v in p.items()) or "default"
        if r := repaint_bars(fn, close, checkpoints=checkpoints):
            out["repaint"][key] = [d.date().isoformat() for d in r]
        if la := lookahead_bars(fn, close, checkpoints=checkpoints):
            out["lookahead"][key] = [d.date().isoformat() for d in la]
    out["ok"] = not out["repaint"] and not out["lookahead"]
    return out

"""Strategy rules: each returns a target weight series in [0, 1] (long-only, no leverage).

The weight at date t uses only data up to and including the close of t. The
backtester applies it from the next bar, so nothing here may look ahead.

Chosen from research/deep-scan-v2.md (strongest published evidence that fits NSE
delivery, daily bars, low turnover):
  1. tsmom      time-series momentum (Moskowitz, Ooi & Pedersen 2012)
  2. ma_filter  long moving-average trend filter (Faber 2007)
  3. *_vt       volatility-targeting overlay (Moreira & Muir 2017; Harvey et al. 2018)
  4. sma_cross  the a8 fast/slow SMA crossover, kept as the NEGATIVE CONTROL that the
                gate must reject on data without a planted trend.
Research code only. Not advice; paper trading only.
"""
from __future__ import annotations

from itertools import product
from typing import Callable

import numpy as np
import pandas as pd

Strategy = Callable[..., pd.Series]


def tsmom(close: pd.Series, lookback: int = 252) -> pd.Series:
    """1 when the trailing `lookback`-day return is positive, else 0 (cash)."""
    past = close / close.shift(lookback) - 1
    return (past > 0).astype(float).where(past.notna(), 0.0)


def ma_filter(close: pd.Series, window: int = 200) -> pd.Series:
    sma = close.rolling(window).mean()
    return (close > sma).astype(float).where(sma.notna(), 0.0)


def sma_cross(close: pd.Series, fast: int = 10, slow: int = 50) -> pd.Series:
    f, s = close.rolling(fast).mean(), close.rolling(slow).mean()
    return (f > s).astype(float).where(s.notna(), 0.0)


def vol_target(weight: pd.Series, close: pd.Series, target: float = 0.12,
               window: int = 20, band: float = 0.10) -> pd.Series:
    """Scale `weight` by target / realised vol (capped at 1) with a no-trade band.

    The band stops tiny daily rebalances that STT would eat.
    """
    rv = close.pct_change().rolling(window).std() * np.sqrt(252)
    raw = (weight * (target / rv).clip(upper=1.0)).fillna(0.0).to_numpy()
    out = np.zeros_like(raw)
    cur = 0.0
    for i, w in enumerate(raw):
        if w == 0.0 or abs(w - cur) > band:
            cur = w
        out[i] = cur
    return pd.Series(out, index=weight.index)


def tsmom_vt(close: pd.Series, lookback: int = 252, target: float = 0.12) -> pd.Series:
    return vol_target(tsmom(close, lookback), close, target)


def ma_filter_vt(close: pd.Series, window: int = 200, target: float = 0.12) -> pd.Series:
    return vol_target(ma_filter(close, window), close, target)


# Every grid has an even number (>= 4) of configs: with an odd N the median OOS rank
# gives logit 0 and biases PBO upward (N=3 -> chance PBO of 2/3 instead of 1/2).
REGISTRY: dict[str, tuple[Strategy, dict[str, list]]] = {
    "tsmom":        (tsmom,        {"lookback": [63, 126, 189, 252]}),
    "ma_filter":    (ma_filter,    {"window": [50, 100, 150, 200]}),
    "tsmom_vt":     (tsmom_vt,     {"lookback": [126, 252], "target": [0.10, 0.15]}),
    "ma_filter_vt": (ma_filter_vt, {"window": [150, 200], "target": [0.10, 0.15]}),
    "sma_cross":    (sma_cross,    {"fast": [5, 10, 20], "slow": [50, 100]}),
}


def param_grid(name: str) -> list[dict]:
    _, grid = REGISTRY[name]
    keys = list(grid)
    return [dict(zip(keys, vals)) for vals in product(*(grid[k] for k in keys))]


def weights(name: str, close: pd.Series, **params) -> pd.Series:
    fn, _ = REGISTRY[name]
    return fn(close, **params)

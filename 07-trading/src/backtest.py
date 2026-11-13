"""Vectorised long-only backtester with Indian delivery costs.

Timing: the weight decided at the close of day t is held from the close of day
t + delay - 1. delay=1 means "fill at the signal day's close" (the usual
convention); delay=2 adds the one-bar fill delay the gate's stress test needs.
Returns are close-to-close. Costs come from src/costs.py and are charged on the
day the position changes.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import costs


@dataclass
class Result:
    returns: pd.Series      # daily net returns (fraction of capital)
    gross: pd.Series        # daily gross returns
    held: pd.Series         # weight held each day
    cost: pd.Series         # daily cost (fraction of capital)
    trades: int             # position changes > 1% of capital (a round trip = 2)

    @property
    def total_cost(self) -> float:
        return float(self.cost.sum())


def run(close: pd.Series, weight: pd.Series, *, delay: int = 1, cost_mult: float = 1.0,
        capital: float = 100_000.0, cash_rate: float = 0.0) -> Result:
    """cash_rate: yearly return earned on the part NOT in the market (e.g. a liquid ETF such as
    LIQUIDBEES, 4.69%/yr since 2003 after its 0.69% fee, anandrathi.com 1 Jun 2025). Default 0
    keeps the gate's numbers unchanged; switching between equity and liquid ETF costs are
    charged on the equity leg only (liquid ETF brokerage is ignored: tiny, flagged in notes)."""
    if delay < 1:
        raise ValueError("delay must be >= 1 (delay 0 would look ahead)")
    if cost_mult <= 0:
        raise ValueError("zero-cost runs are not allowed")
    w = weight.reindex(close.index).fillna(0.0).clip(0.0, 1.0)
    held = w.shift(delay).fillna(0.0)
    r = close.pct_change().fillna(0.0)
    if not 0.0 <= cash_rate < 0.25:
        raise ValueError("cash_rate must be a yearly fraction between 0 and 0.25")
    gross = held * r + (1.0 - held) * ((1.0 + cash_rate) ** (1 / 252) - 1.0)
    # The position actually changes on the day before it first earns a return.
    change = held.shift(-1).fillna(held.iloc[-1]) - held
    buy, sell = change.clip(lower=0), (-change).clip(lower=0)
    b, s = costs.delivery_side_rates()
    dp = costs.rate("dp_per_scrip_sell") / capital
    cost = cost_mult * (b * buy + s * sell + dp * (sell > 1e-9))
    net = gross - cost
    trades = int((change.abs() > 0.01).sum())
    return Result(net, gross, held, cost, trades)


def buy_and_hold(close: pd.Series, capital: float = 100_000.0) -> Result:
    w = pd.Series(1.0, index=close.index)
    return run(close, w, capital=capital)


def config_matrix(close: pd.Series, strategy: str, *, delay: int = 1, cash_rate: float = 0.0,
                  cost_mult: float = 1.0) -> tuple[pd.DataFrame, list[dict]]:
    """Net daily returns for every config in the strategy's grid (columns = configs)."""
    from .strategies import param_grid, weights
    grid = param_grid(strategy)
    cols = {}
    for i, p in enumerate(grid):
        cols[i] = run(close, weights(strategy, close, **p), delay=delay, cost_mult=cost_mult, cash_rate=cash_rate).returns
    return pd.DataFrame(cols), grid


def equity(returns: pd.Series) -> pd.Series:
    return (1 + returns).cumprod()


def max_drawdown(returns: pd.Series) -> float:
    eq = equity(returns)
    return float((eq / eq.cummax() - 1).min())


def cagr(returns: pd.Series) -> float:
    eq = equity(returns)
    years = len(returns) / 252
    return float(eq.iloc[-1] ** (1 / years) - 1) if years > 0 and eq.iloc[-1] > 0 else float("nan")


__all__ = ["Result", "run", "buy_and_hold", "config_matrix", "equity", "max_drawdown", "cagr", "np"]

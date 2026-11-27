"""A250: score Kronos as a probability forecaster, not just a direction guesser.

Kronos samples K possible next candles. P(up) = share of samples whose close is above today's close.
We score P(up) with Brier and log-loss against two baselines that need no model:
  * random walk: P(up) = 0.5 every bar
  * base rate:  P(up) = share of up bars BEFORE the test window (no look-ahead)
Lower is better for both scores. A model with no skill lands at or above the baselines.
Pure numpy/pandas so it is tested without torch.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

EPS = 1e-3  # clip so one confident miss cannot make log-loss infinite (and is still punished hard)


def prob_up(samples: np.ndarray, close: float) -> float:
    """Share of sampled next closes above today's close, smoothed (k+0.5)/(n+1) so it is never 0 or 1."""
    s = np.asarray(samples, dtype=float)
    s = s[np.isfinite(s)]
    if s.size == 0:
        raise ValueError("no finite samples")
    return float((np.sum(s > close) + 0.5) / (s.size + 1))


def brier(p: np.ndarray, y: np.ndarray) -> float:
    p, y = _check(p, y)
    return float(np.mean((p - y) ** 2))


def log_loss(p: np.ndarray, y: np.ndarray) -> float:
    p, y = _check(p, y)
    p = np.clip(p, EPS, 1 - EPS)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def _check(p, y):
    p, y = np.asarray(p, dtype=float), np.asarray(y, dtype=float)
    if p.shape != y.shape or p.size == 0:
        raise ValueError("p and y must be non-empty and the same length")
    if np.any((p < 0) | (p > 1)) or not np.all(np.isin(y, (0.0, 1.0))):
        raise ValueError("p must be in [0,1] and y must be 0/1")
    return p, y


def strategy(p: np.ndarray, ret: np.ndarray, cost_side: float, cash_ret: float = 0.0) -> np.ndarray:
    """Long when P(up) > 0.5, else cash. ret[i] is the return earned AFTER decision i. Cost on every switch."""
    p, ret = np.asarray(p, float), np.asarray(ret, float)
    long = p > 0.5
    prev = np.concatenate([[False], long[:-1]])
    return np.where(long, ret, cash_ret) - (long != prev) * cost_side


def random_beat_share(n_long_frac: float, ret: np.ndarray, target: float, cost_side: float,
                      tries: int = 2000, seed: int = 0) -> float:
    """Share of random long/cash signals (same long share) whose total return beats `target`."""
    rng = np.random.default_rng(seed)
    ret = np.asarray(ret, float)
    wins = 0
    for _ in range(tries):
        p = (rng.random(ret.size) < n_long_frac).astype(float)
        if np.prod(1 + strategy(p, ret, cost_side)) - 1 > target:
            wins += 1
    return wins / tries


def report(name: str, p: np.ndarray, y: np.ndarray, ret: np.ndarray, base_rate: float, cost_side: float,
           cash_ret: float = 0.0) -> dict:
    """One row: scores vs baselines + returns after costs vs holding.
    y[i] = 1 if the bar Kronos forecast closed up; ret[i] = return actually earned after decision i
    (filled at the next open, so it can differ from the forecast bar: no look-ahead)."""
    p, y, ret = np.asarray(p, float), np.asarray(y, float), np.asarray(ret, float)
    if not (p.size == y.size == ret.size):
        raise ValueError("p, y, ret must be the same length")
    rw, br = np.full_like(p, 0.5), np.full_like(p, float(np.clip(base_rate, EPS, 1 - EPS)))
    bot = strategy(p, ret, cost_side, cash_ret)
    eq_bot, eq_hold = np.cumprod(1 + bot), np.cumprod(1 + ret)
    tot_bot, tot_hold = float(eq_bot[-1] - 1), float(eq_hold[-1] - 1)
    out = {
        "name": name, "bars": int(p.size), "up_share": round(float(y.mean()), 4),
        "base_rate_train": round(float(base_rate), 4),
        "brier": {"kronos": round(brier(p, y), 5), "random_walk": round(brier(rw, y), 5),
                  "base_rate": round(brier(br, y), 5)},
        "log_loss": {"kronos": round(log_loss(p, y), 5), "random_walk": round(log_loss(rw, y), 5),
                     "base_rate": round(log_loss(br, y), 5)},
        "direction_accuracy": round(float(((p > 0.5) == (y == 1)).mean()), 4),
        "long_share": round(float((p > 0.5).mean()), 4),
        "return_after_costs": round(tot_bot, 4), "return_hold": round(tot_hold, 4),
        "worst_fall_bot": round(float((eq_bot / np.maximum.accumulate(eq_bot) - 1).min()), 4),
        "worst_fall_hold": round(float((eq_hold / np.maximum.accumulate(eq_hold) - 1).min()), 4),
        "random_signals_beat_bot": round(random_beat_share(float((p > 0.5).mean()), ret, tot_bot, cost_side), 4),
    }
    b, ll = out["brier"], out["log_loss"]
    out["beats_baselines"] = bool(b["kronos"] < min(b["random_walk"], b["base_rate"])
                                  and ll["kronos"] < min(ll["random_walk"], ll["base_rate"]))
    out["beats_hold_after_costs"] = tot_bot > tot_hold
    out["passes"] = out["beats_baselines"] and out["beats_hold_after_costs"]
    return out


def frame_from(preds: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """preds has columns p_up, up (0/1), ret. Drops rows with missing values (e.g. the last bars)."""
    d = preds.dropna(subset=["p_up", "up", "ret"])
    return d["p_up"].to_numpy(float), d["up"].to_numpy(float), d["ret"].to_numpy(float)

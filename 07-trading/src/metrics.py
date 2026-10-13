"""Overfitting-aware statistics, written from the papers (no AGPL/GPL code copied).

- sharpe: annualised at 252 trading days, zero risk-free rate.
- psr: Probabilistic Sharpe Ratio, Bailey & Lopez de Prado (2012).
- dsr: Deflated Sharpe Ratio, Bailey & Lopez de Prado (2014).
- pbo_cscv: Probability of Backtest Overfitting via combinatorially symmetric
  cross-validation, Bailey, Borwein, Lopez de Prado & Zhu (2017).
"""
from __future__ import annotations

from itertools import combinations
from math import erf, exp, log, sqrt

import numpy as np
import pandas as pd

EULER_GAMMA = 0.5772156649015329
ANN = 252


def _phi(x: float) -> float:
    return 0.5 * (1 + erf(x / sqrt(2)))


def _phi_inv(p: float) -> float:
    """Inverse normal CDF (Acklam's rational approximation, |error| < 1.2e-9 after one Newton step)."""
    if not 0 < p < 1:
        raise ValueError("p must be in (0, 1)")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
    pl = 0.02425
    if p < pl:
        q = sqrt(-2 * log(p))
        x = (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    elif p <= 1 - pl:
        q = p - 0.5
        r = q * q
        x = (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    else:
        q = sqrt(-2 * log(1 - p))
        x = -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    e = _phi(x) - p  # one Newton refinement
    return x - e * sqrt(2 * np.pi) * exp(x * x / 2)


def sharpe(returns: pd.Series | np.ndarray, periods: int = ANN) -> float:
    r = np.asarray(returns, dtype=float)
    sd = r.std(ddof=1)
    return float(r.mean() / sd * sqrt(periods)) if sd > 0 else 0.0


def _moments(r: np.ndarray) -> tuple[float, float, float]:
    sd = r.std(ddof=1)
    sr = r.mean() / sd if sd > 0 else 0.0
    z = (r - r.mean()) / r.std(ddof=0) if r.std(ddof=0) > 0 else np.zeros_like(r)
    skew = float((z ** 3).mean())
    kurt = float((z ** 4).mean())  # non-excess (normal = 3)
    return float(sr), skew, kurt


def psr(returns, sr_benchmark: float = 0.0) -> float:
    """P(true per-period Sharpe > sr_benchmark). sr_benchmark is per period (not annualised)."""
    r = np.asarray(returns, dtype=float)
    n = len(r)
    if n < 3:
        return 0.0
    sr, skew, kurt = _moments(r)
    denom = 1 - skew * sr + (kurt - 1) / 4 * sr ** 2
    if denom <= 0:
        return 0.0
    return _phi((sr - sr_benchmark) * sqrt(n - 1) / sqrt(denom))


def expected_max_sharpe(sr_variance: float, n_trials: int) -> float:
    """E[max per-period Sharpe] of n_trials skill-less strategies (False Strategy Theorem)."""
    if n_trials <= 1:
        return 0.0
    g = EULER_GAMMA
    return sqrt(sr_variance) * ((1 - g) * _phi_inv(1 - 1 / n_trials)
                                + g * _phi_inv(1 - 1 / (n_trials * np.e)))


def dsr(returns, n_trials: int, sr_variance: float | None = None) -> float:
    """Deflated Sharpe Ratio: PSR against the Sharpe the best of n_trials lucky tries would show.

    If sr_variance (variance of per-period Sharpe across trials) is unknown, use the
    sampling variance of one Sharpe estimate, 1/(n-1): a conservative default.
    """
    r = np.asarray(returns, dtype=float)
    if sr_variance is None:
        sr_variance = 1.0 / max(len(r) - 1, 1)
    return psr(r, expected_max_sharpe(sr_variance, n_trials))


def pbo_cscv(matrix: pd.DataFrame | np.ndarray, n_splits: int = 16) -> float:
    """Probability of Backtest Overfitting.

    matrix: T x N net returns, one column per configuration tried.
    Splits rows into n_splits blocks; for every half/half combination, picks the
    best in-sample config and checks its out-of-sample rank. PBO = share of
    combinations where the IS winner lands in the bottom half OOS (logit <= 0).
    """
    m = np.asarray(matrix, dtype=float)
    t, n = m.shape
    if n < 2:
        raise ValueError("PBO needs at least 2 configurations")
    if n_splits % 2 or n_splits < 4:
        raise ValueError("n_splits must be even and >= 4")
    t -= t % n_splits
    blocks = np.array_split(m[:t], n_splits)
    # per-block sums and sums of squares make each combination O(N)
    cnt = np.array([len(b) for b in blocks], dtype=float)
    s1 = np.array([b.sum(0) for b in blocks])
    s2 = np.array([(b ** 2).sum(0) for b in blocks])

    def _sr(idx):
        k = cnt[list(idx)].sum()
        mu = s1[list(idx)].sum(0) / k
        var = s2[list(idx)].sum(0) / k - mu ** 2
        return np.where(var > 0, mu / np.sqrt(np.maximum(var, 1e-300)), 0.0)

    all_idx = set(range(n_splits))
    below = total = 0
    for is_idx in combinations(range(n_splits), n_splits // 2):
        oos_idx = tuple(all_idx - set(is_idx))
        best = int(np.argmax(_sr(is_idx)))
        oos = _sr(oos_idx)
        rank = (oos < oos[best]).sum() + 1  # 1..N, N = best OOS
        w = rank / (n + 1)
        below += np.log(w / (1 - w)) <= 0
        total += 1
    return below / total

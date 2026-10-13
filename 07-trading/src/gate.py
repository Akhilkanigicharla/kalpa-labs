"""The Overfit Gatekeeper (Q7.4). Verdict: "rejected" or "paper". Never "live".

A strategy passes only if ALL criteria hold. THRESHOLDS ARE PENDING CEO APPROVAL
(ROADMAP C-queue, PLAN.md Q7.4); until Akhil approves them every verdict says so.

Criteria (PLAN.md Q7.4, plus DSR proposed by Deep Scan v2):
 1. Rolling walk-forward OOS Sharpe >= 0.5 AND above buy-and-hold on the same days.
 2. PSR >= 0.95 on the OOS returns.
 3. At least 30 OOS trades (round trips = position changes / 2).
 4. PBO (CSCV) < 0.5 across the configuration grid.
 5. Criterion 1 still holds at 2x costs plus a one-bar fill delay.
 6. (proposed) Deflated Sharpe >= 0.95 using every config ever logged for this hypothesis.
Sharpe is annualised at 252. Research code, paper only, not advice.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from . import backtest, metrics, trials
from .strategies import param_grid

THRESHOLDS = {
    "oos_sharpe_min": 0.5,
    "psr_min": 0.95,
    "oos_trades_min": 30,
    "pbo_max": 0.5,
    "stress_cost_mult": 2.0,
    "stress_delay": 2,       # one extra bar
    "dsr_min": 0.95,
    "train_days": 756,       # 3 years in-sample per fold
    "test_days": 252,        # 1 year out-of-sample per fold
}
THRESHOLDS_STATUS = "pending CEO approval"


class GateError(RuntimeError):
    pass


@dataclass
class Verdict:
    trial_id: str
    verdict: str
    checks: dict[str, bool]
    numbers: dict[str, float]
    chosen: list[dict] = field(default_factory=list)
    thresholds_status: str = THRESHOLDS_STATUS

    def summary(self) -> str:
        lines = [f"{self.trial_id}: {self.verdict.upper()} (thresholds {self.thresholds_status})"]
        lines += [f"  [{'x' if ok else ' '}] {k}" for k, ok in self.checks.items()]
        lines += [f"  {k} = {v:.3f}" for k, v in self.numbers.items()]
        return "\n".join(lines)


def walk_forward(close: pd.Series, strategy: str, *, delay: int = 1, cost_mult: float = 1.0,
                 train: int | None = None, test: int | None = None):
    """Rolling walk-forward: pick the best-IS-Sharpe config per fold, trade it OOS.

    Returns (oos_returns, oos_trades, chosen_params_per_fold, full_config_matrix).
    """
    train = train or THRESHOLDS["train_days"]
    test = test or THRESHOLDS["test_days"]
    mat, grid = backtest.config_matrix(close, strategy, delay=delay, cost_mult=cost_mult)
    from .strategies import weights
    pieces, chosen, n_changes = [], [], 0
    start = train
    while start + test <= len(close):
        is_slice = mat.iloc[start - train:start]
        best = int(np.argmax([metrics.sharpe(is_slice[c]) for c in is_slice.columns]))
        res = backtest.run(close, weights(strategy, close, **grid[best]), delay=delay, cost_mult=cost_mult)
        oos = slice(start, start + test)
        pieces.append(res.returns.iloc[oos])
        held = res.held.iloc[start - 1:start + test]
        n_changes += int((held.diff().abs() > 0.01).sum())
        chosen.append(grid[best])
        start += test
    if not pieces:
        raise GateError(f"need at least {train + test} bars, got {len(close)}")
    # a round trip (in and out) is 2 position changes; count round trips (stricter)
    return pd.concat(pieces), n_changes // 2, chosen, mat


def evaluate(close: pd.Series, strategy: str, trial_id: str | None, *,
             registry: Path | None = None, record: bool = True) -> Verdict:
    """Run the gate. Refuses to run unless `trial_id` was logged first."""
    t = trials.get_trial(trial_id, path=registry)  # raises TrialError if not logged
    if t["strategy"] != strategy:
        raise GateError(f"trial {trial_id} was logged for {t['strategy']}, not {strategy}")
    if int(t["n_configs"]) != len(param_grid(strategy)):
        raise GateError("logged n_configs does not match the grid being run; log a new trial")

    oos, n_trades, chosen, mat = walk_forward(close, strategy)
    bh = backtest.buy_and_hold(close).returns.loc[oos.index]
    s_oos, s_bh = metrics.sharpe(oos), metrics.sharpe(bh)
    is_sharpe = float(max(metrics.sharpe(mat[c]) for c in mat.columns))

    stress, _, _, _ = walk_forward(close, strategy, delay=THRESHOLDS["stress_delay"],
                                   cost_mult=THRESHOLDS["stress_cost_mult"])
    bh_stress = backtest.run(close, pd.Series(1.0, index=close.index),
                             cost_mult=THRESHOLDS["stress_cost_mult"]).returns.loc[stress.index]
    s_stress = metrics.sharpe(stress)

    n_all = trials.configs_tried(t["hypothesis_id"], path=registry)
    sr_var = float(np.var([metrics.sharpe(mat[c], periods=1) for c in mat.columns], ddof=1)) \
        if mat.shape[1] > 1 else None
    psr = metrics.psr(oos)
    dsr = metrics.dsr(oos, max(n_all, 1), sr_var if sr_var and sr_var > 0 else None)
    pbo = metrics.pbo_cscv(mat.loc[oos.index[0]:]) if mat.shape[1] > 1 else 1.0

    th = THRESHOLDS
    checks = {
        "1 OOS Sharpe >= 0.5 and > buy-and-hold": s_oos >= th["oos_sharpe_min"] and s_oos > s_bh,
        "2 PSR >= 0.95": psr >= th["psr_min"],
        "3 OOS trades >= 30": n_trades >= th["oos_trades_min"],
        "4 PBO < 0.5": pbo < th["pbo_max"],
        "5 survives 2x costs + 1-bar delay": s_stress >= th["oos_sharpe_min"]
                                              and s_stress > metrics.sharpe(bh_stress),
        "6 DSR >= 0.95 (proposed)": dsr >= th["dsr_min"],
    }
    numbers = {"is_sharpe": is_sharpe, "oos_sharpe": s_oos, "bh_sharpe": s_bh, "psr": psr,
               "dsr": dsr, "pbo": float(pbo), "oos_trades": float(n_trades),
               "stress_sharpe": s_stress, "configs_logged": float(n_all),
               "oos_max_dd": backtest.max_drawdown(oos)}
    v = Verdict(trial_id, "paper" if all(checks.values()) else "rejected", checks, numbers, chosen)
    if record:
        trials.record_result(trial_id, {**{k: numbers[k] for k in
                             ("is_sharpe", "oos_sharpe", "bh_sharpe", "psr", "dsr", "pbo", "stress_sharpe")},
                             "oos_trades": n_trades, "verdict": v.verdict}, path=registry)
    return v

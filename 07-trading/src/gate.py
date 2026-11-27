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
 7. (A247) No repaint and no look-ahead in any config: truncation test + future-scramble test
    (src/causal.py), and every run uses a fill delay >= 1 bar.
 8. (A247) Multi-asset: the same rule, walk-forward picked the same way, passes on most of an
    ETF basket (NIFTYBEES, BANKBEES, GOLDBEES, JUNIORBEES). Per asset: OOS Sharpe >= 0.5 and
    still profitable (Sharpe > 0) at 2x costs + one extra bar of delay. "Most" = more than half
    (3 of 4). No basket given = not checked = rejected.
Sharpe is annualised at 252. Research code, paper only, not advice.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from . import backtest, causal, metrics, trials
from .strategies import param_grid

THRESHOLDS = {
    "oos_sharpe_min": 0.5,
    "psr_min": 0.95,
    "oos_trades_min": 30,
    "pbo_max": 0.5,
    "stress_cost_mult": 2.0,
    "stress_delay": 2,       # one extra bar
    "dsr_min": 0.95,
    "basket_sharpe_min": 0.5,   # per-asset OOS Sharpe (A247)
    "basket_stress_min": 0.0,   # per-asset Sharpe at 2x costs + extra bar
    "train_days": 756,       # 3 years in-sample per fold
    "test_days": 252,        # 1 year out-of-sample per fold
    # Yearly return on money the bot keeps out of the market. 0 = old behaviour. A real track-A
    # bot parks idle money in a liquid ETF: LIQUIDBEES 4.69%/yr since 2003 after its 0.69% fee
    # (anandrathi.com, 1 Jun 2025). Use 0.047 for track A; crypto (track B) has no such ETF: 0.
    "cash_rate": 0.0,
}
THRESHOLDS_STATUS = "pending CEO approval"
BASKET = ("NIFTYBEES", "BANKBEES", "GOLDBEES", "JUNIORBEES")
BASKET_START = "2010-02-01"  # Yahoo's GOLDBEES rows before Jan 2010 are mostly zero prices (stress.py)


class GateError(RuntimeError):
    pass


@dataclass
class Verdict:
    trial_id: str
    verdict: str
    checks: dict[str, bool]
    numbers: dict[str, float]
    chosen: list[dict] = field(default_factory=list)
    basket: dict = field(default_factory=dict)
    causal: dict = field(default_factory=dict)
    thresholds_status: str = THRESHOLDS_STATUS

    def summary(self) -> str:
        lines = [f"{self.trial_id}: {self.verdict.upper()} (thresholds {self.thresholds_status})"]
        lines += [f"  [{'x' if ok else ' '}] {k}" for k, ok in self.checks.items()]
        lines += [f"  {k} = {v:.3f}" for k, v in self.numbers.items()]
        return "\n".join(lines)


def walk_forward(close: pd.Series, strategy: str, *, delay: int = 1, cost_mult: float = 1.0,
                 train: int | None = None, test: int | None = None, cash_rate: float | None = None):
    """Rolling walk-forward: pick the best-IS-Sharpe config per fold, trade it OOS.

    Returns (oos_returns, oos_trades, chosen_params_per_fold, full_config_matrix).
    """
    try:
        backtest.check_delay(delay)
    except ValueError as e:
        raise GateError(str(e)) from None
    train = train or THRESHOLDS["train_days"]
    test = test or THRESHOLDS["test_days"]
    cr = THRESHOLDS["cash_rate"] if cash_rate is None else cash_rate
    mat, grid = backtest.config_matrix(close, strategy, delay=delay, cost_mult=cost_mult, cash_rate=cr)
    from .strategies import weights
    pieces, chosen, n_changes = [], [], 0
    start = train
    while start + test <= len(close):
        is_slice = mat.iloc[start - train:start]
        best = int(np.argmax([metrics.sharpe(is_slice[c]) for c in is_slice.columns]))
        res = backtest.run(close, weights(strategy, close, **grid[best]), delay=delay, cost_mult=cost_mult, cash_rate=cr)
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


def basket_pass_min(n: int) -> int:
    """'Pass on most' = more than half: 3 of 4, 2 of 3, 3 of 5."""
    return n // 2 + 1


def multi_asset(basket: dict[str, pd.Series], strategy: str, *, cash_rate: float | None = None) -> dict:
    """A247 check 8: run the rule on every basket asset the same honest way (walk-forward pick,
    then 2x costs + one extra bar). Returns per-asset numbers, the pass count and ok."""
    th, rows = THRESHOLDS, {}
    for sym, close in basket.items():
        try:
            oos, n_tr, _, _ = walk_forward(close, strategy, cash_rate=cash_rate)
            st, _, _, _ = walk_forward(close, strategy, delay=th["stress_delay"],
                                       cost_mult=th["stress_cost_mult"], cash_rate=cash_rate)
        except GateError as e:  # too little history counts as a fail, never a skip
            rows[sym] = {"passed": False, "why": str(e)}
            continue
        s, s_st = metrics.sharpe(oos), metrics.sharpe(st)
        bh = metrics.sharpe(backtest.buy_and_hold(close).returns.loc[oos.index])
        rows[sym] = {"oos_sharpe": round(float(s), 3), "stress_sharpe": round(float(s_st), 3),
                     "bh_sharpe": round(float(bh), 3), "oos_trades": n_tr,
                     "oos_total": round(float((1 + oos).prod() - 1), 3),
                     "passed": bool(s >= th["basket_sharpe_min"] and s_st > th["basket_stress_min"])}
    n_pass = sum(r["passed"] for r in rows.values())
    return {"assets": rows, "passed": n_pass, "of": len(rows),
            "need": basket_pass_min(len(rows)), "ok": bool(rows) and n_pass >= basket_pass_min(len(rows))}


def load_basket(symbols=BASKET, *, start: str = BASKET_START, refresh: bool = False) -> dict[str, pd.Series]:
    """Closes for the ETF basket from the local Parquet cache (Yahoo via yfinance when missing),
    with wrong-scale split rows removed (data.repair_spikes)."""
    from . import data
    out = {}
    for s in symbols:
        df, _ = data.repair_spikes(data.get_daily(s, start=start, refresh=refresh, strict=False))
        if p := data.validate(df):
            raise GateError(f"{s}: data problems after repair: {'; '.join(p)}")
        out[s] = df["close"]
    return out


def evaluate(close: pd.Series, strategy: str, trial_id: str | None, *,
             registry: Path | None = None, record: bool = True, cash_rate: float | None = None,
             basket: dict[str, pd.Series] | None = None) -> Verdict:
    """Run the gate. Refuses to run unless `trial_id` was logged first."""
    if THRESHOLDS["stress_delay"] < 2:
        raise GateError("stress_delay must be at least 2 (one bar more than the normal fill)")
    t = trials.get_trial(trial_id, path=registry)  # raises TrialError if not logged
    if t["strategy"] != strategy:
        raise GateError(f"trial {trial_id} was logged for {t['strategy']}, not {strategy}")
    if int(t["n_configs"]) != len(param_grid(strategy)):
        raise GateError("logged n_configs does not match the grid being run; log a new trial")

    oos, n_trades, chosen, mat = walk_forward(close, strategy, cash_rate=cash_rate)
    bh = backtest.buy_and_hold(close).returns.loc[oos.index]
    s_oos, s_bh = metrics.sharpe(oos), metrics.sharpe(bh)
    is_sharpe = float(max(metrics.sharpe(mat[c]) for c in mat.columns))

    stress, _, _, _ = walk_forward(close, strategy, delay=THRESHOLDS["stress_delay"],
                                   cost_mult=THRESHOLDS["stress_cost_mult"], cash_rate=cash_rate)
    bh_stress = backtest.run(close, pd.Series(1.0, index=close.index),
                             cost_mult=THRESHOLDS["stress_cost_mult"]).returns.loc[stress.index]
    s_stress = metrics.sharpe(stress)

    n_all = trials.configs_tried(t["hypothesis_id"], path=registry)
    sr_var = float(np.var([metrics.sharpe(mat[c], periods=1) for c in mat.columns], ddof=1)) \
        if mat.shape[1] > 1 else None
    psr = metrics.psr(oos)
    dsr = metrics.dsr(oos, max(n_all, 1), sr_var if sr_var and sr_var > 0 else None)
    pbo = metrics.pbo_cscv(mat.loc[oos.index[0]:]) if mat.shape[1] > 1 else 1.0

    cz = causal.check_strategy(strategy, close)
    mb = multi_asset(basket, strategy, cash_rate=cash_rate) if basket else {"passed": 0, "of": 0, "ok": False}

    th = THRESHOLDS
    checks = {
        "1 OOS Sharpe >= 0.5 and > buy-and-hold": s_oos >= th["oos_sharpe_min"] and s_oos > s_bh,
        "2 PSR >= 0.95": psr >= th["psr_min"],
        "3 OOS trades >= 30": n_trades >= th["oos_trades_min"],
        "4 PBO < 0.5": pbo < th["pbo_max"],
        "5 survives 2x costs + 1-bar delay": s_stress >= th["oos_sharpe_min"]
                                              and s_stress > metrics.sharpe(bh_stress),
        "6 DSR >= 0.95 (proposed)": dsr >= th["dsr_min"],
        "7 no repaint, no look-ahead, delay >= 1": cz["ok"],
        "8 passes on most of the ETF basket": mb["ok"],
    }
    numbers = {"is_sharpe": is_sharpe, "oos_sharpe": s_oos, "bh_sharpe": s_bh, "psr": psr,
               "dsr": dsr, "pbo": float(pbo), "oos_trades": float(n_trades),
               "stress_sharpe": s_stress, "configs_logged": float(n_all),
               "oos_max_dd": backtest.max_drawdown(oos),
               "basket_passed": float(mb["passed"]), "basket_size": float(mb["of"])}
    v = Verdict(trial_id, "paper" if all(checks.values()) else "rejected", checks, numbers, chosen,
                basket=mb, causal=cz)
    if record:
        trials.record_result(trial_id, {**{k: numbers[k] for k in
                             ("is_sharpe", "oos_sharpe", "bh_sharpe", "psr", "dsr", "pbo", "stress_sharpe")},
                             "oos_trades": n_trades, "basket": f"{mb['passed']}/{mb['of']}",
                             "verdict": v.verdict}, path=registry)
    return v


def main(argv: list[str] | None = None) -> int:
    """Multi-asset + causal report for every registered rule (research only, no trials logged)."""
    import argparse
    import json
    from datetime import datetime
    from .strategies import REGISTRY
    ap = argparse.ArgumentParser(description="A247 basket + no-repaint check for every candidate (paper only)")
    ap.add_argument("--out", type=Path, default=Path("reports") / f"a247-basket-{datetime.now(trials.IST):%Y-%m-%d}.json")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args(argv)
    basket = load_basket(refresh=a.refresh)
    rep = {"basket": list(basket), "from": str(min(c.index[0] for c in basket.values()).date()),
           "to": str(max(c.index[-1] for c in basket.values()).date()),
           "thresholds_status": THRESHOLDS_STATUS, "rules": {}}
    for name in REGISTRY:
        if name == "hold":
            continue
        mb = multi_asset(basket, name)
        cz = causal.check_strategy(name, basket["NIFTYBEES"])
        rep["rules"][name] = {"basket": mb, "causal_ok": cz["ok"]}
        print(f"{name:14} basket {mb['passed']}/{mb['of']} {'PASS' if mb['ok'] else 'fail'}  "
              f"causal {'ok' if cz['ok'] else 'FAIL'}  " +
              " ".join(f"{s}:{r.get('oos_sharpe', 'na')}" for s, r in mb["assets"].items()))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(rep, indent=1), encoding="utf-8")
    print(a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

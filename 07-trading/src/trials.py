"""Trials registry (Q7.5): every backtest configuration family must be logged
before the gate will look at it. The count of trials per hypothesis feeds the
Deflated Sharpe Ratio, so hiding failed attempts is impossible by design.

File: 07-trading/research/trials.csv (in git; holds metrics only, no prices).
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

REGISTRY = Path(__file__).resolve().parents[1] / "research" / "trials.csv"
FIELDS = ["trial_id", "logged_ist", "hypothesis_id", "strategy", "params", "data",
          "n_configs", "is_sharpe", "oos_sharpe", "bh_sharpe", "psr", "dsr", "pbo",
          "oos_trades", "stress_sharpe", "verdict"]
IST = timezone(timedelta(hours=5, minutes=30))


class TrialError(RuntimeError):
    pass


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def _write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


def log_trial(hypothesis_id: str, strategy: str, params: dict | list, data: str,
              n_configs: int, *, path: Path | None = None) -> str:
    """Register a trial BEFORE running it. Returns the trial id."""
    if not hypothesis_id.strip():
        raise TrialError("hypothesis_id is required (e.g. H1-tsmom-nifty)")
    path = path or REGISTRY
    rows = _read(path)
    tid = f"T{len(rows) + 1:04d}"
    rows.append({"trial_id": tid, "logged_ist": datetime.now(IST).strftime("%Y-%m-%d %H:%M"),
                 "hypothesis_id": hypothesis_id, "strategy": strategy,
                 "params": json.dumps(params, separators=(",", ":")), "data": data,
                 "n_configs": str(int(n_configs))})
    _write(path, rows)
    return tid


def get_trial(trial_id: str | None, *, path: Path | None = None) -> dict:
    if not trial_id:
        raise TrialError("no trial id: log the trial first with trials.log_trial()")
    for r in _read(path or REGISTRY):
        if r["trial_id"] == trial_id:
            return r
    raise TrialError(f"trial {trial_id} is not in the registry; log it first")


def configs_tried(hypothesis_id: str, *, path: Path | None = None) -> int:
    """Total configurations tried so far for a hypothesis (for the DSR)."""
    return sum(int(r["n_configs"] or 0) for r in _read(path or REGISTRY)
               if r["hypothesis_id"] == hypothesis_id)


def record_result(trial_id: str, result: dict, *, path: Path | None = None) -> None:
    path = path or REGISTRY
    rows = _read(path)
    for r in rows:
        if r["trial_id"] == trial_id:
            if r.get("verdict"):
                raise TrialError(f"trial {trial_id} already has a verdict; log a new trial")
            for k, v in result.items():
                if k in FIELDS:
                    r[k] = f"{v:.4f}" if isinstance(v, float) else str(v)
            _write(path, rows)
            return
    raise TrialError(f"trial {trial_id} is not in the registry")

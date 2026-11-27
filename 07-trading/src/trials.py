"""Trials registry (Q7.5): every backtest configuration family must be logged
before the gate will look at it. The count of trials per hypothesis feeds the
Deflated Sharpe Ratio, so hiding failed attempts is impossible by design.

File: 07-trading/research/trials.csv (in git; holds metrics only, no prices).
"""
from __future__ import annotations

import csv
import hashlib
import inspect
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

REGISTRY = Path(__file__).resolve().parents[1] / "research" / "trials.csv"
FIELDS = ["trial_id", "logged_ist", "hypothesis_id", "strategy", "params", "data",
          "n_configs", "is_sharpe", "oos_sharpe", "bh_sharpe", "psr", "dsr", "pbo",
          "oos_trades", "stress_sharpe", "verdict", "basket",
          "config_hash", "frozen_ist", "frozen_config"]
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


# ---------------------------------------------------------------- A247: freeze before paper
def _code_of(fn, seen: set | None = None) -> str:
    """Source of a strategy function plus every strategies.py function it calls (one hash
    covers tsmom_vt -> tsmom + vol_target), so editing the rule's code breaks the freeze."""
    from . import strategies
    seen = seen if seen is not None else set()
    if fn.__name__ in seen:
        return ""
    seen.add(fn.__name__)
    out = inspect.getsource(fn)
    for name in fn.__code__.co_names:
        g = getattr(strategies, name, None)
        if inspect.isfunction(g) and g.__module__ == strategies.__name__:
            out += _code_of(g, seen)
    return out


def config_hash(strategy: str, params: dict, symbol: str) -> tuple[str, str]:
    """(sha256, canonical JSON) of what paper will trade: rule name, exact params, symbol, rule code."""
    from .strategies import REGISTRY
    if strategy not in REGISTRY:
        raise TrialError(f"unknown strategy {strategy!r}")
    cfg = json.dumps({"strategy": strategy, "params": params, "symbol": symbol.strip().upper()},
                     sort_keys=True, separators=(",", ":"))
    code = hashlib.sha256(_code_of(REGISTRY[strategy][0]).encode()).hexdigest()
    return hashlib.sha256(f"{cfg}|{code}".encode()).hexdigest(), cfg


def freeze(trial_id: str, strategy: str, params: dict, symbol: str, *, path: Path | None = None) -> str:
    """Write the frozen config hash BEFORE paper starts. Only a gate 'paper' verdict can be
    frozen, and a frozen trial can never be re-frozen to something else (log a new trial)."""
    path = path or REGISTRY
    rows = _read(path)
    for r in rows:
        if r["trial_id"] != trial_id:
            continue
        if r.get("verdict") != "paper":
            raise TrialError(f"trial {trial_id} has verdict {r.get('verdict') or 'none'}; only 'paper' can be frozen")
        if r["strategy"] != strategy:
            raise TrialError(f"trial {trial_id} was logged for {r['strategy']}, not {strategy}")
        h, cfg = config_hash(strategy, params, symbol)
        if r.get("config_hash"):
            if r["config_hash"] != h:
                raise TrialError(f"trial {trial_id} is already frozen to another config; log a new trial")
            return h
        r.update(config_hash=h, frozen_ist=datetime.now(IST).strftime("%Y-%m-%d %H:%M"), frozen_config=cfg)
        _write(path, rows)
        return h
    raise TrialError(f"trial {trial_id} is not in the registry")


def verify_frozen(trial_id: str, strategy: str, params: dict, symbol: str, *, path: Path | None = None) -> str:
    """Paper refuses to run unless today's config and code hash match the frozen one."""
    r = get_trial(trial_id, path=path)
    if not r.get("config_hash"):
        raise TrialError(f"trial {trial_id} is not frozen; run trials.freeze() before paper starts")
    h, _ = config_hash(strategy, params, symbol)
    if h != r["config_hash"]:
        raise TrialError(f"trial {trial_id}: config or rule code changed since it was frozen; log a new trial")
    return h

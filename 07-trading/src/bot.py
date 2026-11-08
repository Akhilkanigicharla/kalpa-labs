"""b7 daily bot (A153): strategy signal → target quantity → Live Guard → broker.

Runs once a day after the NSE close (GitHub Actions, 15:50 IST). Dry run unless the Live Guard's
three switches are on (see live.py). State (risk marks, dry-run holdings, cash) is kept in
research/bot-state.json so the daily/weekly/monthly loss caps work across runs.

  python -m src.bot --strategy ma_filter --trial T009 --symbols NIFTYBEES,GOLDBEES
"""
from __future__ import annotations

import argparse
import json
import math
import os
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from .live import DryRunBroker, Guard, HERE
from .paper import STOP_PCT
from .risk import LIMITS, RiskBook
from .strategies import weights

STATE = HERE / "research" / "bot-state.json"
MIN_BARS = 260   # one trading year: enough for 200-day filters and 252-day momentum


def targets_for(bars: dict[str, pd.DataFrame], strategy: str, pot: float, held: dict[str, int],
                limits: dict = LIMITS, **params) -> tuple[dict[str, tuple[int, float | None]], dict[str, float]]:
    """Each symbol gets an equal slice of the pot, scaled by the strategy weight, then capped so the
    stop-loss risk stays inside per_trade_risk and the position inside position_size."""
    out, last = {}, {}
    slice_ = pot / max(1, len(bars))
    for sym, df in bars.items():
        close = df["close"].sort_index()
        w = float(weights(strategy, close, **params).fillna(0.0).clip(0.0, 1.0).iloc[-1])
        px = float(close.iloc[-1])
        last[sym] = px
        stop = round(px * (1 - STOP_PCT), 2)
        want = math.floor(w * slice_ / px + 1e-9)
        h = held.get(sym, 0)
        if want > h:   # caps apply to the WHOLE position, so it cannot creep up day after day
            max_risk = math.floor(limits["per_trade_risk"] * pot / (px - stop) + 1e-9)
            max_size = math.floor(limits["position_size"] * pot / px + 1e-9)
            want = max(h, min(want, max_risk, max_size))
        out[sym] = (want, stop)
    return out, last


def load_state(path: Path) -> dict:
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {}


def save_state(path: Path, g: Guard, broker: DryRunBroker | None) -> None:
    s = {"pot": g.book.pot, "marks": {d.isoformat(): v for d, v in sorted(g.book.marks.items())[-120:]}}
    if broker is not None and broker.name == "dry-run":
        s["dry"] = {"cash": broker.cash_inr, "held": broker.held}
    Path(path).write_text(json.dumps(s, indent=1))


def run(strategy: str, trial: str, symbols: list[str], *, bars: dict[str, pd.DataFrame] | None = None,
        broker=None, env=None, state_path: Path = STATE, today: date | None = None, **params) -> Guard:
    env = dict(os.environ) if env is None else env
    if bars is None:
        from .data import get_daily
        start = (datetime.now().date().replace(day=1) - pd.Timedelta(days=3 * 365)).isoformat()
        bars = {s: get_daily(s, start=start, refresh=True, strict=False) for s in symbols}
    st = load_state(state_path)
    cap = float(env.get("KL_LIVE_CAPITAL", "5000"))
    if broker is None:
        last = {s: float(df["close"].iloc[-1]) for s, df in bars.items()}
        dry = st.get("dry", {})
        broker = DryRunBroker(prices=last, cash_inr=dry.get("cash", cap), held=dict(dry.get("held", {})))
    book = RiskBook(pot=st.get("pot", cap), marks={date.fromisoformat(k): v for k, v in st.get("marks", {}).items()})
    g = Guard(broker=broker, trial_id=trial, book=book, env=env, universe=tuple(symbols))
    short = [s for s, df in bars.items() if len(df) < MIN_BARS]
    if short:   # never trade on a signal the data cannot support; keep holdings as they are
        g._say(f"NO TRADE: too little price history for {', '.join(short)} (need {MIN_BARS} days)")
        bars = {s: df for s, df in bars.items() if s not in short}
    held = {s: q for s, q in broker.positions().items() if s in symbols}
    tg, _ = targets_for(bars, strategy, book.pot, held, book.limits, **params)
    g.run_once(tg, today or datetime.now().date())
    save_state(state_path, g, broker if isinstance(broker, DryRunBroker) else None)
    return g


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", default="ma_filter")
    ap.add_argument("--trial", default="")
    ap.add_argument("--symbols", default="NIFTYBEES,GOLDBEES")
    a = ap.parse_args(argv)
    g = run(a.strategy, a.trial, [s.strip() for s in a.symbols.split(",") if s.strip()])
    print(f"mode={'LIVE' if g.live else 'DRY'} broker={g.broker.name} pot={g.book.pot:.0f} "
          f"positions={g.broker.positions()} alerts={len(g.alerts)}")
    for a_ in g.alerts:
        print(" -", a_)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

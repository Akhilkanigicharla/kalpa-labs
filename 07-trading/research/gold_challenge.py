"""A306: paper gold challenge. Runs the daily gold trend strategy (A305, research/gold_prop.py) on live
Yahoo prices every weekday against the exact Hindustan Funded 1-Step and Greenwick 2-Step rules, and writes
a phone-readable status. PAPER ONLY: no orders, no account, no fee. Both firms ban bots (see
research/gold-prop-2026-11-21.md), so this only answers "would it have passed?" before any fee is paid.
Rule: 90 calendar days of paper first; a fee is only worth discussing if a rule set shows PASSED by then.

Rules (RULES in gold_prop.py, from the firms' pages read 21 Nov 2026):
  daily loss  : equity may not fall more than 5% below the day's opening equity at any point in the day
  max loss    : 10% of the account size below the high-water mark (HF1, trailing) or the start (GW2, static)
  target      : +10% (HF1); +8% then +5% (GW2, balance resets between phases); only when flat
  min days    : 5 trading days (HF1)
  consistency : HF1 passes only when no single day is > 20% of total profit; until then it keeps trading
Kill switch: a file KILL in --flags stops all updates (the last numbers are kept, status says KILLED).

Run: cd 07-trading && python research/gold_challenge.py --paper paper/gold-challenge --flags paper/track-A/flags
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gold_prop as gp  # noqa: E402

RULES = gp.RULES
NAMES = {"HF1": "Hindustan 1-Step", "GW2": "Greenwick 2-Step"}
RISK = 0.01            # A305: best pass rate was the trend strategy at 1% risk on Hindustan rules
PAPER_DAYS = 90


class Challenge:
    """One prop-firm evaluation. Feed one trading day at a time: the day's worst and closing P&L in rupees
    relative to the day's opening equity, and whether the book is flat at the close."""

    def __init__(self, rule: dict):
        self.rule = rule
        self.size = rule["size"]
        self.base = self.equity = self.hwm = float(self.size)
        self.phase, self.days, self.history_pnl = 0, 0, []
        self.status, self.reason, self.note, self.last = "active", "", "", ""

    def floors(self) -> tuple[float, float]:
        daily = self.equity * (1 - self.rule["daily"])
        mx = (self.hwm if self.rule["trailing"] else self.base) - self.rule["maxdd"] * self.size
        return daily, mx

    def target(self) -> float:
        return round(self.base * (1 + self.rule["targets"][self.phase]), 2)   # 1.1 x 100000 is 110000.00000000001

    def day(self, when: str, worst: float, close: float, flat: bool = True) -> str:
        if self.status != "active":
            return self.status
        if not (np.isfinite(worst) and np.isfinite(close)):
            raise ValueError(f"bad P&L on {when}")
        daily, mx = self.floors()
        low = self.equity + min(worst, close)
        self.last, self.days = when, self.days + 1
        if low < daily:
            return self._fail(f"daily loss on {when}: low {low:,.0f} < {daily:,.0f}")
        if low < mx:
            return self._fail(f"max loss on {when}: low {low:,.0f} < {mx:,.0f}")
        self.equity += close
        self.history_pnl.append(close)
        self.hwm = max(self.hwm, self.equity)
        self.note = ""
        if self.equity < self.target():
            return self.status
        profit = self.equity - self.base
        if not flat:
            self.note = "target reached, waiting: position open"
        elif len(self.history_pnl) < self.rule["min_days"]:
            self.note = f"target reached, waiting: min {self.rule['min_days']} days"
        elif self.rule["consistency"] and max(self.history_pnl) > self.rule["consistency"] * profit:
            pct = 100 * max(self.history_pnl) / profit
            self.note = f"target reached, waiting: consistency (best day {pct:.0f}% > 20%)"
        else:
            self.phase += 1
            if self.phase == len(self.rule["targets"]):
                self.status, self.reason = "passed", f"passed on {when}"
            else:                                   # next phase starts fresh on the same account size
                self.base = self.equity = self.hwm = float(self.size)
                self.history_pnl = []
                self.note = f"phase {self.phase} passed on {when}"
        return self.status

    def _fail(self, why: str) -> str:
        self.status, self.reason = "failed", why
        return self.status


def daily_pnl(d: pd.DataFrame, start, rule: dict, risk: float = RISK) -> list[dict]:
    """Per-day worst / closing P&L of the trend strategy from `start` on (same fills, stops and costs as
    gold_prop.account: one position at a time, lots = risk x size / stop distance, whole grams)."""
    o, h, lo, c = (d[k].values for k in ("open", "high", "low", "close"))
    s0 = int(np.searchsorted(d.index.values, np.datetime64(pd.Timestamp(start))))
    by_entry = {}
    for t in gp.trades(d, "trend", first=max(210, s0 - 1)):   # a live signal enters on day one
        if t["entry"] >= s0:
            by_entry.setdefault(t["entry"], []).append(t)
    rows, open_t = [], None
    for day in range(s0, len(d)):
        if open_t is None and by_entry.get(day):
            t = by_entry[day][0]
            lots = max(1, int((risk * rule["size"]) // (abs(t["px_in"] - t["stop"]) or 1)))
            open_t = dict(t, lots=lots, mark=t["px_in"])
        worst = close = 0.0
        pos = 0
        if open_t is not None:
            s, q, ref = open_t["side"], open_t["lots"], open_t["mark"]
            adverse = lo[day] if s == 1 else h[day]
            if day == open_t["exit"] and open_t["why"] != "end":    # "end" = no exit yet, still open
                low_pt = open_t["px_out"] if open_t["why"] == "stop" else adverse
                worst = s * q * (low_pt - ref)
                close = s * q * (open_t["px_out"] - ref) - gp.COST * q * open_t["px_in"]
                open_t = None
            else:                                    # still open (a trade "ending" on the last bar is open)
                worst = s * q * (adverse - ref)
                close = s * q * (c[day] - ref)
                open_t["mark"] = c[day]
                pos = s * q
        rows.append(dict(date=str(d.index[day].date()), worst=float(worst), close=float(close), pos=int(pos)))
    return rows


def _rs(x: float) -> str:
    return f"Rs {x:,.0f}"


def _lines(key: str, ch: Challenge, pos: int) -> list[str]:
    head = f"{key} {NAMES[key]} {_rs(ch.size)}: {ch.status.upper()}"
    if ch.status != "active":
        return [head, f"  {ch.reason}"[:80]]
    daily, mx = ch.floors()
    gain = 100 * (ch.equity - ch.base) / ch.base
    side = "flat" if pos == 0 else (f"long {pos} g" if pos > 0 else f"short {-pos} g")
    out = [head, f"  equity {_rs(ch.equity)} ({gain:+.1f}%), target {_rs(ch.target())}",
           f"  floors: daily {_rs(daily)}, max loss {_rs(mx)}; {side}"]
    if len(RULES[key]["targets"]) > 1:
        out.append(f"  phase {ch.phase + 1} of {len(RULES[key]['targets'])}")
    if ch.note:
        out.append(f"  {ch.note}"[:80])
    return out


def paper(out: Path, d: pd.DataFrame, flags: Path | None = None, start: str | None = None,
          today: str | None = None) -> dict:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    sf = out / "state.json"
    old = json.loads(sf.read_text()) if sf.exists() else {}
    if flags and (Path(flags) / "KILL").exists():
        st = dict(old, status="killed", note="KILL flag present; no paper update")
        sf.write_text(json.dumps(st, indent=1))
        (out / "latest.txt").write_text("Gold challenge (PAPER ONLY): KILLED, no update.\n"
                                        "Remove paper/track-A/flags/KILL to resume.\n")
        return st
    d = d.dropna() if len(d) else d
    if len(d) < 230:
        st = dict(old, status="no-data", note=f"only {len(d)} clean daily bars")
        sf.write_text(json.dumps(st, indent=1))
        return st
    start = start or old.get("start") or str(today or d.index[-1].date())
    rows = daily_pnl(d, start, RULES["HF1"])
    res, text = {}, []
    for key, rule in RULES.items():
        ch = Challenge(rule)
        pos = 0
        for r in daily_pnl(d, start, rule) if key != "HF1" else rows:
            ch.day(r["date"], r["worst"], r["close"], flat=r["pos"] == 0)
            pos = r["pos"]
        res[key] = dict(status=ch.status, reason=ch.reason, note=ch.note, phase=ch.phase,
                        equity=round(ch.equity), trading_days=ch.days, last=ch.last)
        text += _lines(key, ch, pos)
    elapsed = (pd.Timestamp(today or date.today()) - pd.Timestamp(start)).days
    st = dict(status="running", start=start, today=str(today or date.today()), calendar_days=elapsed,
              paper_days_needed=PAPER_DAYS, risk=RISK, last_bar=str(d.index[-1].date()), rules=res)
    sf.write_text(json.dumps(st, indent=1))
    hdr = [f"Gold trend vs prop rules, PAPER ONLY (no fee, no orders)",
           f"Day {max(elapsed, 0)} of {PAPER_DAYS} since {start}; last bar {st['last_bar']}"]
    (out / "latest.txt").write_text("\n".join(hdr + text) + "\n")
    return st


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--paper", default="paper/gold-challenge")
    ap.add_argument("--flags", default=None)
    ap.add_argument("--start", default=None, help="paper start date (first run only; then kept in state.json)")
    a = ap.parse_args(argv)
    flags = Path(a.flags) if a.flags else None
    d = pd.DataFrame() if flags and (flags / "KILL").exists() else gp.load()
    st = paper(Path(a.paper), d, flags=flags, start=a.start)
    p = Path(a.paper) / "latest.txt"
    print(p.read_text() if p.exists() else json.dumps(st))
    return 0


if __name__ == "__main__":
    sys.exit(main())

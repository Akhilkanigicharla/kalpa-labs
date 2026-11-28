"""A307: hourly gold strategies vs the prop-firm rules (paper research, no tips, weak evidence).

Data: Yahoo GC=F 1-hour bars (Yahoo keeps only ~730 days of hourly data) priced as MCX Gold Petal
(1 gram per lot): GC x USD/INR (daily close, carried forward) / 31.1035. All times are UTC.

Rules, fixed BEFORE any result was seen (written 28 Nov 2026; common chart patterns, not copied from a
source, so their pedigree is "unverified"; K204 asks the free agents for a sourced version):
  breakout  Asian range = high/low of the bars that open 00:00-06:00 UTC (needs >= 5 bars). Signal bars
            07:00-15:00 UTC: first close above the range -> long, below -> short, entry at the next bar's
            open. Stop = the other side of the range. Target = 1.5 x the stop distance. One trade a day.
  pullback  EMA20 and EMA200 of hourly closes. Long when close > EMA200, EMA20 > EMA200, the bar's low
            touched EMA20 and it closed back above it; mirror for shorts. Signal bars 04:00-15:00 UTC
            (inside MCX hours), entry at the next open. Stop 1.5 x ATR14, target 2 x stop. Up to 2 trades
            a day, one at a time.
  both      Flat by the close of the 16:00 UTC bar (21:30-22:30 IST, before MCX closes), so every day
            ends flat. When stop and target sit inside one bar, the stop counts (conservative). Gaps fill
            at the open. Cost 0.04% of value per round trip (same as A305).
  random    Same number of trades per seed, same stop size (% of price), same target multiple and same
            exit time, on random days, random signal hours and random sides (20 seeds): the luck baseline.

Prop rules: Hindustan 1-Step and Greenwick 2-Step, checked by the same `Challenge` class the A306 paper
run uses (daily loss on the day's worst intraday point, max loss, targets, min days, consistency).
Lots = risk x account size / stop distance in rupees per gram (whole grams, at least 1).
Run: python3 research/hourly_gold_prop.py  (writes reports/hourly-gold-prop-<date>.md and .json)
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gold_challenge as gc  # noqa: E402

COST = 0.0004
RISKS = (0.005, 0.01)
SEEDS = 20
EXIT_HOUR = 16                      # last bar that may be held opens at 16:00 UTC
STRATS = {
    "breakout": dict(win=(7, 15), target_r=1.5, per_day=1),
    "pullback": dict(win=(4, 15), target_r=2.0, per_day=2),
}


def load() -> pd.DataFrame:
    import yfinance as yf

    def get(sym, **kw):
        d = yf.download(sym, progress=False, auto_adjust=False, **kw)
        if isinstance(d.columns, pd.MultiIndex):
            d.columns = d.columns.get_level_values(0)
        return d
    g = get("GC=F", period="730d", interval="1h")
    u = get("USDINR=X", period="3y")
    return to_inr(g, u["Close"])


def to_inr(g: pd.DataFrame, usdinr: pd.Series) -> pd.DataFrame:
    """Hourly GC (USD/oz) -> INR per gram, UTC index, bad rows dropped."""
    g = g.copy()
    g.index = pd.DatetimeIndex(g.index).tz_convert("UTC") if g.index.tz is not None else pd.DatetimeIndex(g.index).tz_localize("UTC")
    fx = usdinr.copy()
    fx.index = pd.DatetimeIndex(fx.index).tz_localize(None).normalize()
    k = fx.reindex(g.index.tz_localize(None).normalize(), method="ffill").values / 31.1035
    d = pd.DataFrame({c: g[c.capitalize()].values * k for c in ("open", "high", "low", "close")}, index=g.index).dropna()
    d = d[(d > 0).all(axis=1)]
    d["high"] = d[["open", "high", "low", "close"]].max(axis=1)
    d["low"] = d[["open", "high", "low", "close"]].min(axis=1)
    return d


def _days(idx: pd.DatetimeIndex) -> np.ndarray:
    """UTC day number per bar (works for any datetime resolution: s, ms or ns)."""
    return idx.tz_convert("UTC").tz_localize(None).values.astype("datetime64[D]").astype(np.int64)


def _ema(x: pd.Series, n: int) -> np.ndarray:
    return x.ewm(span=n, adjust=False).mean().values


def _atr(d: pd.DataFrame, n: int = 14) -> np.ndarray:
    pc = d["close"].shift(1)
    tr = pd.concat([d["high"] - d["low"], (d["high"] - pc).abs(), (d["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean().values


def _walk(d, e, side, stop, target, last):
    """Hold from bar e (entry at its open) to bar `last` at most. Stop before target inside a bar."""
    o, h, lo, c = (d[k].values for k in ("open", "high", "low", "close"))
    for j in range(e, last + 1):
        if (side == 1 and lo[j] <= stop) or (side == -1 and h[j] >= stop):
            return j, (min(o[j], stop) if side == 1 else max(o[j], stop)), "stop"
        if (side == 1 and h[j] >= target) or (side == -1 and lo[j] <= target):
            return j, (max(o[j], target) if side == 1 else min(o[j], target)), "target"
    return last, c[last], "time"


def _last_bar(day_idx: np.ndarray, hours: np.ndarray, e: int) -> int:
    """Index of the last bar on entry bar e's UTC day that opens at or before EXIT_HOUR."""
    j = e
    while j + 1 < len(hours) and day_idx[j + 1] == day_idx[e] and hours[j + 1] <= EXIT_HOUR:
        j += 1
    return j


def trades(d: pd.DataFrame, name: str) -> list[dict]:
    """Trade list for one fixed strategy. Signals use only closed bars; entry at the next bar's open."""
    p = STRATS[name]
    o, h, lo, c = (d[k].values for k in ("open", "high", "low", "close"))
    hours = d.index.hour.values
    day_idx = _days(d.index)
    out, busy_to, per_day = [], -1, {}
    if name == "pullback":
        e20, e200, a = _ema(d["close"], 20), _ema(d["close"], 200), _atr(d)
    rng_hi = rng_lo = None
    cur = None
    for i in range(len(d) - 1):
        if day_idx[i] != cur:                                  # new UTC day: build the Asian range
            cur = day_idx[i]
            m = (day_idx == cur) & (hours <= 6)
            rng_hi, rng_lo = (h[m].max(), lo[m].min()) if m.sum() >= 5 else (None, None)
        if i <= busy_to or not (p["win"][0] <= hours[i] <= p["win"][1]) or per_day.get(cur, 0) >= p["per_day"]:
            continue
        e = i + 1
        if day_idx[e] != cur or hours[e] > EXIT_HOUR:
            continue
        side = 0
        if name == "breakout" and rng_hi is not None:
            side = 1 if c[i] > rng_hi else (-1 if c[i] < rng_lo else 0)
            stop = rng_lo if side == 1 else rng_hi
        elif name == "pullback" and i >= 200 and np.isfinite(a[i]):
            if c[i] > e200[i] and e20[i] > e200[i] and lo[i] <= e20[i] < c[i]:
                side = 1
            elif c[i] < e200[i] and e20[i] < e200[i] and h[i] >= e20[i] > c[i]:
                side = -1
            stop = o[e] - side * 1.5 * a[i]
        if side == 0:
            continue
        dist = abs(o[e] - stop)
        if dist <= 0 or (side == 1 and stop >= o[e]) or (side == -1 and stop <= o[e]):
            continue                                           # gapped through the stop at entry: skip
        target = o[e] + side * p["target_r"] * dist
        j, px, why = _walk(d, e, side, stop, target, _last_bar(day_idx, hours, e))
        out.append({"entry": e, "exit": j, "side": side, "px_in": o[e], "px_out": px, "stop": stop,
                    "target": target, "why": why, "day": int(cur)})
        per_day[cur] = per_day.get(cur, 0) + 1
        if name == "breakout":
            per_day[cur] = p["per_day"]                        # the first break of the day only
        busy_to = j
    return out


def random_like(d: pd.DataFrame, like: list[dict], name: str, seed: int) -> list[dict]:
    """Luck baseline: same count, stop % and target multiple; random day, signal hour and side."""
    rng = np.random.default_rng(seed)
    p = STRATS[name]
    hours = d.index.hour.values
    day_idx = _days(d.index)
    ok = np.where((hours >= p["win"][0]) & (hours <= p["win"][1]))[0]
    ok = ok[(ok + 1 < len(d))]
    ok = ok[(day_idx[ok + 1] == day_idx[ok]) & (hours[ok + 1] <= EXIT_HOUR)]
    o = d["open"].values
    out = []
    for t in like:
        i = int(rng.choice(ok))
        e, side = i + 1, int(rng.choice([1, -1]))
        dist = abs(t["px_in"] - t["stop"]) / t["px_in"] * o[e]
        stop, target = o[e] - side * dist, o[e] + side * p["target_r"] * dist
        j, px, why = _walk(d, e, side, stop, target, _last_bar(day_idx, hours, e))
        out.append({"entry": e, "exit": j, "side": side, "px_in": o[e], "px_out": px, "stop": stop,
                    "target": target, "why": why, "day": int(day_idx[i])})
    out.sort(key=lambda t: t["entry"])
    kept, busy = [], -1                                        # one position at a time, like the real book
    for t in out:
        if t["entry"] > busy:
            kept.append(t)
            busy = t["exit"]
    return kept


def daily_book(d: pd.DataFrame, tl: list[dict], size: float, risk: float) -> dict[int, tuple[float, float]]:
    """Per UTC day: (worst intraday P&L, closing P&L) in rupees for this trade list. Days end flat."""
    h, lo = d["high"].values, d["low"].values
    book = {}
    for t in tl:
        q = max(1, int((risk * size) // abs(t["px_in"] - t["stop"])))
        s, done = t["side"], book.get(t["day"], (0.0, 0.0))[1]
        worst = done
        for j in range(t["entry"], t["exit"] + 1):
            adverse = t["px_out"] if (j == t["exit"] and t["why"] == "stop") else (lo[j] if s == 1 else h[j])
            if j == t["exit"] and t["why"] != "stop":
                adverse = min(adverse, t["px_out"]) if s == 1 else max(adverse, t["px_out"])
            worst = min(worst, done + s * q * (adverse - t["px_in"]))
        pnl = s * q * (t["px_out"] - t["px_in"]) - COST * q * t["px_in"]
        prev_worst = book.get(t["day"], (0.0, 0.0))[0]
        book[t["day"]] = (min(prev_worst, worst, done + pnl), done + pnl)
    return book


def run_challenge(days: list[int], book: dict, rule: dict) -> tuple[str, int]:
    ch = gc.Challenge(rule)
    for n, dy in enumerate(days, 1):
        w, c = book.get(dy, (0.0, 0.0))
        if ch.day(str(dy), w, c, flat=True) != "active":
            return ch.status, n
    return "unfinished", len(days)


def evaluate(d: pd.DataFrame, tl: list[dict], rule: dict, risk: float, step: int = 5) -> dict:
    days = sorted(set(_days(d.index).tolist()))
    book = daily_book(d, tl, rule["size"], risk)
    starts = days[15:-20:step]                                 # 15 days of EMA warm-up, 20 left to trade
    res, took = [], []
    for k, s in enumerate(starts):
        st, n = run_challenge(days[days.index(s):], book, rule)
        res.append(st)
        if st == "passed":
            took.append(n)
    r = np.array(res)
    return {"starts": len(starts), "pass": round(float((r == "passed").mean()), 3),
            "fail": round(float((r == "failed").mean()), 3), "unfinished": round(float((r == "unfinished").mean()), 3),
            "median_days_to_pass": float(np.median(took)) if took else None}


def stats(tl: list[dict]) -> dict:
    if not tl:
        return {"trades": 0}
    r = np.array([t["side"] * (t["px_out"] - t["px_in"]) / abs(t["px_in"] - t["stop"]) - COST * t["px_in"] / abs(t["px_in"] - t["stop"]) for t in tl])
    win, loss = r[r > 0].sum(), -r[r < 0].sum()
    return {"trades": len(tl), "win_rate": round(float((r > 0).mean()), 3), "avg_r": round(float(r.mean()), 3),
            "total_r": round(float(r.sum()), 1), "profit_factor": round(float(win / loss), 2) if loss else None}


def main() -> int:
    d = load()
    out = {"data": {"bars": len(d), "from": str(d.index[0]), "to": str(d.index[-1])}, "stats": {}, "prop": {}}
    for name in STRATS:
        tl = trades(d, name)
        rnd = [random_like(d, tl, name, s) for s in range(SEEDS)]
        out["stats"][name] = stats(tl)
        out["stats"][f"{name}|random"] = {k: round(float(np.mean([stats(x)[k] or 0 for x in rnd])), 3) for k in ("trades", "win_rate", "avg_r", "total_r")}
        for rk, rule in gc.RULES.items():
            for risk in RISKS:
                out["prop"][f"{rk}|{name}|{risk}"] = evaluate(d, tl, rule, risk)
                rr = [evaluate(d, x, rule, risk) for x in rnd]
                out["prop"][f"{rk}|{name}|random|{risk}"] = {k: round(float(np.mean([x[k] for x in rr])), 3) for k in ("pass", "fail", "unfinished")}
    today = date.today().isoformat()
    rep = Path(__file__).resolve().parents[1] / "reports"
    (rep / f"hourly-gold-prop-{today}.json").write_text(json.dumps(out, indent=1))
    (rep / f"hourly-gold-prop-{today}.md").write_text(report(out, today))
    print(json.dumps(out["stats"]))
    return 0


def report(out: dict, today: str) -> str:
    L = [f"# A307: hourly gold strategies vs prop rules ({today})", "",
         "**Weak evidence.** About 2 years of hourly data (Yahoo keeps no more), one market, two rule sets fixed "
         "before testing. Paper research only, no tips. Rules and method: `research/hourly_gold_prop.py` docstring.", "",
         f"Data: {out['data']['bars']} hourly bars, {out['data']['from'][:10]} to {out['data']['to'][:10]} (GC=F x USD/INR, INR per gram).", "",
         "## The edge itself (per trade, in R = multiples of the risk)", "",
         "| Book | Trades | Win rate | Avg R | Total R | Profit factor |", "|---|---|---|---|---|---|"]
    for k, s in out["stats"].items():
        L.append(f"| {k} | {s.get('trades')} | {s.get('win_rate')} | {s.get('avg_r')} | {s.get('total_r')} | {s.get('profit_factor', '-')} |")
    L += ["", "Random rows are the average of 20 seeds (same trade count, stop size, target and exit time; random day, hour and side).", "",
          "## Prop challenge (a fresh attempt every 5th trading day)", "",
          "| Firm | Book | Risk | Pass | Fail | Unfinished | Median days to pass | Random pass | Random fail |",
          "|---|---|---|---|---|---|---|---|---|"]
    for k, v in out["prop"].items():
        if "|random|" in k:
            continue
        firm, name, risk = k.split("|")
        rv = out["prop"][f"{firm}|{name}|random|{risk}"]
        L.append(f"| {gc.NAMES[firm]} | {name} | {float(risk):.1%} | {v['pass']:.0%} | {v['fail']:.0%} | {v['unfinished']:.0%} | "
                 f"{v['median_days_to_pass'] if v['median_days_to_pass'] is not None else '-'} | {rv['pass']:.0%} | {rv['fail']:.0%} |")
    L += ["", "## Verdict", ""]
    for name in STRATS:
        s = out["stats"][name]
        good = s.get("avg_r", 0) > 0.05 and (s.get("profit_factor") or 0) > 1.1
        L.append(f"- **{name}**: " + ("small edge in this window; needs a longer paper run before any money." if good else
                 f"no edge (avg {s.get('avg_r')} R a trade, profit factor {s.get('profit_factor')} after costs). Beating the random "
                 "row only shows the rules lose less than coin flips; a prop pass here would be luck, so it is not kept."))
    L += ["", "## How to read it", "",
          "- Random books hold fewer trades than the real ones because overlapping random trades are dropped (one position at a time).",
          "- A book only beats luck if its pass rate is clearly above the random row at the same risk AND its average R is above 0.",
          "- 'Unfinished' = the 2-year window ended before a pass or fail; late starts have little time, so pass rates are a floor.",
          "- Costs ignore the MCX import-duty premium and overnight funding (every day ends flat). Bots are banned at Hindustan "
          "and need written approval at Greenwick (A305), so any use is signals only.",
          "- Two years of one instrument cannot prove an edge. Treat a good result as a reason for a longer paper run, not for money."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())

"""A302: Can a gold strategy pass an Indian MCX prop-firm challenge? (Akhil, 21 Nov 2026). Research only.

Question: Akhil wants a gold bot that passes a ₹1 lakh (100k INR) funded-account challenge bought with his
₹10k, then earns from the funded account. This script answers with data, before any money is spent.

Prop rules modelled (read from the firms' own pages, 21 Nov 2026; see research/gold-prop-2026-11-21.md):
  HF1  Hindustan Funded 1-Step, ₹1,00,000, fee ₹4,599: target +10%; daily loss 5% of the day's opening
       balance; max loss 10% TRAILING from the equity high-water mark; min 5 trading days; consistency:
       no single day > 20% of total profit at the pass; bots banned (so the bot only gives signals).
  GW2  Greenwick 2-Step, ₹2,00,000, fee ₹3,499 (launch offer): +8% then +5%; daily 5%; max loss 10% STATIC
       from the start; bots banned unless Greenwick approves in writing.
Gold: MCX Gold Petal (1 gram per lot) priced from COMEX gold (GC=F) x USD/INR / 31.1035 (Yahoo daily).
  This ignores the import-duty premium (a level shift, not a change in daily moves; a duty CUT gaps MCX
  down, as in July 2024, and that gap is in the data only through the fx/price path, so treat it as a caveat).
Costs: 0.04% of value per round trip (brokerage, exchange, CTT 0.01% on sells, 1 tick slippage each side).

Strategies (fixed BEFORE any result was seen; long AND short, MCX futures allow both):
  trend    close > SMA50 and SMA20 > SMA50 -> long; mirror -> short; stop 2 ATR; exit when the signal flips
  donchian break of the 20-day high/low -> long/short; stop 2 ATR; exit on the opposite 10-day channel
  revert   RSI(2) < 10 above SMA200 -> long, RSI(2) > 90 below SMA200 -> short; exit on SMA5 cross; stop 2 ATR
  random   same number of trades, same holding days and stop distance as trend, random days and sides
           (the honest baseline: what pure luck does under the same rules)
Risk per trade: 0.5%, 1%, 2% and 3% of the starting balance (lots = risk / stop distance, whole grams, at least 1).

Method: start a fresh challenge on every 5th trading day of the TEST years (2016-11 .. 2026-11; the rules
were set without looking at any year), run it until pass, fail, or 750 trading days (no time limit at either firm). Daily loss and the
drawdown use each day's adverse extreme (low for longs, high for shorts) to stay conservative.
Then the money: expected ₹ per attempt = P(pass) x average 80% split of funded profits over the next
6 months (payout every 14 days, stop at the first breach) - fee.

Run: cd 07-trading && python3 research/gold_prop.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

COST = 0.0004
TEST_START = "2016-11-21"
RISKS = (0.005, 0.01, 0.02, 0.03)          # share of the starting balance risked per trade


def load() -> pd.DataFrame:
    import yfinance as yf

    def get(s):
        d = yf.download(s, start="2005-01-01", auto_adjust=False, progress=False)
        if isinstance(d.columns, pd.MultiIndex):
            d.columns = d.columns.get_level_values(0)
        return d
    g, u = get("GC=F"), get("USDINR=X")
    fx = u["Close"].reindex(g.index).ffill()
    k = fx / 31.1035
    df = pd.DataFrame({c: g[c.capitalize()] * k for c in ("open", "high", "low", "close")}).dropna()
    df = df[(df > 0).all(axis=1)]
    df["high"] = df[["open", "high", "low", "close"]].max(axis=1)
    df["low"] = df[["open", "high", "low", "close"]].min(axis=1)
    return df


def atr(d, n=14):
    pc = d.close.shift()
    tr = pd.concat([d.high - d.low, (d.high - pc).abs(), (d.low - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def rsi(c, n=2):
    x = c.diff()
    up = x.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-x.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)


def signals(d: pd.DataFrame, name: str) -> tuple[np.ndarray, np.ndarray]:
    """Desired side for the NEXT day (+1/-1/0) known at each close, and the exit flag."""
    c = d.close
    if name == "trend":
        s20, s50 = c.rolling(20).mean(), c.rolling(50).mean()
        side = np.where((c > s50) & (s20 > s50), 1, np.where((c < s50) & (s20 < s50), -1, 0))
        return side, side == 0
    if name == "donchian":
        hi20, lo20 = d.high.rolling(20).max().shift(), d.low.rolling(20).min().shift()
        hi10, lo10 = d.high.rolling(10).max().shift(), d.low.rolling(10).min().shift()
        side = np.where(c > hi20, 1, np.where(c < lo20, -1, 0))
        ex = np.zeros(len(d), dtype=int)                      # 1 = exit longs, -1 = exit shorts
        ex = np.where(c < lo10, 1, np.where(c > hi10, -1, 0))
        return side, ex
    if name == "revert":
        r, s200, s5 = rsi(c), c.rolling(200).mean(), c.rolling(5).mean()
        side = np.where((r < 10) & (c > s200), 1, np.where((r > 90) & (c < s200), -1, 0))
        ex = np.where(c > s5, 1, np.where(c < s5, -1, 0))     # long exits above SMA5, short below
        return side, ex
    raise ValueError(name)


def trades(d: pd.DataFrame, name: str, seed: int = 0, like: list | None = None) -> list[dict]:
    """Trade list on the full history. Entry at the next open after a signal; stop 2 ATR checked on the
    day's range (stop first); exits at the close of the exit signal day. No look-ahead."""
    o, h, lo, c = (d[k].values for k in ("open", "high", "low", "close"))
    a = atr(d).values
    out = []
    if name == "random":
        rng = np.random.default_rng(seed)
        n = len(d)
        for t in like:
            i = int(rng.integers(260, n - 30))
            side = int(rng.choice([1, -1]))
            hold = t["exit"] - t["entry"]
            stop_d = t["stop_dist_pct"] * o[i]
            out.append(_run(o, h, lo, c, i, side, stop_d, max_hold=max(1, hold)))
        return [t for t in out if t]
    side, ex = signals(d, name)
    i = 210
    while i < len(d) - 1:
        s = int(side[i])
        if s == 0 or not np.isfinite(a[i]):
            i += 1
            continue
        e = i + 1
        stop_d = 2 * a[i]
        j, px, why = e, None, "end"
        for j in range(e, len(d)):
            stop = o[e] - s * stop_d
            if (s == 1 and lo[j] <= stop) or (s == -1 and h[j] >= stop):
                px, why = (min(o[j], stop) if s == 1 else max(o[j], stop)), "stop"
                break
            exit_now = (ex[j] if isinstance(ex[j], (bool, np.bool_)) else (ex[j] == s)) or (name == "trend" and side[j] == -s)
            if exit_now and j > e - 1:
                px, why = c[j], "signal"
                break
        if px is None:
            px = c[j]
        out.append({"entry": e, "exit": j, "side": s, "px_in": o[e], "px_out": px, "stop": o[e] - s * stop_d,
                    "stop_dist_pct": stop_d / o[e], "why": why})
        i = j + 1
    return out


def _run(o, h, lo, c, i, s, stop_d, max_hold):
    stop = o[i] - s * stop_d
    for j in range(i, min(i + max_hold, len(o) - 1) + 1):
        if (s == 1 and lo[j] <= stop) or (s == -1 and h[j] >= stop):
            return {"entry": i, "exit": j, "side": s, "px_in": o[i], "px_out": (min(o[j], stop) if s == 1 else max(o[j], stop)),
                    "stop": stop, "stop_dist_pct": stop_d / o[i], "why": "stop"}
    j = min(i + max_hold, len(o) - 1)
    return {"entry": i, "exit": j, "side": s, "px_in": o[i], "px_out": c[j], "stop": stop, "stop_dist_pct": stop_d / o[i], "why": "time"}


RULES = {
    "HF1": dict(size=100_000, fee=4_599, targets=[0.10], daily=0.05, maxdd=0.10, trailing=True, min_days=5, consistency=0.20),
    "GW2": dict(size=200_000, fee=3_499, targets=[0.08, 0.05], daily=0.05, maxdd=0.10, trailing=False, min_days=0, consistency=None),
}


def account(d, tl, start, rule, risk, max_days=750, funded=False):
    """Run one account from day `start`. Returns ('pass'|'fail'|'timeout', days, balance path info)."""
    o, h, lo, c = (d[k].values for k in ("open", "high", "low", "close"))
    size = rule["size"]
    bal = size
    hwm = size
    phase, base = 0, size
    day_pnl = []
    by_entry = {}
    for t in tl:
        if t["entry"] >= start:
            by_entry.setdefault(t["entry"], []).append(t)
    open_t = []
    end = min(start + max_days, len(d) - 1)
    payouts, last_pay = 0.0, start
    for day in range(start, end + 1):
        day_open_bal = bal
        if not open_t:                                          # one position at a time
            for t in by_entry.get(day, []):
                lots = max(1, int((risk * size) // (abs(t["px_in"] - t["stop"]) or 1)))
                open_t.append(dict(t, lots=lots))
                break
        realised, worst = 0.0, 0.0
        still = []
        for t in open_t:
            s, q = t["side"], t["lots"]
            ref = t.get("mark", t["px_in"])
            adverse = lo[day] if s == 1 else h[day]
            if day == t["exit"]:
                # closed today: at a stop the loss stops at the stop price; on a signal exit the day's worst counts
                low_pt = t["px_out"] if t["why"] == "stop" else adverse
                worst += s * q * (low_pt - ref)
                realised += s * q * (t["px_out"] - ref) - COST * q * t["px_in"]
            else:
                worst += s * q * (adverse - ref)
                realised += s * q * (c[day] - ref)
                t["mark"] = c[day]
                still.append(t)
        open_t = still
        # daily loss and drawdown on the day's worst point (conservative)
        if day_open_bal + min(worst, realised) - day_open_bal < -rule["daily"] * day_open_bal:
            return "fail", day - start, payouts
        floor = (hwm if rule["trailing"] else size) - rule["maxdd"] * size
        if day_open_bal + min(worst, realised) < floor:
            return "fail", day - start, payouts
        bal += realised
        day_pnl.append(realised)
        hwm = max(hwm, bal)
        if funded:
            if day - last_pay >= 10 and bal > size:            # ~14 calendar days
                payouts += 0.8 * (bal - size)
                bal = size
                hwm = size
                last_pay = day
            continue
        target = base * (1 + rule["targets"][phase])
        if bal >= target and not open_t and len(day_pnl) >= rule["min_days"]:
            prof = bal - base
            if rule["consistency"] and max(day_pnl) > rule["consistency"] * prof:
                continue                                       # keep trading until no single day is > 20%
            phase += 1
            if phase == len(rule["targets"]):
                return "pass", day - start, payouts
            bal = base = size
            hwm = size
            day_pnl = []
    return ("timeout" if not funded else "funded-end"), end - start, payouts


def evaluate(d, tl, rule, risk):
    idx = np.where(d.index >= TEST_START)[0]
    starts = idx[:-60:5]
    res, ev_pay, days = [], [], []
    for s in starts:
        r, n, _ = account(d, tl, s, rule, risk)
        res.append(r)
        if r == "pass":
            days.append(n)
            _, _, pay = account(d, tl, min(s + n + 1, len(d) - 2), rule, risk, max_days=125, funded=True)
            ev_pay.append(pay)
    res = np.array(res)
    p = float((res == "pass").mean())
    avg_pay = float(np.mean(ev_pay)) if ev_pay else 0.0
    return {"starts": len(starts), "pass": round(p, 3), "fail": round(float((res == "fail").mean()), 3),
            "timeout": round(float((res == "timeout").mean()), 3), "median_days_to_pass": float(np.median(days)) if days else None,
            "avg_6m_payout_if_passed": round(avg_pay), "ev_per_attempt_rs": round(p * avg_pay - rule["fee"])}


def main() -> int:
    d = load()
    out, lines = {}, []
    base_trend = trades(d, "trend")
    books = {"trend": base_trend, "donchian": trades(d, "donchian"), "revert": trades(d, "revert")}
    rnd = [trades(d, "random", seed=s, like=base_trend) for s in range(5)]
    for rname, rule in RULES.items():
        for risk in RISKS:
            for name, tl in books.items():
                out[f"{rname}|{name}|{risk}"] = evaluate(d, tl, rule, risk)
            rr = [evaluate(d, t, rule, risk) for t in rnd]
            out[f"{rname}|random|{risk}"] = {k: (round(float(np.mean([x[k] for x in rr if x[k] is not None])), 3) if any(x[k] is not None for x in rr) else None) for k in rr[0]}
    # plain strategy stats (test years) so the edge itself is visible
    stats = {}
    t0 = int(np.where(d.index >= TEST_START)[0][0])
    for name, tl in {**books, "random": rnd[0]}.items():
        r = np.array([t["side"] * (t["px_out"] / t["px_in"] - 1) - COST for t in tl if t["entry"] >= t0])
        stats[name] = {"trades": int(len(r)), "win": round(float((r > 0).mean()), 3) if len(r) else 0,
                       "avg_ret_pct": round(float(r.mean() * 100), 3) if len(r) else 0, "sum_ret_pct": round(float(r.sum() * 100), 1)}
    rep = Path(__file__).resolve().parents[1] / "reports"
    rep.mkdir(exist_ok=True)
    day = d.index[-1].date()
    (rep / f"gold-prop-{day}.json").write_text(json.dumps({"challenge": out, "strategy": stats}, indent=1))
    lines = [f"# Gold vs Indian prop-firm rules — {day} (research only)", "",
             "## Plain strategy results, test years 2016-11..2026-11 (per trade, after 0.04% costs)", "",
             "| Strategy | Trades | Win % | Avg per trade | Sum |", "|---|---|---|---|---|"]
    for k, v in stats.items():
        lines.append(f"| {k} | {v['trades']} | {v['win']:.0%} | {v['avg_ret_pct']:+.2f}% | {v['sum_ret_pct']:+.0f}% |")
    lines += ["", "## Challenge simulation (fresh start every 5th trading day, 2016-11..2026-11)", "",
              "| Firm/plan | Risk/trade | Strategy | Pass | Fail | Still running at 750 days | Median days to pass | Avg 6-month payout if passed (₹) | Expected ₹ per attempt (after fee) |",
              "|---|---|---|---|---|---|---|---|---|"]
    for k, v in out.items():
        f, s, r = k.split("|")
        lines.append(f"| {f} | {float(r):.1%} | {s} | {v['pass']:.0%} | {v['fail']:.0%} | {v['timeout']:.0%} | {v['median_days_to_pass']} | {v['avg_6m_payout_if_passed']} | {v['ev_per_attempt_rs']} |")
    lines += ["", "HF1 = Hindustan Funded ₹1 lakh 1-Step (fee ₹4,599; trailing 10%; 20% consistency rule). "
              "GW2 = Greenwick ₹2 lakh 2-Step (fee ₹3,499 launch offer; static 10%).",
              "Random = same trade count, holding time and stop size as trend, random days and sides (5 seeds). "
              "Not investment advice."]
    (rep / f"gold-prop-{day}.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

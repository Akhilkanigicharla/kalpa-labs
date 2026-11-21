"""A308: Akhil's gold plan as a testable bot (21 Nov 2026).

Akhil: "Gold sell trade bot until 3100 and from there buy trade strategy using 9ema
and malaysia strategy (MSNR)".

Rules (fixed before any result was seen):
  bias    (the $3,100 level rule was removed 21 Nov 2026 on Akhil's request, A322)
          both   - both sides, no level (tests the 9 EMA + MSNR trigger alone)
          ema_d  - side = direction of the DAILY 9 EMA (data-driven bias, for comparison)
  trigger short: close < EMA9, EMA9 falling, and the bar's high wicks into a FRESH MSNR
          resistance (A level from closes, or a V level that flipped) and closes back below it.
          long: the mirror image on fresh support. First touch only (MSNR "fresh" rule).
  entry   next bar's open.  stop: beyond the wick + 0.25 ATR.  target: 2R.  max hold H bars.
  costs   $0.40 of gold price per round trip (MGC: ~$4/contract commission + 1 tick slippage).

Honesty checks: placebo trades (same side, same stop size in ATR, random bars) and a bootstrap
p-value; then Topstep 50K Trading Combine rules simulated on every weekly start.
Run:  python research/gold_ema9_msnr.py            (writes reports/gold-ema9-msnr-<date>.md/json)
      python research/gold_ema9_msnr.py --signal   (today's paper signal from the latest hourly bars)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.msnr import levels  # noqa: E402

COST = 0.40            # $ of gold price per round trip
RR = 2.0
ATR_BUF = 0.25
MGC_OZ = 10            # Micro Gold = 10 troy oz, so $1 move = $10 per contract
TOPSTEP_50K = dict(size=50_000, target=3_000, mll=2_000, consistency=0.50, max_micro=50,
                   monthly=49 + 29, activation=149)  # $49 Combine + $29 TopstepX API


def ema(c: pd.Series, n: int = 9) -> pd.Series:
    return c.ewm(span=n, adjust=False).mean()


def atr(d: pd.DataFrame, n: int = 14) -> np.ndarray:
    pc = d.close.shift()
    tr = pd.concat([d.high - d.low, (d.high - pc).abs(), (d.low - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=n).mean().values


def clean(df: pd.DataFrame) -> pd.DataFrame:
    d = df.rename(columns=str.lower)[["open", "high", "low", "close"]].astype(float).dropna()
    d["high"] = d[["open", "high", "low", "close"]].max(axis=1)     # repair bad high/low prints
    d["low"] = d[["open", "high", "low", "close"]].min(axis=1)
    r = d.close.pct_change().abs()
    return d[~(r > 0.15)]                                          # drop >15% one-bar spikes


def bias_series(d: pd.DataFrame, mode: str, daily_ema_up: pd.Series | None = None) -> np.ndarray:
    """+1 long only, -1 short only, 0 both sides."""
    if mode == "both":
        return np.zeros(len(d), dtype=int)
    if mode == "ema_d":
        idx = d.index.tz_localize(None) if d.index.tz is not None else d.index
        up = daily_ema_up.shift(1).reindex(pd.DatetimeIndex(idx).normalize(), method="ffill")
        return np.where(up.fillna(True).astype(bool).values, 1, -1)   # yesterday's EMA: no look-ahead
    raise ValueError(mode)


def setups(d: pd.DataFrame, bias: np.ndarray, k: int = 2) -> list[dict]:
    """Signals decided on bar t's close; trade fills at t+1 open. No look-ahead:
    a level is usable only from the bar after it is known."""
    o, h, lo, c = (d[x].values for x in ("open", "high", "low", "close"))
    e = ema(d.close).values
    a = atr(d)
    lv = sorted(levels(d, k), key=lambda x: x.known_at)
    act: list[list] = []                      # [price, role(+1 support/-1 resistance), fresh]
    j, out = 0, []
    for t in range(15, len(d) - 1):
        while j < len(lv) and lv[j].known_at < t:
            act.append([lv[j].price, 1 if lv[j].kind == "V" else -1, True])
            j += 1
        if np.isnan(a[t]):
            continue
        sig = None
        for L in act:
            p, role, fresh = L
            if role == -1:                                     # resistance
                if c[t] > p:
                    L[1], L[2] = 1, True                       # flip to fresh support (RBS)
                    continue
                if h[t] >= p:
                    if fresh and sig is None and bias[t] <= 0 and c[t] < e[t] and e[t] < e[t - 1]:
                        sig = dict(t=t, side=-1, stop=max(h[t], p) + ATR_BUF * a[t], level=p)
                    L[2] = False
            else:                                              # support
                if c[t] < p:
                    L[1], L[2] = -1, True                      # flip to fresh resistance (SBR)
                    continue
                if lo[t] <= p:
                    if fresh and sig is None and bias[t] >= 0 and c[t] > e[t] and e[t] > e[t - 1]:
                        sig = dict(t=t, side=1, stop=min(lo[t], p) - ATR_BUF * a[t], level=p)
                    L[2] = False
        if len(act) > 400:
            act = act[-400:]
        if sig:
            sig["atr"] = a[t]
            out.append(sig)
    return out


def run(d: pd.DataFrame, sig: list[dict], hold: int, rr: float = RR, cost: float = COST) -> pd.DataFrame:
    """One position at a time. Stop checked before target inside a bar (worst case)."""
    o, h, lo, c = (d[x].values for x in ("open", "high", "low", "close"))
    rows, busy = [], -1
    for s in sig:
        i = s["t"] + 1
        if i <= busy or i >= len(d):
            continue
        side, en, st = s["side"], o[i], s["stop"]
        risk = (en - st) * side
        if risk <= 0.05 * s["atr"]:                       # gapped through the stop: skip
            continue
        tp = en + side * rr * risk
        out_px, why, k = c[min(i + hold, len(d) - 1)], "time", min(i + hold, len(d) - 1)
        worst = en
        for k2 in range(i, min(i + hold + 1, len(d))):
            if side == 1:
                if lo[k2] <= st:
                    out_px, why, k = min(st, o[k2]) if k2 > i else st, "stop", k2
                    break
                if h[k2] >= tp:
                    out_px, why, k = max(tp, o[k2]) if k2 > i else tp, "target", k2
                    break
                worst = min(worst, lo[k2])
            else:
                if h[k2] >= st:
                    out_px, why, k = max(st, o[k2]) if k2 > i else st, "stop", k2
                    break
                if lo[k2] <= tp:
                    out_px, why, k = min(tp, o[k2]) if k2 > i else tp, "target", k2
                    break
                worst = max(worst, h[k2])
        if why == "stop":
            worst = out_px
        pnl = (out_px - en) * side - cost
        rows.append(dict(t_in=d.index[i], t_out=d.index[k], side=side, entry=en, stop=st, exit=out_px,
                         why=why, risk=risk, R=pnl / risk, adverse=(worst - en) * side))
        busy = k
    return pd.DataFrame(rows)


def placebo(d: pd.DataFrame, sig: list[dict], seed: int) -> list[dict]:
    """Same side and stop size (in ATR) at random bars: the 'no skill' benchmark."""
    rng = np.random.default_rng(seed)
    a = atr(d)
    c = d.close.values
    ok = np.where(~np.isnan(a))[0]
    ok = ok[(ok > 15) & (ok < len(d) - 2)]
    out = []
    for s in sig:
        t = int(rng.choice(ok))
        dist = abs(c[s["t"]] - s["stop"]) / s["atr"] * a[t]
        out.append(dict(t=t, side=s["side"], stop=c[t] - s["side"] * dist, atr=a[t], level=np.nan))
    return sorted(out, key=lambda x: x["t"])


def stats(tr: pd.DataFrame) -> dict:
    if tr.empty:
        return dict(n=0)
    r = tr.R.values
    w = r[r > 0].sum()
    lsum = -r[r < 0].sum()
    return dict(n=int(len(r)), win=round(float((r > 0).mean()), 3), avg_r=round(float(r.mean()), 3),
                pf=round(float(w / lsum), 2) if lsum else None, total_r=round(float(r.sum()), 1),
                longs=int((tr.side == 1).sum()), shorts=int((tr.side == -1).sum()))


def honest(d, sig, hold, seeds=20) -> dict:
    real = run(d, sig, hold)
    s = stats(real)
    if real.empty:
        return dict(real=s)
    pl = [run(d, placebo(d, sig, k), hold).R.mean() for k in range(seeds)]
    rng = np.random.default_rng(7)
    boot = [rng.choice(real.R.values, len(real)).mean() for _ in range(2000)]
    s["placebo_avg_r"] = round(float(np.nanmean(pl)), 3)
    s["p_not_better"] = round(float(np.mean(np.array(boot) <= np.nanmean(pl))), 3)
    return dict(real=s, trades=real)


def topstep(trades: pd.DataFrame, start, risk_usd: float, rule=TOPSTEP_50K, max_days=120) -> dict:
    """Topstep 50K Combine: +$3,000 target, $2,000 MLL trailing the end-of-day balance high until
    it locks at the start balance, best day <= 50% of profit at pass, max 50 micro contracts.
    A loss that reaches the floor on the stop counts as a breach (worst case)."""
    tr = trades[(trades.t_in >= start) & (trades.t_in < start + pd.Timedelta(days=max_days))]
    bal = rule["size"]
    floor = bal - rule["mll"]
    eod_high = bal
    day_pnl: dict = {}
    last_day = None
    for _, x in tr.iterrows():
        day = (x.t_out - pd.Timedelta(hours=17)).date()        # Topstep day ends 5 pm CT (approx.)
        if last_day is not None and day != last_day:
            eod_high = max(eod_high, bal)
            floor = min(max(floor, eod_high - rule["mll"]), rule["size"])
        last_day = day
        qty = int(min(rule["max_micro"], risk_usd // (x.risk * MGC_OZ)))
        if qty < 1:
            continue
        if bal + x.adverse * MGC_OZ * qty <= floor:
            return dict(result="fail", days=(x.t_out - start).days)
        pnl = (x.R * x.risk) * MGC_OZ * qty
        bal += pnl
        day_pnl[day] = day_pnl.get(day, 0) + pnl
        prof = bal - rule["size"]
        if prof >= rule["target"] and max(day_pnl.values()) <= rule["consistency"] * prof:
            return dict(result="pass", days=(x.t_out - start).days)
    return dict(result="timeout", days=max_days)


def xfa(trades: pd.DataFrame, start, risk_usd: float, rule=TOPSTEP_50K, max_days=120) -> dict:
    """Express Funded Account after a pass (Standard Path): first payout needs 5 winning days of
    >= $150; payout = 50% of profit, 90% split. Breach = the same $2,000 trailing MLL."""
    tr = trades[(trades.t_in >= start) & (trades.t_in < start + pd.Timedelta(days=max_days))]
    bal, floor, eod_high, last_day, days = rule["size"], rule["size"] - rule["mll"], rule["size"], None, {}
    for _, x in tr.iterrows():
        day = (x.t_out - pd.Timedelta(hours=17)).date()
        if last_day is not None and day != last_day:
            eod_high = max(eod_high, bal)
            floor = min(max(floor, eod_high - rule["mll"]), rule["size"])
        last_day = day
        qty = int(min(rule["max_micro"], risk_usd // (x.risk * MGC_OZ)))
        if qty < 1:
            continue
        if bal + x.adverse * MGC_OZ * qty <= floor:
            return dict(result="breach", payout=0.0)
        pnl = x.R * x.risk * MGC_OZ * qty
        bal += pnl
        days[day] = days.get(day, 0) + pnl
        if sum(v >= 150 for v in days.values()) >= 5 and bal > rule["size"]:
            return dict(result="payout", payout=round(0.5 * (bal - rule["size"]) * 0.9, 0))
    return dict(result="timeout", payout=0.0)


def journey(trades: pd.DataFrame, risk_usd: float, first, last) -> dict:
    """Whole path per weekly start: Combine (pay monthly) -> activation -> first XFA payout.
    Net $ = payout - fees. This is the number that decides if the plan makes money."""
    starts = pd.date_range(first, last, freq="7D", tz=trades.t_in.dt.tz)
    nets, paid = [], 0
    for s in starts:
        c = topstep(trades, s, risk_usd)
        fees = max(1, np.ceil(c["days"] / 30)) * TOPSTEP_50K["monthly"]
        if c["result"] != "pass":
            nets.append(-fees)
            continue
        x = xfa(trades, s + pd.Timedelta(days=c["days"] + 1), risk_usd)
        fees += TOPSTEP_50K["activation"]
        paid += x["result"] == "payout"
        nets.append(x["payout"] - fees)
    n = np.array(nets)
    return dict(starts=len(n), first_payout_rate=round(paid / len(n), 2), avg_net_usd=round(float(n.mean()), 0),
                median_net_usd=round(float(np.median(n)), 0), best_usd=round(float(n.max()), 0))


def topstep_eval(trades: pd.DataFrame, risk_usd: float, first, last) -> dict:
    starts = pd.date_range(first, last, freq="7D", tz=trades.t_in.dt.tz)
    res = [topstep(trades, s, risk_usd) for s in starts]
    n = len(res)
    p = sum(r["result"] == "pass" for r in res) / n
    f = sum(r["result"] == "fail" for r in res) / n
    days = [r["days"] for r in res if r["result"] == "pass"]
    months = np.mean([max(1, np.ceil(r["days"] / 30)) for r in res])
    cost = months * TOPSTEP_50K["monthly"]
    return dict(starts=n, pass_rate=round(p, 2), fail_rate=round(f, 2),
                median_days_to_pass=int(np.median(days)) if days else None,
                avg_cost_usd_per_attempt=round(float(cost), 0),
                cost_usd_per_pass=round(float(cost / p), 0) if p else None)


PAPER_START = "2026-11-21"    # forward test only: no trade before this date counts


def paper(out: Path, trades: pd.DataFrame, flags: Path | None = None, today=None) -> dict:
    """Forward paper test of Akhil's rule against Topstep 50K. Recomputed from bars each run,
    so the ledger only holds trades whose entry bar is on/after PAPER_START. No orders are sent."""
    out.mkdir(parents=True, exist_ok=True)
    if flags and (flags / "KILL").exists():
        st = dict(status="killed", note="KILL flag present; no paper update")
        (out / "state.json").write_text(json.dumps(st, indent=1))
        return st
    t0 = pd.Timestamp(PAPER_START)
    t = trades.copy()
    naive = t.t_in.dt.tz_localize(None) if t.t_in.dt.tz is not None else t.t_in
    t = t[naive >= t0]
    t.to_csv(out / "ledger.csv", index=False)
    start = t0.tz_localize(trades.t_in.dt.tz) if trades.t_in.dt.tz is not None else t0
    acct = topstep(t, start, 400, max_days=3650) if len(t) else dict(result="running", days=0)
    if acct["result"] == "timeout":
        acct["result"] = "running"
    bal = TOPSTEP_50K["size"] + float((t.R * t.risk * MGC_OZ * (400 // (t.risk * MGC_OZ)).clip(upper=50)).sum()) if len(t) else TOPSTEP_50K["size"]
    st = dict(status=acct["result"], trades=int(len(t)), sum_R=round(float(t.R.sum()), 2) if len(t) else 0.0,
              balance_usd=round(bal, 0), start=PAPER_START, today=str(today or date.today()), risk_usd=400)
    (out / "state.json").write_text(json.dumps(st, indent=1))
    (out / "latest.txt").write_text(f"Gold 9EMA+MSNR paper vs Topstep 50K: {st['status']}, "
                                    f"{st['trades']} trades, {st['sum_R']}R, balance ${st['balance_usd']:,.0f}\n")
    return st


def load_hourly():
    import yfinance as yf
    h = yf.download("GC=F", period="730d", interval="1h", progress=False, auto_adjust=False)
    h.columns = [c[0] if isinstance(c, tuple) else c for c in h.columns]
    return clean(h)


def load_daily():
    import yfinance as yf
    x = yf.download("GC=F", start="2005-01-01", interval="1d", progress=False, auto_adjust=False)
    x.columns = [c[0] if isinstance(c, tuple) else c for c in x.columns]
    return clean(x)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--signal", action="store_true")
    ap.add_argument("--out", default="reports")
    ap.add_argument("--paper", help="forward paper-test folder")
    ap.add_argument("--flags", help="folder with KILL switch")
    a = ap.parse_args(argv)
    hd, dd = load_hourly(), load_daily()
    up = ema(dd.close) > ema(dd.close).shift()
    if a.paper:
        tr = run(hd, setups(hd, bias_series(hd, "both")), 48)
        print(json.dumps(paper(Path(a.paper), tr, Path(a.flags) if a.flags else None)))
        return 0
    if a.signal:
        sig = setups(hd, bias_series(hd, "both"))
        last = sig[-1] if sig else None
        print(json.dumps(dict(time=str(hd.index[-1]), close=round(float(hd.close.iloc[-1]), 1),
                              bias="BOTH",
                              ema9=round(float(ema(hd.close).iloc[-1]), 1),
                              last_setup=None if not last else dict(
                                  at=str(hd.index[last["t"]]), side="SHORT" if last["side"] < 0 else "LONG",
                                  level=round(last["level"], 1), stop=round(last["stop"], 1)))))
        return 0
    out = {"generated": str(date.today()), "hourly": {}, "daily": {}, "topstep": {}}
    peak = dd.close.idxmax()
    for mode in ("both", "ema_d"):
        r = honest(hd, setups(hd, bias_series(hd, mode, up)), hold=48)
        out["hourly"][mode] = r["real"]
        if mode == "both" and "trades" in r:
            t = r["trades"]
            since = t[t.t_in.dt.tz_localize(None) >= peak] if t.t_in.dt.tz else t[t.t_in >= peak]
            out["hourly"]["level_since_peak"] = stats(since)
            out["hourly"]["level_shorts_only"] = stats(t[t.side == -1])
        if "trades" in r:
            first = r["trades"].t_in.min().normalize()
            last = r["trades"].t_in.max().normalize() - pd.Timedelta(days=60)
            out["topstep"][mode] = {f"risk_${x}": topstep_eval(r["trades"], x, first, last) for x in (200, 400, 600)}
            out["topstep"][mode]["journey_$400"] = journey(r["trades"], 400, first, last)
            sig = setups(hd, bias_series(hd, mode, up))
            pl = [journey(run(hd, placebo(hd, sig, k), 48), 400, first, last) for k in range(5)]
            out["topstep"][mode]["placebo_journey_$400"] = dict(
                first_payout_rate=round(float(np.mean([q["first_payout_rate"] for q in pl])), 2),
                avg_net_usd=round(float(np.mean([q["avg_net_usd"] for q in pl])), 0))
    for mode in ("both", "ema_d"):
        out["daily"][mode] = honest(dd, setups(dd, bias_series(dd, mode, up)), hold=20)["real"]
    out["gold_peak"] = dict(date=str(peak.date()), close=round(float(dd.close.max()), 1),
                            last=round(float(dd.close.iloc[-1]), 1), last_date=str(dd.index[-1].date()))
    Path(a.out).mkdir(exist_ok=True)
    p = Path(a.out) / f"gold-ema9-msnr-{date.today()}.json"
    p.write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

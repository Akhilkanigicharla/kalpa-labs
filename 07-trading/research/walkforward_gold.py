"""A316 (not run): self-picking gold bot, walk-forward tested (Akhil 21 Nov 2026: "do it yourself, make more profit
and more trades, forward test it, give me true and best results").

Pool of trade streams (all double costs, gold futures GC=F hourly, Jul 2024 -> now):
  - all 1,024 MSNR / FVG / order block / Fibonacci versions from A314 (research/combo_gold.py)
  - time of day: buy or sell at the open of hour H (UTC), hold 1 or 4 hours, stop 1 ATR  (96 streams)
  - Asia range breakout at London (playlist setups 4/5): range 00-07 UTC, first break 07-12 UTC,
    stop at the range middle, target 2R, both sides
  - trend: 4h EMA20 vs EMA50 flip, held until the next flip, risk = 2 ATR at entry, both sides
Walk-forward (the "forward test" on past data): on the 1st of every month, score every stream on the
previous LOOKBACK months only; trade the TOP K (>= 10 trades, avg R > 0) during that month; repeat.
Nothing a month trades was used to choose it. Fixed before running: K = 3, LOOKBACK = 6.
Random baseline: the same, but K random eligible streams each month (300 runs).
Run:   python research/walkforward_gold.py                 -> reports/walkforward-gold-<date>.json
       python research/walkforward_gold.py --paper DIR     -> live forward test from 21 Nov 2026
"""
from __future__ import annotations

import itertools
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import combo_gold as cg  # noqa: E402
import gold_ema9_msnr as g  # noqa: E402

K, LOOKBACK, MIN_TRADES = 3, 6, 10
COST_R_FLOOR = 0.0004          # double cost as a fraction of price, same as A310
PAPER_START = pd.Timestamp("2026-11-21")


def _atr(h):
    return pd.Series(g.atr(h), index=h.index)


def session_streams(h: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Time-of-day trades: enter at the open of hour H, exit after n bars, stop 1 ATR (stop first)."""
    a = _atr(h).values
    o, hi, lo, c = (h[x].values for x in ("open", "high", "low", "close"))
    hours = h.index.hour
    out = {}
    for H, n, side in itertools.product(range(24), (1, 4), (1, -1)):
        rows = []
        for i in np.where(hours == H)[0]:
            if i + n > len(h) or not np.isfinite(a[i - 1]) or i == 0:
                continue
            risk = a[i - 1]
            st = o[i] - side * risk
            px, j = c[i + n - 1], i + n - 1
            for k in range(i, i + n):
                if (side == 1 and lo[k] <= st) or (side == -1 and hi[k] >= st):
                    px, j = st, k
                    break
            rows.append((h.index[i], ((px - o[i]) * side - COST_R_FLOOR * o[i]) / risk))
        out[f"hour{H:02d}_{n}h_{'buy' if side > 0 else 'sell'}"] = pd.DataFrame(rows, columns=["date", "r"])
    return out


def asia_breakout(h: pd.DataFrame) -> dict[str, pd.DataFrame]:
    o, hi, lo, c = (h[x].values for x in ("open", "high", "low", "close"))
    res = {"asia_break_buy": [], "asia_break_sell": []}
    for day, idx in pd.Series(np.arange(len(h)), index=h.index).groupby(h.index.date):
        ix = idx.values
        hrs = h.index[ix].hour
        rng = ix[hrs < 7]
        win = ix[(hrs >= 7) & (hrs < 12)]
        if len(rng) < 5 or len(win) == 0:
            continue
        top, bot = hi[rng].max(), lo[rng].min()
        mid = (top + bot) / 2
        for i in win:
            side = 1 if hi[i] > top else (-1 if lo[i] < bot else 0)
            if side == 0:
                continue
            en = top if side == 1 else bot
            risk = abs(en - mid)
            if risk <= 0:
                break
            tp = en + side * 2 * risk
            px = None
            end = min(ix[-1] + 1, len(h))
            for k in range(i, end):
                if (side == 1 and lo[k] <= mid) or (side == -1 and hi[k] >= mid):
                    px = mid
                    break
                if k > i and ((side == 1 and hi[k] >= tp) or (side == -1 and lo[k] <= tp)):
                    px = tp
                    break
            px = c[end - 1] if px is None else px
            r = ((px - en) * side - COST_R_FLOOR * en) / risk
            res["asia_break_buy" if side == 1 else "asia_break_sell"].append((h.index[i], r))
            break
    return {k: pd.DataFrame(v, columns=["date", "r"]) for k, v in res.items()}


def trend_4h(f: pd.DataFrame) -> dict[str, pd.DataFrame]:
    e1, e2 = g.ema(f.close, 20).values, g.ema(f.close, 50).values
    a = g.atr(f)
    c, o = f.close.values, f.open.values
    sig = np.sign(e1 - e2)
    res = {"trend4h_buy": [], "trend4h_sell": []}
    i = 51
    while i < len(f) - 1:
        if sig[i] != sig[i - 1] and sig[i] != 0 and np.isfinite(a[i]):
            side, en, risk = int(sig[i]), o[i + 1], 2 * a[i]
            j = i + 1
            while j < len(f) - 1 and sig[j] == side:
                j += 1
            r = ((c[j] - en) * side - COST_R_FLOOR * en) / risk
            res["trend4h_buy" if side > 0 else "trend4h_sell"].append((f.index[i + 1], r))
            i = j
        else:
            i += 1
    return {k: pd.DataFrame(v, columns=["date", "r"]) for k, v in res.items()}


def _cfg_name(c):
    tf, side, (a, b), e, s = c
    return f"{tf}_{side}_{a}{'+' + b if b else ''}{'_ema' if e else ''}{'_story' if s else ''}"


def combo_streams() -> dict[str, pd.DataFrame]:
    sigs = [(a, None) for a in cg.FAM] + [(a, b) for a in cg.FAM for b in cg.FAM if a != b]
    zkeys = list(itertools.product(("1h", "4h"), ("long", "short"), cg.FAM))
    with ProcessPoolExecutor(initializer=cg._init) as ex:
        zmap = dict(ex.map(cg.zones_job, zkeys))
    if not cg._D:
        cg._init()
    out, seen = {}, set()
    for c in itertools.product(("1h", "4h"), ("long", "short"), sigs, (True, False), (True, False)):
        t = cg.trades(c[0], c[1], cg.build(*c, zmap), 2 * cg.COST)
        if t.empty:
            continue
        key = tuple(t.entry_bar) + (c[0], c[1])
        if key in seen:                 # identical trade list (filter changed nothing): keep one
            continue
        seen.add(key)
        out[_cfg_name(c)] = t[["date", "r"]].reset_index(drop=True)
    return out


def all_streams() -> dict[str, pd.DataFrame]:
    s = combo_streams()
    h = cg._D[("1h", "long")]
    f = cg._D[("4h", "long")]
    s.update(session_streams(h))
    s.update(asia_breakout(h))
    s.update(trend_4h(f))
    return {k: v.sort_values("date").reset_index(drop=True) for k, v in s.items() if len(v)}


def walk(streams: dict, months: pd.DatetimeIndex, k=K, lookback=LOOKBACK, rng=None) -> tuple[pd.DataFrame, list]:
    """Each month: rank streams on the previous `lookback` months, trade the top k (or k random
    eligible ones if rng is given) during the month."""
    taken, picks = [], []
    for m0 in months:
        m1 = m0 + pd.offsets.MonthBegin(1)
        lb = m0 - pd.DateOffset(months=lookback)
        sc = []
        for name, t in streams.items():
            past = t[(t.date >= lb) & (t.date < m0)]
            if len(past) >= MIN_TRADES and past.r.mean() > 0:
                sc.append((past.r.sum(), name))
        if not sc:
            picks.append((str(m0.date()), []))
            continue
        if rng is None:
            chosen = [n for _, n in sorted(sc, reverse=True)[:k]]
        else:
            chosen = list(rng.choice([n for _, n in sc], size=min(k, len(sc)), replace=False))
        picks.append((str(m0.date()), chosen))
        for n in chosen:
            t = streams[n]
            cur = t[(t.date >= m0) & (t.date < m1)]
            taken.append(cur.assign(stream=n))
    return (pd.concat(taken).sort_values("date") if taken else pd.DataFrame(columns=["date", "r", "stream"])), picks


def summary(t: pd.DataFrame) -> dict:
    if t.empty:
        return dict(n=0)
    r = t.r.values
    eq = np.cumsum(r)
    yrs = max((t.date.max() - t.date.min()).days / 365.25, 0.1)
    mon = t.groupby(t.date.dt.to_period("M")).r.sum()
    return dict(n=int(len(r)), trades_per_month=round(len(r) / max(len(mon), 1), 1), win=round(float((r > 0).mean()), 3),
                avg_r=round(float(r.mean()), 3), total_r=round(float(r.sum()), 1), per_year_r=round(float(r.sum() / yrs), 1),
                worst_drop_r=round(float((eq - np.maximum.accumulate(eq)).min()), 1),
                green_months=f"{int((mon > 0).sum())}/{len(mon)}", rupees_at_100=int(round(r.sum() * 100)))


def main() -> int:
    if "--paper" in sys.argv:
        return paper(Path(sys.argv[sys.argv.index("--paper") + 1]),
                     Path(sys.argv[sys.argv.index("--flags") + 1]) if "--flags" in sys.argv else None)
    streams = all_streams()
    first = min(t.date.min() for t in streams.values())
    start = (first + pd.DateOffset(months=LOOKBACK)).to_period("M").to_timestamp()
    months = pd.date_range(start, pd.Timestamp.today().normalize(), freq="MS")
    t, picks = walk(streams, months)
    rnd = [walk(streams, months, rng=np.random.default_rng(s))[0] for s in range(300)]
    rtot = np.array([x.r.sum() if len(x) else 0 for x in rnd])
    sens = {f"K{k}_L{lb}": summary(walk(streams, months, k=k, lookback=lb)[0]) for k in (1, 3, 5) for lb in (3, 6)}
    out = dict(generated=str(date.today()), streams=len(streams), months=len(months),
               rule=f"top {K} by previous {LOOKBACK} months, >= {MIN_TRADES} trades, avg R > 0",
               result=summary(t), random_median_total_r=round(float(np.median(rtot)), 1),
               random_p95_total_r=round(float(np.percentile(rtot, 95)), 1),
               p_random_as_good=round(float(np.mean(rtot >= t.r.sum())), 3),
               by_stream=t.groupby("stream").r.agg(["count", "sum"]).round(1).sort_values("sum").to_dict("index"),
               by_month={str(k): round(float(v), 1) for k, v in t.groupby(t.date.dt.to_period("M")).r.sum().items()},
               picks=picks, sensitivity_not_used_to_choose=sens)
    Path("reports").mkdir(exist_ok=True)
    (Path("reports") / f"walkforward-gold-{date.today()}.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: out[k] for k in ("streams", "months", "result", "random_median_total_r",
                                          "random_p95_total_r", "p_random_as_good", "by_month",
                                          "sensitivity_not_used_to_choose")}, indent=1))
    return 0


def paper(out: Path, flags: Path | None) -> int:
    """Live forward test: same rule, only trades on/after 21 Nov 2026 count. No orders are sent."""
    out.mkdir(parents=True, exist_ok=True)
    if flags and (flags / "KILL").exists():
        (out / "state.json").write_text(json.dumps(dict(status="killed")))
        return 0
    streams = all_streams()
    months = pd.date_range(PAPER_START.to_period("M").to_timestamp(), pd.Timestamp.today().normalize(), freq="MS")
    t, picks = walk(streams, months)
    t = t[t.date >= PAPER_START]
    t.to_csv(out / "ledger.csv", index=False)
    st = dict(status="running", start=str(PAPER_START.date()), picks_now=picks[-1] if picks else None, **summary(t))
    (out / "state.json").write_text(json.dumps(st, indent=1, default=str))
    print(json.dumps(st, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

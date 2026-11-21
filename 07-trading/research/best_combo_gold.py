"""A323: "combine all these and create best ... more trades in different time frames ... last 2 years:
how many trades, how many win, how many lose" (Akhil, 21 Nov 2026).

Every gold strategy built so far becomes a candidate, run on 1h, 2h and 4h (2 years of free hourly data;
5m/30m have only 60 days, so they cannot be tested over 2 years):
  EA      A315 loose EA (H4 regime, H1 trend, setup+trigger on the timeframe, doc exits), every setup
  EA+MSNR same + A320 MSNR fresh-level filter
  EMA9    A308 9 EMA + fresh MSNR level rejection, both directions, 2R target
  MSNR    A309 playlist setups (fresh_v, qm, eq_sweep), long and short, k=2, 9 EMA filter, 2R target
Rule written BEFORE looking at results:  a candidate joins the "best" mix only if, in the EARLIER part
(before 2025-09-01), it has >= 15 trades and avg R >= +0.05 after costs.  The mix is then reported
for the full 2 years and, separately, for the LATER part it was not chosen on.
Mix account: $10K, 0.5% risk a trade (several strategies can be in trades at once), no compounding.
Win = R > +0.05, loss = R < -0.05, breakeven in between (stop moved to entry after a partial).
Random baseline: every chosen candidate's entries replaced by random bars (same count/side/exits), 20 seeds.
Research code only.  Not investment advice.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ea_design_gold as e  # noqa: E402
import ea_msnr_gold as m  # noqa: E402
import ea_multitf_gold as mt  # noqa: E402
import gold_ema9_msnr as g  # noqa: E402
import msnr_gold_robust as mr  # noqa: E402
from src.msnr import SETUPS, mirror  # noqa: E402
from src.smc import placebo as zone_placebo  # noqa: E402

SPLIT = pd.Timestamp("2025-09-01")
RISK = 0.005
TFS = {"1h": "1h", "2h": "2h", "4h": "4h"}
MSNR_COST = 0.40          # $ per round trip, converted to a price fraction per trade


def frames():
    h1 = m.load_h1()
    return {"1h": h1, "2h": e.resample(h1, "2h").dropna(), "4h": e.resample(h1, "4h").dropna()}


# ---------- candidates: each returns a DataFrame with t_in, t_out, side, r ----------
def ea_trades(x, tf, h1f, h4f, h4, msnr: bool, rand_seed=None):
    e.SCALED, e.DROP, e.EVERY, e.LADDER = True, set(e.LOOSE), True, False
    sig = e.setups(x, pd.Timedelta(tf), h1f, h4f)
    if msnr:
        st = m.msnr_state(x, h4, tf=tf)
        sig = m.apply(sig, st, pd.Series(0.0, index=x.index), pd.Series(e.g.atr(x), index=x.index), {"fresh"}, x.index, tf=tf)
    if rand_seed is not None:
        sig = mt.placebo(sig, x, tf, rand_seed)
    t = e.simulate(x, pd.Timedelta(tf), sig, 2 * pd.Timedelta(tf))
    e.EVERY = False
    return t[["t_in", "t_out", "side", "r"]] if len(t) else pd.DataFrame(columns=["t_in", "t_out", "side", "r"])


def ema9_trades(x, tf, rand_seed=None):
    d = g.clean(x)
    sig = g.setups(d, g.bias_series(d, "both"), k=2)
    if rand_seed is not None:
        sig = g.placebo(d, sig, rand_seed)
    hold = {"1h": 48, "2h": 24, "4h": 12}[tf]
    t = g.run(d, sig, hold)
    if t.empty:
        return pd.DataFrame(columns=["t_in", "t_out", "side", "r"])
    return t.rename(columns={"R": "r"})[["t_in", "t_out", "side", "r"]]


def msnr_trades(x, tf, setup, side, rand_seed=None):
    real = g.clean(x)
    df = mirror(real) if side == "short" else real
    zs = mr.filt(SETUPS[setup](df, k=2, storyline_on=False), real, df, True, side)
    if rand_seed is not None:
        zs = zone_placebo(df, zs, seed=rand_seed)
    p = {"1h": (20, 48), "2h": (10, 24), "4h": (10, 20)}[tf]
    from src.smc import simulate
    cost = MSNR_COST / float(real.close.mean())
    t = simulate(df, zs, wait=p[0], hold=p[1], rr=2.0, cost=cost)
    if t.empty:
        return pd.DataFrame(columns=["t_in", "t_out", "side", "r"])
    return pd.DataFrame(dict(t_in=df.index[t.entry_bar.values], t_out=df.index[t.exit_bar.values],
                             side=1 if side == "long" else -1, r=t.r.values))


def candidates(fr, rand_seed=None):
    h1 = fr["1h"]
    h4 = fr["4h"]
    e.SCALED, e.DROP = True, set(e.LOOSE)          # must be set BEFORE the features are built (A316 lesson)
    h4f, h1f = e.h4_features(h4, h1), e.h1_features(h1)
    out = {}
    for tf, x in fr.items():
        out[f"EA {tf}"] = lambda x=x, tf=tf: ea_trades(x, tf, h1f, h4f, h4, False, rand_seed)
        out[f"EA+MSNR {tf}"] = lambda x=x, tf=tf: ea_trades(x, tf, h1f, h4f, h4, True, rand_seed)
        out[f"EMA9 {tf}"] = lambda x=x, tf=tf: ema9_trades(x, tf, rand_seed)
        for setup in ("fresh_v", "qm", "eq_sweep"):
            for side in ("long", "short"):
                out[f"MSNR {setup} {side} {tf}"] = lambda x=x, tf=tf, s=setup, sd=side: msnr_trades(x, tf, s, sd, rand_seed)
    return out


# ---------- stats ----------
def count(t):
    r = t.r.values
    return dict(trades=int(len(r)), wins=int((r > 0.05).sum()), losses=int((r < -0.05).sum()),
                breakeven=int(((r >= -0.05) & (r <= 0.05)).sum()),
                win_rate=round(float((r > 0.05).mean()), 3) if len(r) else None,
                avg_r=round(float(r.mean()), 3) if len(r) else None, total_r=round(float(r.sum()), 1))


def account(t, start=10_000.0):
    if t.empty:
        return {}
    t = t.sort_values("t_out")
    pnl = t.r.values * start * RISK
    eq = start + np.cumsum(pnl)
    peak = np.maximum.accumulate(np.r_[start, eq])[1:]
    day = t.assign(p=pnl).groupby(t.t_out.dt.date).p.sum()
    ev = sorted([(a, 1) for a in t.t_in] + [(b, -1) for b in t.t_out])
    c = mx = 0
    for _, d in ev:
        c += d
        mx = max(mx, c)
    months = max((t.t_out.max() - t.t_in.min()).days / 30.4, 1)
    return dict(profit_usd=round(float(pnl.sum()), 0), worst_drop_pct=round(float(((peak - eq) / peak).max() * 100), 1),
                worst_day_usd=round(float(day.min()), 0), best_day_usd=round(float(day.max()), 0),
                max_open_together=int(mx), trades_per_month=round(len(t) / months, 1),
                profit_months=f"{int((t.assign(p=pnl).groupby(t.t_out.dt.to_period('M')).p.sum() > 0).sum())} of "
                              f"{t.t_out.dt.to_period('M').nunique()}")


def the5ers(t, start=10_000.0, target=0.08, daily=0.05, maxloss=0.10):
    """Start a $10K step-1 attempt every Monday: pass / fail / still running at the end."""
    t = t.sort_values("t_out")
    res = {"pass": 0, "fail": 0, "running": 0}
    for s in pd.date_range(t.t_in.min().normalize(), t.t_out.max(), freq="W-MON"):
        u = t[t.t_in >= s]
        eq, out, day_pnl = start, "running", {}
        for _, row in u.iterrows():
            p = row.r * start * RISK
            eq += p
            dd = row.t_out.date()
            day_pnl[dd] = day_pnl.get(dd, 0) + p
            if day_pnl[dd] <= -daily * start or eq <= start * (1 - maxloss):
                out = "fail"
                break
            if eq >= start * (1 + target):
                out = "pass"
                break
        res[out] += 1
    n = sum(res.values())
    return {k: round(v / n, 2) for k, v in res.items()} | dict(starts=n)


def main() -> int:
    if "--paper" in sys.argv:
        fl = sys.argv[sys.argv.index("--flags") + 1] if "--flags" in sys.argv else None
        st = paper(Path(sys.argv[sys.argv.index("--paper") + 1]), Path(fl) if fl else None)
        print(json.dumps({k: v for k, v in st.items() if k not in ("open_trades", "by_strategy")}, default=str))
        return 0
    fr = frames()
    cand = candidates(fr)
    rows, kept = [], []
    trades = {}
    for name, fn in cand.items():
        t = fn()
        trades[name] = t
        a, b = t[t.t_in < SPLIT], t[t.t_in >= SPLIT]
        ok = len(a) >= 15 and len(a) and a.r.mean() >= 0.05
        rows.append(dict(name=name, early=count(a), late=count(b), chosen=bool(ok)))
        if ok:
            kept.append(name)
    mix = pd.concat([trades[k].assign(strategy=k) for k in kept]) if kept else pd.DataFrame()
    late = mix[mix.t_in >= SPLIT] if len(mix) else mix
    rnd = []
    for sd in range(20):
        cr = candidates(fr, rand_seed=sd)
        pt = pd.concat([cr[k]() for k in kept]) if kept else pd.DataFrame(columns=["r"])
        rnd.append(float(pt.r.mean()) if len(pt) else 0.0)
    per_rand = {}
    for k in kept:
        vals = []
        for sd in range(5):
            pt = candidates(fr, rand_seed=50 + sd)[k]()
            vals.append(float(pt.r.mean()) if len(pt) else 0.0)
        per_rand[k] = dict(real=round(float(trades[k].r.mean()), 3), random=round(float(np.mean(vals)), 3))
    rep = dict(per_strategy_vs_random=per_rand, generated=str(date.today()), period=f"{fr['1h'].index[0].date()} to {fr['1h'].index[-1].date()}",
               rule="joins the mix if earlier part (before 2025-09-01) has >= 15 trades and avg R >= +0.05",
               chosen=kept, candidates=rows,
               mix_2y=count(mix) | account(mix), mix_later_part=count(late) | account(late),
               mix_by_strategy={k: count(trades[k]) for k in kept},
               mix_by_quarter={str(q): round(float(v), 1) for q, v in mix.groupby(mix.t_in.dt.to_period("Q")).r.sum().items()} if len(mix) else {},
               random_avg_r=round(float(np.mean(rnd)), 3),
               p_vs_random=round(float((np.array(rnd) >= mix.r.mean()).mean()), 2) if len(mix) else None,
               the5ers_step1=the5ers(mix) if len(mix) else None)
    Path("reports").mkdir(exist_ok=True)
    (Path("reports") / f"best-combo-gold-{date.today()}.json").write_text(json.dumps(rep, indent=1, default=str))
    if len(mix):
        mix.sort_values("t_in").to_csv(Path("reports") / f"best-combo-gold-trades-{date.today()}.csv", index=False)
    for r in rows:
        print(f"{r['name']:28s} early {r['early']['trades']:4d} {r['early']['avg_r']} | late {r['late']['trades']:4d} {r['late']['avg_r']} {'<- IN' if r['chosen'] else ''}")
    print(json.dumps({k: v for k, v in rep.items() if k not in ("candidates",)}, indent=1, default=str))
    return 0


# ---------------- A324: 6-month forward test (paper only) ----------------
PAPER_START = pd.Timestamp("2026-11-21")
PAPER_END = pd.Timestamp("2027-05-21")
PAPER_RISK = 0.0025          # the risk chosen in A323 (The5%ers step 1 passed 98% in the backtest)
CHOSEN = ["EA+MSNR 1h", "MSNR fresh_v long 1h", "MSNR qm long 1h", "MSNR qm short 1h", "EMA9 2h",
          "MSNR fresh_v long 2h", "MSNR fresh_v short 2h", "MSNR qm long 2h", "EMA9 4h",
          "MSNR fresh_v long 4h", "MSNR fresh_v short 4h", "MSNR qm long 4h", "MSNR qm short 4h"]   # frozen 21 Nov 2026


def layer_view(led: pd.DataFrame) -> dict:
    """A325 layer on the same paper ledger: 1.5x size after that strategy's last closed trade won, 0.75x after a
    loss; plus how trades within 2 h of CPI / jobs report / FOMC did (the EA blocks those)."""
    import macro_layer_gold as ml
    t = led.sort_values("t_in").reset_index(drop=True)
    w = []
    for _, row in t.iterrows():
        prior = t[(t.strategy == row.strategy) & (t.t_out < row.t_in)].sort_values("t_out")
        last = prior.r.iloc[-1] if len(prior) else 0.0
        w.append(1.5 if last > 0.05 else (0.75 if last < -0.05 else 1.0))
    w = np.array(w)
    ev = ml.events_utc().values
    ti = t.t_in.values.astype("datetime64[ns]")
    j = np.searchsorted(ev, ti)
    gap = np.minimum(np.abs((ev[np.minimum(j, len(ev) - 1)] - ti) / np.timedelta64(1, "h")),
                     np.abs((ti - ev[np.maximum(j - 1, 0)]) / np.timedelta64(1, "h")))
    near = gap <= 2
    return dict(streak_sized_total_r=round(float((t.r.values * w).sum()), 1),
                streak_sized_profit_usd=round(float((t.r.values * w).sum() * 10_000 * PAPER_RISK), 0),
                near_news_trades=int(near.sum()),
                near_news_avg_r=round(float(t.r.values[near].mean()), 3) if near.any() else None)


def paper(out: Path, flags: Path | None = None, fr: dict | None = None, today: pd.Timestamp | None = None) -> dict:
    """Append-only forward ledger: a trade is written once it has CLOSED, entered on/after PAPER_START and
    before PAPER_END. Trades already in the ledger are never rewritten (later data revisions can't change
    the record). Still-open trades are listed separately. No orders are sent anywhere."""
    out.mkdir(parents=True, exist_ok=True)
    led_p = out / "ledger.csv"
    if flags and (flags / "KILL").exists():
        st = dict(status="killed")
        (out / "state.json").write_text(json.dumps(st, indent=1))
        return st
    fr = fr or frames()
    last_bar = fr["1h"].index[-1]
    today = today or pd.Timestamp(date.today())
    cand = candidates(fr)
    new = []
    open_now = []
    for k in CHOSEN:
        t = cand[k]()
        if t.empty:
            continue
        t = t[(t.t_in >= PAPER_START) & (t.t_in < PAPER_END)]
        done = t[t.t_out < last_bar]               # a trade ending on the last bar may still be running
        new.append(done.assign(strategy=k))
        for _, row in t[t.t_out >= last_bar].iterrows():
            open_now.append(dict(strategy=k, t_in=str(row.t_in), side="LONG" if row.side == 1 else "SHORT"))
    new = pd.concat(new) if new else pd.DataFrame(columns=["t_in", "t_out", "side", "r", "strategy"])
    old = pd.read_csv(led_p, parse_dates=["t_in", "t_out"]) if led_p.exists() else new.iloc[0:0]
    key = lambda d: d.strategy.astype(str) + "|" + d.t_in.astype(str)
    add = new[~key(new).isin(set(key(old)))] if len(old) else new
    led = pd.concat([old, add.assign(recorded=str(today.date()))]).sort_values("t_in")
    led.to_csv(led_p, index=False)
    global RISK
    RISK = PAPER_RISK
    st = dict(status="running" if today < PAPER_END else "finished", start=str(PAPER_START.date()),
              end=str(PAPER_END.date()), days_done=int((min(today, PAPER_END) - PAPER_START).days),
              risk_per_trade_pct=PAPER_RISK * 100, data_up_to=str(last_bar),
              **count(led), open_trades=open_now,
              **(account(led) if len(led) else {}),
              backtest_expected=dict(avg_r=0.143, win_rate=0.406, trades_per_month=168),
              by_strategy={k: count(led[led.strategy == k]) for k in CHOSEN if (led.strategy == k).any()})
    st["with_layer_A325"] = layer_view(led) if len(led) else {}
    if len(led) >= 30:
        st["verdict"] = ("on track" if st["avg_r"] >= 0.07 else "below backtest — review")
    else:
        st["verdict"] = "too early (fewer than 30 closed trades)"
    (out / "state.json").write_text(json.dumps(st, indent=1, default=str))
    return st


if __name__ == "__main__":
    raise SystemExit(main())

"""Hedge-fund style validation of the gold mix backtest (21 Nov 2026).  Research only; not investment advice.

Input:  reports/ea-mix-backtest-trades-cap2-2026-11-21.csv  (pnl already net of $0.40/oz round-trip cost)
        research/validation/candidates_r.csv  (27 candidate strategies, unit R, from gen_candidates.py)
        /tmp/gc_h1_730d.parquet  (GC=F hourly, UTC, yfinance)
Output: research/validation/results.json  (+ prints short headline lines)

All rules below were written before running:
  splits     H1/H2 = calendar halves; SEL = 2025-09-01 (the split the mix was selected on); Y1 = before 2025-07-01
  costs      extra $0.10/0.30/0.50 per oz per side -> pnl -= c*100*lot*2
  MC         10,000 paths, stationary block bootstrap of business days (mean block 5 d), The5%ers High Stakes
             $10K: daily loss 5% of start (closed P&L), max loss 10% of start, Step1 +10%, Step2 +5%, 3 profit days
  spike A    news breakout: H1 bar containing CPI/NFP/FOMC release; if its range > 1.5*ATR14 enter next bar open in
             its direction; stop = opposite end of that bar; target 2R; time exit after 8 bars; cost $0.30/oz/side
  spike B    ATR expansion: any H1 bar with range > 2*ATR14 and close in outer 25% of the range; enter next open in
             that direction; stop 1*ATR14, target 2*ATR14, exit after 12 bars; cost $0.30/oz/side
  risk       fit on Y1, test on the rest: (a) drop strategies with Y1 pnl <= 0; (b) inverse-vol weights from Y1 daily
             pnl std (mean weight 1); (c) vol targeting: size x (Y1 median 20d vol / trailing 20d vol), clip 0.5..2,
             using only data known before the entry day; (d) concurrency: skip a trade if >= 2 same-side trades open;
             (e) a + b combined
"""
from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research"))
import macro_layer_gold as ml  # noqa: E402

START = 10_000.0
OUT = Path(__file__).parent
rng = np.random.default_rng(7)

t = pd.read_csv(ROOT / "reports/ea-mix-backtest-trades-cap2-2026-11-21.csv", parse_dates=["t_in", "t_out"])
t = t.sort_values("t_out").reset_index(drop=True)
DAYS = pd.bdate_range(t.t_in.min().normalize(), t.t_out.max().normalize())
MID = DAYS[0] + (DAYS[-1] - DAYS[0]) / 2
SEL = pd.Timestamp("2025-09-01")
Y1 = pd.Timestamp("2025-07-01")


def daily(x: pd.DataFrame, col="pnl", days=DAYS) -> pd.Series:
    d = x.groupby(x.t_out.dt.normalize())[col].sum()
    d.index = d.index.map(lambda z: z if z.weekday() < 5 else z - pd.offsets.BDay(1))
    return d.groupby(level=0).sum().reindex(days, fill_value=0.0)


def maxdd(pnl_sorted: np.ndarray) -> float:
    eq = START + np.cumsum(pnl_sorted)
    peak = np.maximum.accumulate(np.r_[START, eq])[1:]
    return float(((peak - eq) / peak).max() * 100) if len(eq) else 0.0


def streak(pnl: np.ndarray) -> int:
    best = c = 0
    for p in pnl:
        c = c + 1 if p < 0 else 0
        best = max(best, c)
    return best


def stat(x: pd.DataFrame, days=DAYS) -> dict:
    if len(x) == 0:
        return dict(n=0)
    x = x.sort_values("t_out")
    r, p = x.r.values, x.pnl.values
    d = daily(x, days=days)
    w = d.resample("W-FRI").sum()
    sh = float(d.mean() / d.std() * np.sqrt(252)) if d.std() > 0 else 0.0
    return dict(n=len(x), win=round(float((r > 0.05).mean() * 100), 1), avg_r=round(float(r.mean()), 3),
                exp_usd=round(float(p.mean()), 2),
                pf=round(float(p[p > 0].sum() / -p[p < 0].sum()), 2) if (p < 0).any() else None,
                sharpe=round(sh, 2), t_r=round(float(r.mean() / (r.std(ddof=1) / np.sqrt(len(r)))), 2) if len(r) > 2 else None,
                pnl=round(float(p.sum()), 0), maxdd=round(maxdd(p), 2), lose_streak=streak(p),
                worst_day=round(float(d.min()), 0), worst_week=round(float(w.min()), 0))


res: dict = {}
strats = sorted(t.strategy.unique())

# 1 ---------- per strategy + portfolio ----------
res["stats"] = {s: stat(t[t.strategy == s]) for s in strats} | {"PORTFOLIO": stat(t)}

# 2 ---------- walk forward ----------
wf = {}
for s in strats + ["PORTFOLIO"]:
    x = t if s == "PORTFOLIO" else t[t.strategy == s]
    q = x.groupby(x.t_in.dt.to_period("Q")).pnl.sum()
    wf[s] = dict(h1=round(float(x[x.t_in < MID].pnl.sum()), 0), h2=round(float(x[x.t_in >= MID].pnl.sum()), 0),
                 h1_r=round(float(x[x.t_in < MID].r.mean()), 3), h2_r=round(float(x[x.t_in >= MID].r.mean()), 3),
                 pre_sel=round(float(x[x.t_in < SEL].pnl.sum()), 0), post_sel=round(float(x[x.t_in >= SEL].pnl.sum()), 0),
                 post_sel_r=round(float(x[x.t_in >= SEL].r.mean()), 3) if (x.t_in >= SEL).any() else None,
                 post_sel_t=round(float(stats.ttest_1samp(x[x.t_in >= SEL].r, 0).statistic), 2) if (x.t_in >= SEL).sum() > 2 else None,
                 q_pos=f"{int((q > 0).sum())}/{len(q)}", quarters={str(k): round(float(v), 0) for k, v in q.items()})
res["walk_forward"] = dict(mid=str(MID.date()), sel=str(SEL.date()), by=wf)

# 3 ---------- DSR + PBO ----------
def dsr(dr: pd.Series, n_trials: int, var_sr: float) -> dict:
    sr = dr.mean() / dr.std()
    T = len(dr)
    g3, g4 = stats.skew(dr), stats.kurtosis(dr, fisher=False)
    em = 0.5772156649
    sr0 = np.sqrt(var_sr) * ((1 - em) * stats.norm.ppf(1 - 1 / n_trials) + em * stats.norm.ppf(1 - 1 / (n_trials * np.e)))
    z = (sr - sr0) * np.sqrt(T - 1) / np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2)
    return dict(sr_ann=round(float(sr * np.sqrt(252)), 2), sr0_ann=round(float(sr0 * np.sqrt(252)), 2),
                dsr=round(float(stats.norm.cdf(z)), 3), psr0=round(float(stats.norm.cdf(sr * np.sqrt(T - 1) /
                np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2))), 3), skew=round(float(g3), 2), kurt=round(float(g4), 1))


cand = pd.read_csv(OUT / "candidates_r.csv", parse_dates=["t_in", "t_out"])
cand["pnl"] = cand.r  # unit R per trade
cdays = pd.bdate_range(cand.t_in.min().normalize(), cand.t_out.max().normalize())
M = pd.DataFrame({k: daily(g, "r", cdays) for k, g in cand.groupby("strategy")})
cand_sr = (M.mean() / M.std()).replace([np.inf, -np.inf], np.nan).dropna()
var_sr = float(cand_sr.var())
pdr = daily(t) / START
res["dsr"] = {f"N={n}": dsr(pdr, n, var_sr) for n in (13, 27, 50, 100)}
res["dsr_null_var"] = {f"N={n}": dsr(pdr, n, 1 / len(pdr)) for n in (13, 50, 100)}
res["dsr_var_sr_ann"] = round(float(np.sqrt(var_sr) * np.sqrt(252)), 2)
res["dsr_per_strategy_N50"] = {s: dsr(daily(t[t.strategy == s]) / START, 50, var_sr)["dsr"] for s in strats}
# second-half-only DSR (closest to true OOS)
res["dsr_post_sel_N50"] = dsr(pdr[pdr.index >= SEL], 50, var_sr)


def pbo(M: pd.DataFrame, S=16) -> dict:
    blocks = np.array_split(np.arange(len(M)), S)
    X = M.values
    logits, deg = [], []
    for comb in combinations(range(S), S // 2):
        IS = np.concatenate([blocks[i] for i in comb])
        OS = np.concatenate([blocks[i] for i in range(S) if i not in comb])
        f = lambda idx: X[idx].mean(0) / (X[idx].std(0) + 1e-12)
        si, so = f(IS), f(OS)
        best = int(np.argmax(si))
        rank = stats.rankdata(so)[best] / (len(so) + 1)
        logits.append(np.log(rank / (1 - rank)))
        deg.append((si[best], so[best]))
    logits = np.array(logits)
    deg = np.array(deg)
    return dict(pbo=round(float((logits <= 0).mean()), 3), median_logit=round(float(np.median(logits)), 2),
                is_best_sr_ann=round(float(deg[:, 0].mean() * np.sqrt(252)), 2),
                oos_of_is_best_sr_ann=round(float(deg[:, 1].mean() * np.sqrt(252)), 2),
                p_oos_loss=round(float((deg[:, 1] < 0).mean()), 3), n_trials=M.shape[1], splits=len(logits))


res["pbo_27_candidates"] = pbo(M)
res["pbo_13_mix"] = pbo(pd.DataFrame({s: daily(t[t.strategy == s]) for s in strats}))

# 4 ---------- Monte Carlo prop sim ----------
def boot_days(n_days: int, base: np.ndarray, paths: int, block=5) -> np.ndarray:
    L = len(base)
    idx = np.empty((paths, n_days), int)
    j = rng.integers(L, size=paths)
    for d in range(n_days):
        idx[:, d] = j
        jump = rng.random(paths) < 1 / block
        j = np.where(jump, rng.integers(L, size=paths), (j + 1) % L)
    return base[idx]


def prop(sim: np.ndarray, target: float, horizons=(60, 90, 180)) -> dict:
    """sim: paths x days of $ pnl (business days).  Profit day = >= 0.5% of start."""
    cum = np.cumsum(sim, 1)
    fail_day = (sim <= -0.05 * START) | (cum <= -0.10 * START)
    pday = np.cumsum(sim >= 0.005 * START, 1) >= 3
    hit = (cum >= target * START) & pday
    first_fail = np.where(fail_day.any(1), fail_day.argmax(1), 10 ** 9)
    first_hit = np.where(hit.any(1), hit.argmax(1), 10 ** 9)
    o = {}
    for h in horizons:
        bd = int(h * 5 / 7)
        o[f"pass_{h}d"] = round(float(((first_hit < first_fail) & (first_hit < bd)).mean()), 3)
        o[f"fail_{h}d"] = round(float(((first_fail < first_hit) & (first_fail < bd)).mean()), 3)
    o["pass_ever_1y"] = round(float((first_hit < first_fail).mean()), 3)
    return o


base_d = daily(t).values
H = 252
sims = {}
for lab, base in (("full", base_d), ("post_sel", daily(t[t.t_in >= SEL]).values[DAYS >= SEL]),
                  ("full_cost030", daily(t.assign(pnl=t.pnl - 0.30 * 100 * t.lot * 2)).values)):
    for mult in (1, 2, 3, 4):
        sim = boot_days(H, base * mult, 5000 if mult > 1 else 10000)
        cum = np.cumsum(sim, 1)
        eq = START + cum
        dd = ((np.maximum.accumulate(np.c_[np.full(len(eq), START), eq], 1)[:, 1:] - eq) /
              np.maximum.accumulate(np.c_[np.full(len(eq), START), eq], 1)[:, 1:]).max(1) * 100
        sims[f"{lab}_x{mult}"] = dict(
            risk_pct=0.25 * mult, dd_p50=round(float(np.percentile(dd, 50)), 1), dd_p95=round(float(np.percentile(dd, 95)), 1),
            dd_p99=round(float(np.percentile(dd, 99)), 1),
            p_daily_5=round(float((sim <= -0.05 * START).any(1).mean()), 4),
            p_total_10=round(float((cum <= -0.10 * START).any(1).mean()), 4),
            ret_1y_p5_p50_p95=[round(float(np.percentile(cum[:, -1], q) / START * 100), 1) for q in (5, 50, 95)],
            step1=prop(sim, 0.10), step2=prop(sim, 0.05))
res["monte_carlo"] = sims

# 5 ---------- cost stress ----------
cs = {}
for c in (0.0, 0.10, 0.30, 0.50):
    x = t.assign(pnl=t.pnl - c * 100 * t.lot * 2)
    x = x.assign(r=x.pnl / x.risk)
    row = {s: round(float(x[x.strategy == s].pnl.sum()), 0) for s in strats}
    row["PORTFOLIO"] = round(float(x.pnl.sum()), 0)
    row["PORT_sharpe"] = stat(x)["sharpe"]
    row["PORT_maxdd"] = stat(x)["maxdd"]
    row["PORT_post_sel"] = round(float(x[x.t_in >= SEL].pnl.sum()), 0)
    cs[f"+{c:.2f}"] = row
res["cost_stress"] = cs
res["avg_cost_per_trade_usd_at_0.30"] = round(float((0.30 * 100 * t.lot * 2).mean()), 2)
res["avg_cost_in_R_at_0.30"] = round(float((0.30 * 100 * t.lot * 2 / t.risk).mean()), 3)

# 6 ---------- news / spikes ----------
ev = ml.events_utc()
ev = ev[(ev >= DAYS[0]) & (ev <= DAYS[-1] + pd.Timedelta("1D"))]


def h_to_ev(ts: pd.Series) -> np.ndarray:
    e = ev.values
    ti = ts.values
    j = np.searchsorted(e, ti)
    nxt = (e[np.minimum(j, len(e) - 1)] - ti) / np.timedelta64(1, "h")
    prv = (ti - e[np.maximum(j - 1, 0)]) / np.timedelta64(1, "h")
    return np.minimum(np.abs(nxt), np.abs(prv))


t["h_ev"] = h_to_ev(t.t_in)
cand["h_ev"] = h_to_ev(cand.t_in)
ns = {}
for lab, x in (("mix", t), ("candidates_unfiltered", cand)):
    for w in (2, 6, 24):
        a, b = x[x.h_ev <= w], x[x.h_ev > w]
        ns[f"{lab}_within_{w}h"] = dict(n_in=len(a), r_in=round(float(a.r.mean()), 3) if len(a) else None,
                                         n_out=len(b), r_out=round(float(b.r.mean()), 3),
                                         p=round(float(stats.ttest_ind(a.r, b.r, equal_var=False).pvalue), 3) if len(a) > 2 else None)
# trades OPEN during an event (entered before, exit after)
openev = np.zeros(len(t), bool)
for e_ in ev:
    openev |= (t.t_in.values < e_.to_datetime64()) & (t.t_out.values > e_.to_datetime64())
ns["mix_open_through_event"] = dict(n=int(openev.sum()), r=round(float(t.r[openev].mean()), 3),
                                    r_other=round(float(t.r[~openev].mean()), 3),
                                    pnl=round(float(t.pnl[openev].sum()), 0))
res["news"] = ns

h1 = pd.read_parquet("/tmp/gc_h1_730d.parquet")
o, hi, lo, cl = (h1[k].values for k in ("open", "high", "low", "close"))
tr = np.maximum(hi - lo, np.maximum(abs(hi - np.r_[cl[0], cl[:-1]]), abs(lo - np.r_[cl[0], cl[:-1]])))
atr = pd.Series(tr).rolling(14).mean().shift(1).values  # ATR known before the bar


def run_rule(sig_idx, sides, stops, tgts, hold, cost=0.30):
    rows = []
    for i, sd, st, tg in zip(sig_idx, sides, stops, tgts):
        k = i + 1
        if k >= len(o) - 1:
            continue
        ent = o[k]
        risk = (ent - st) * sd
        if risk <= 0:
            continue
        tgt = ent + sd * tg if tg is not None else ent + sd * 2 * risk
        ex = None
        for j in range(k, min(k + hold, len(o))):
            if (sd == 1 and lo[j] <= st) or (sd == -1 and hi[j] >= st):
                ex = st
                break
            if (sd == 1 and hi[j] >= tgt) or (sd == -1 and lo[j] <= tgt):
                ex = tgt
                break
        if ex is None:
            ex = cl[min(k + hold - 1, len(o) - 1)]
        rows.append(dict(t_in=h1.index[k], side=sd, r=((ex - ent) * sd - 2 * cost) / risk))
    return pd.DataFrame(rows)


ix = h1.index
# rule A
ia, sa, sta = [], [], []
for e_ in ev:
    b = ix.searchsorted(e_.floor("h"))
    if b < len(ix) and ix[b] == e_.floor("h") and not np.isnan(atr[b]) and hi[b] - lo[b] > 1.5 * atr[b]:
        sd = 1 if cl[b] > o[b] else -1
        ia.append(b); sa.append(sd); sta.append(lo[b] if sd == 1 else hi[b])
A = run_rule(ia, sa, sta, [None] * len(ia), 8)
# rule B
rng_ = hi - lo
pos = np.where(rng_ > 0, (cl - lo) / np.where(rng_ > 0, rng_, 1), 0.5)
mB = (rng_ > 2 * atr) & ((pos >= 0.75) | (pos <= 0.25))
ib = np.where(mB)[0]
sb = np.where(pos[ib] >= 0.75, 1, -1)
B = run_rule(ib, sb, [o[i + 1] - s * atr[i + 1] if i + 1 < len(o) else np.nan for i, s in zip(ib, sb)],
             [2 * atr[i + 1] if i + 1 < len(o) else None for i in ib], 12)
B = B.dropna()


def rule_stats(x):
    if len(x) == 0:
        return dict(n=0)
    a, b = x[x.t_in < MID], x[x.t_in >= MID]
    f = lambda y: dict(n=len(y), avg_r=round(float(y.r.mean()), 3), win=round(float((y.r > 0).mean() * 100), 1),
                       t=round(float(stats.ttest_1samp(y.r, 0).statistic), 2) if len(y) > 2 else None) if len(y) else dict(n=0)
    return dict(all=f(x), h1=f(a), h2=f(b), long=f(x[x.side == 1]), short=f(x[x.side == -1]))


res["spike_A_news_breakout"] = rule_stats(A)
res["spike_B_atr_expansion"] = rule_stats(B)
res["spike_B_no_cost"] = rule_stats(run_rule(ib, sb, [o[i + 1] - s * atr[i + 1] if i + 1 < len(o) else np.nan for i, s in zip(ib, sb)],
                                             [2 * atr[i + 1] if i + 1 < len(o) else None for i in ib], 12, cost=0.0).dropna())
res["events_in_window"] = int(len(ev))

# 7 ---------- risk improvements (fit Y1, test after) ----------
fit, test = t[t.t_in < Y1], t[t.t_in >= Y1]
tdays = DAYS[DAYS >= Y1]
fd = pd.DataFrame({s: daily(fit[fit.strategy == s], days=DAYS[DAYS < Y1]) for s in strats})
res["corr_y1_daily"] = dict(mean_offdiag=round(float((fd.corr().values.sum() - len(strats)) / (len(strats) ** 2 - len(strats))), 3),
                             top_pairs=sorted([(a, b, round(float(fd.corr().loc[a, b]), 2)) for a, b in combinations(strats, 2)],
                                              key=lambda z: -z[2])[:6])
keep = [s for s in strats if fit[fit.strategy == s].pnl.sum() > 0]
vol = fd.std().replace(0, np.nan)
ivw = (1 / vol).fillna(0)
ivw = ivw / ivw[ivw > 0].mean()


def eval_test(x):
    s = stat(x, days=tdays)
    d = daily(x, days=tdays)
    return dict(pnl=s["pnl"], maxdd=s["maxdd"], sharpe=s["sharpe"], ret_dd=round(s["pnl"] / START * 100 / max(s["maxdd"], 1e-9), 2),
                worst_day=s["worst_day"], n=s["n"], ann_vol_pct=round(float(d.std() * np.sqrt(252) / START * 100), 2))


ri = {"baseline": eval_test(test)}
ri["a_drop_neg_y1"] = eval_test(test[test.strategy.isin(keep)]) | dict(dropped=[s for s in strats if s not in keep])
w = test.strategy.map(ivw)
ri["b_inverse_vol"] = eval_test(test.assign(pnl=test.pnl * w))
w2 = test.strategy.map(ivw.where(ivw.index.isin(keep), 0))
w2 = w2 / w2[w2 > 0].mean()
ri["e_drop_plus_invvol"] = eval_test(test.assign(pnl=test.pnl * w2)[w2 > 0])
# vol targeting
alld = daily(t)
rv = alld.rolling(20).std().shift(1)
tgt = float(rv[rv.index < Y1].median())
scale = (tgt / rv).clip(0.5, 2).fillna(1)
sc = test.t_in.dt.normalize().map(lambda d: scale.asof(d) if d >= scale.index[0] else 1.0)
ri["c_vol_target"] = eval_test(test.assign(pnl=test.pnl * sc.values))
# concurrency cap
def conc(x, k=2):
    x = x.sort_values("t_in")
    keepm, opened = [], []
    for ti, to, sd in zip(x.t_in, x.t_out, x.side):
        opened = [(a, b) for a, b in opened if a > ti]
        if sum(1 for _, b2 in opened if b2 == sd) >= k:
            keepm.append(False)
            continue
        opened.append((to, sd))
        keepm.append(True)
    return x[np.array(keepm)]


ri["d_max2_same_side"] = eval_test(conc(test, 2))
ri["d_max1_same_side"] = eval_test(conc(test, 1))
# same tests in Y1 (in-sample) for reference
ri["IS_baseline_y1"] = dict(pnl=round(float(fit.pnl.sum()), 0), maxdd=stat(fit, DAYS[DAYS < Y1])["maxdd"],
                            sharpe=stat(fit, DAYS[DAYS < Y1])["sharpe"])
res["risk"] = ri
res["vol_target_level_usd_day"] = round(tgt, 1)

# 8 ---------- monthly ----------
mo = t.groupby(t.t_out.dt.to_period("M")).pnl.sum()
mo_post = t[t.t_in >= SEL].groupby(t.t_out.dt.to_period("M")).pnl.sum()
bs = [rng.choice(mo.values, len(mo)).mean() for _ in range(5000)]
res["monthly"] = dict(mean=round(float(mo.mean()), 0), median=round(float(mo.median()), 0), pos=f"{int((mo > 0).sum())}/{len(mo)}",
                      worst=round(float(mo.min()), 0), best=round(float(mo.max()), 0),
                      boot_ci90=[round(float(np.percentile(bs, 5)), 0), round(float(np.percentile(bs, 95)), 0)],
                      post_sel_mean=round(float(mo_post.mean()), 0), post_sel_pos=f"{int((mo_post > 0).sum())}/{len(mo_post)}")
(OUT / "results.json").write_text(json.dumps(res, indent=1, default=str))
print("ok")

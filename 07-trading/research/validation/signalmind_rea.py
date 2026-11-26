"""A344: what SignalMind's public Gold AI pages show, rebuilt from the outside and tested on our gold data.
Taken from their own pages only (signalmind.app/gold, /gold-faq, /gold-results, read 26 Nov 2026):
  XAUUSD, 15-minute chart with H1/H4 context; setups = Squeeze Momentum, Hidden Divergence, Supertrend H4,
  Trend Pulse H1, Smart Breakout, Trend Rider, London / New York Judas sweeps, LIT POI; targets 1:1 and 1:2;
  no new signals Fri 18:00 - Mon 02:00 UTC; they suggest 1% risk per trade.
Their code is not public, so each setup is rebuilt from its standard public definition (LazyBear squeeze,
RSI hidden divergence, Supertrend 10/3, EMA pullback, ICT Judas sweep). Our history is 1h bars, so the
15-minute setups run on 1h (stated in the report). Rules were fixed before any result was seen.
Step 1 replays their 60 published signals on our 1h prices to check their record.
Step 2 backtests each rebuilt setup alone, after $0.40 cost, split before / after 2025-09-01.
Step 3 adds only setups that are positive in BOTH halves to our E8 bot at weight 0.5, then reruns the E8 test."""
import json, sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
sys.argv = [sys.argv[0], "10000"]
import numpy as np, pandas as pd
import video_tweaks as V
b, em = V.b, V.em
COST = 0.40
SPLIT = pd.Timestamp("2025-09-01")


def atr(d, n=14):
    tr = np.maximum(d.high - d.low, np.maximum((d.high - d.close.shift()).abs(), (d.low - d.close.shift()).abs()))
    return tr.rolling(n).mean()


def trade_out(d, i, side, stop, rr, hold):
    """Enter at bar i+1 open; stop first if both are touched in one bar (conservative)."""
    if i + 1 >= len(d):
        return None
    o, h, l, c = d.open.values, d.high.values, d.low.values, d.close.values
    px = o[i + 1]; risk = (px - stop) * side
    if risk <= 0.5:
        return None
    tgt = px + side * rr * risk
    for j in range(i + 1, min(i + 1 + hold, len(d))):
        if (l[j] <= stop) if side > 0 else (h[j] >= stop):
            return j, -1.0 - COST / risk
        if (h[j] >= tgt) if side > 0 else (l[j] <= tgt):
            return j, rr - COST / risk
    j = min(i + hold, len(d) - 1)
    return j, (c[j] - px) * side / risk - COST / risk


def closed_window(ts):
    wd, hr = ts.weekday(), ts.hour
    return (wd == 4 and hr >= 18) or wd == 5 or (wd == 6) or (wd == 0 and hr < 2)


def collect(d, sigs, name, rr, hold=24):
    rows, busy = [], -1
    for i, side, stop in sigs:
        if i <= busy or closed_window(d.index[i]):
            continue
        r = trade_out(d, i, side, stop, rr, hold)
        if r:
            busy = r[0]
            rows.append(dict(t_in=d.index[i + 1], t_out=d.index[r[0]], side=side, r=r[1], strategy=name))
    return pd.DataFrame(rows, columns=["t_in", "t_out", "side", "r", "strategy"])


def squeeze(d):                      # LazyBear: BB(20,2) inside KC(20,1.5) -> fire on release, side = momentum
    m = d.close.rolling(20).mean(); sd = d.close.rolling(20).std(); a = atr(d, 20)
    on = (m + 2 * sd < m + 1.5 * a) & (m - 2 * sd > m - 1.5 * a)
    mid = ((d.high.rolling(20).max() + d.low.rolling(20).min()) / 2 + m) / 2
    x = np.arange(20)
    mom = (d.close - mid).rolling(20).apply(lambda v: np.polyfit(x, v, 1)[0] * 19 + np.polyfit(x, v, 1)[1], raw=True)
    a14 = atr(d)
    return [(i, 1 if mom.iloc[i] > 0 else -1, d.close.iloc[i] - 1.5 * a14.iloc[i] * (1 if mom.iloc[i] > 0 else -1))
            for i in range(40, len(d)) if on.iloc[i - 1] and not on.iloc[i] and not np.isnan(mom.iloc[i])]


def rsi(c, n=14):
    g = c.diff().clip(lower=0).ewm(alpha=1 / n).mean(); l = (-c.diff().clip(upper=0)).ewm(alpha=1 / n).mean()
    return 100 - 100 / (1 + g / l)


def hidden_div(d, k=5):              # trend continuation: price higher low + RSI lower low (and mirror)
    r = rsi(d.close); e50, e200 = d.close.ewm(span=50).mean(), d.close.ewm(span=200).mean(); a = atr(d)
    lo, hi = d.low.values, d.high.values; out, pl, ph = [], [], []
    for i in range(2 * k, len(d)):
        p = i - k                              # pivot confirmed k bars later (no look-ahead)
        if lo[p] == lo[p - k:p + k + 1].min():
            if pl and lo[p] > lo[pl[-1]] and r.iloc[p] < r.iloc[pl[-1]] and e50.iloc[i] > e200.iloc[i]:
                out.append((i, 1, lo[p] - 0.2 * a.iloc[i]))
            pl.append(p)
        if hi[p] == hi[p - k:p + k + 1].max():
            if ph and hi[p] < hi[ph[-1]] and r.iloc[p] > r.iloc[ph[-1]] and e50.iloc[i] < e200.iloc[i]:
                out.append((i, -1, hi[p] + 0.2 * a.iloc[i]))
            ph.append(p)
    return out


def supertrend(d, n=10, m=3.0):
    a = atr(d, n); hl = (d.high + d.low) / 2; up, dn = (hl - m * a).to_numpy().copy(), (hl + m * a).to_numpy().copy()
    c = d.close.values; st = np.full(len(d), np.nan); dirn = np.ones(len(d)); out = []
    for i in range(n + 1, len(d)):
        up[i] = max(up[i], up[i - 1]) if c[i - 1] > up[i - 1] else up[i]
        dn[i] = min(dn[i], dn[i - 1]) if c[i - 1] < dn[i - 1] else dn[i]
        dirn[i] = 1 if c[i] > dn[i - 1] else (-1 if c[i] < up[i - 1] else dirn[i - 1])
        if dirn[i] != dirn[i - 1]:
            out.append((i, int(dirn[i]), up[i] if dirn[i] > 0 else dn[i]))
    return out


def trend_pulse(d):                  # EMA20 > EMA50, low tags EMA20, closes back above (and mirror)
    e20, e50, a = d.close.ewm(span=20).mean(), d.close.ewm(span=50).mean(), atr(d); out = []
    for i in range(60, len(d)):
        if e20.iloc[i] > e50.iloc[i] and d.low.iloc[i] <= e20.iloc[i] < d.close.iloc[i]:
            out.append((i, 1, d.close.iloc[i] - 1.5 * a.iloc[i]))
        elif e20.iloc[i] < e50.iloc[i] and d.high.iloc[i] >= e20.iloc[i] > d.close.iloc[i]:
            out.append((i, -1, d.close.iloc[i] + 1.5 * a.iloc[i]))
    return out


def judas(d, rng_hours, sweep_hours):  # ICT: take out the earlier session's high/low, close back inside -> fade
    out = []; a = atr(d)
    for day, g in d.groupby(d.index.date):
        rg = g[g.index.hour.isin(rng_hours)]; sw = g[g.index.hour.isin(sweep_hours)]
        if len(rg) < 3 or sw.empty:
            continue
        H, L = rg.high.max(), rg.low.min(); done = False
        for t, row in sw.iterrows():
            i = d.index.get_loc(t)
            if not done and row.high > H and row.close < H:
                out.append((i, -1, row.high + 0.2 * a.iloc[i])); done = True
            elif not done and row.low < L and row.close > L:
                out.append((i, 1, row.low - 0.2 * a.iloc[i])); done = True
    return out


def verify_their_record(h1):
    """Replay the 60 signals listed on /gold-results (26 Nov 2026) on our 1h bars."""
    rows = json.loads((HERE / "signalmind_published.json").read_text())
    agree = n = 0; diffs = []
    for s in rows:
        t = pd.Timestamp(s["t"]).floor("h"); side = 1 if s["side"] == "BUY" else -1
        d = h1[h1.index >= t]
        if d.empty:
            continue
        diffs.append(abs(d.open.iloc[0] - s["entry"]))
        res = None
        for _, r in d.iloc[:96].iterrows():
            if (r.low <= s["stop"]) if side > 0 else (r.high >= s["stop"]):
                res = "STOPPED"; break
            if (r.high >= s["target"]) if side > 0 else (r.low <= s["target"]):
                res = "TARGET"; break
        if res:
            n += 1; agree += res == s["result"]
    return dict(signals_checked=n, same_outcome=agree, median_entry_gap=round(float(np.median(diffs)), 2))


def main():
    fr = b.frames(); h1, h4 = fr["1h"], fr["4h"]
    rep = {"their_record_on_our_prices": verify_their_record(h1)}
    print(rep, flush=True)
    setups = {"SM Squeeze 1h": (h1, squeeze), "SM HiddenDiv 1h": (h1, hidden_div), "SM Supertrend 4h": (h4, supertrend),
              "SM TrendPulse 1h": (h1, trend_pulse),
              "SM Judas London 1h": (h1, lambda d: judas(d, range(0, 7), range(7, 10))),
              "SM Judas NY 1h": (h1, lambda d: judas(d, range(7, 13), range(13, 16)))}
    alone, keep = {}, []
    for name, (d, fn) in setups.items():
        sig = fn(d)
        for rr in (1.0, 2.0):
            t = collect(d, sig, f"{name.rsplit(' ', 1)[0]} 1:{rr:g} {name.rsplit(' ', 1)[1]}", rr, hold=24 if d is h1 else 12)
            a, bb = t[t.t_in < SPLIT].r, t[t.t_in >= SPLIT].r
            row = dict(trades=len(t), win=round(float((t.r > 0).mean()), 3) if len(t) else None,
                       avg_r=round(float(t.r.mean()), 3) if len(t) else None,
                       avg_r_before=round(float(a.mean()), 3) if len(a) else None,
                       avg_r_after=round(float(bb.mean()), 3) if len(bb) else None,
                       usd_at_0_30pct=round(float(t.r.sum() * 30)))
            alone[f"{name} 1:{rr:g}"] = row; print(name, rr, row, flush=True)
            if len(a) >= 30 and len(bb) >= 30 and a.mean() > 0.05 and bb.mean() > 0.05:
                keep.append(t)
    rep["alone"] = alone
    base_t = V.trades(fr)
    rep["base"] = V.evaluate(base_t, fr, dict(V.KW, mix_risk=0.003), name="our bot (E8, 0.30%)")
    if keep:
        add = pd.concat(keep)
        w = dict(em.WEIGHTS_2026_11_21, **{s: 0.5 for s in add.strategy.unique()})
        rep["added"] = sorted(add.strategy.unique())
        rep["with_signalmind"] = V.evaluate(pd.concat([base_t, add]).reset_index(drop=True), fr,
                                            dict(V.KW, mix_risk=0.003, weights=w), name="our bot + passing SignalMind setups")
    pathlib.Path("reports/signalmind-rea-2026-11-26.json").write_text(json.dumps(rep, indent=1, default=str))


if __name__ == "__main__":
    main()

"""A338/A340: ideas from Akhil's videos (26 Nov 2026), tested on the final E8 Pro $10K bot.
Every rule below was written BEFORE looking at results; nothing is tuned to the data.
  K  Kronos filter (Tsinghua Kronos-mini, MIT; trained on data up to June 2024, our data starts July 2024 = unseen):
     at each entry, 256 past 1h candles -> 5 sampled paths 12h ahead -> P(up). K1 keep only trades Kronos agrees
     with (P(side) >= 0.5); K2 drop only trades Kronos strongly disagrees with (P(side) <= 0.2).
  R  "Opposite of last week" (the video's finding that Kronos ~= short-term reversal): R1 keep only trades against
     the last 120h move; R2 drop trades WITH the last 120h move only when that move was > 2%.
  N  Nearby settings (5th hedge-fund check): MSNR level width k 1/3 (base 2), reward:risk 1.6/2.4 (base 2.0),
     wait/hold x0.7 and x1.3, risk 0.30%/0.50% (base 0.40%), min stop $1.20/$1.80 (base $1.50).
Usage: python3 video_tweaks.py 10000 [kronos|reversal|nearby|all]"""
import json, sys, pathlib, time
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import numpy as np, pandas as pd
import e8_pro_5k as E                      # reads sys.argv[1] = account size
import ea_mix_scenarios as S
em, b = S.em, S.b
INIT = E.INIT
KW = dict(mix_risk=0.004, weights=em.WEIGHTS_2026_11_21, friday_cut=0.0125, gap_pct=0.0375, gap_budget=0.03,
          extra_cost=0.30, min_stop=1.5, lot_cap=0.10, day_stop_eq=0.015, eq_floor=INIT * 0.93,
          day_profit_cap=0.02, margin_lev=15.0)
LIVE = [k for k, w in em.WEIGHTS_2026_11_21.items() if w > 0 and k in em.MIX]
SPLIT = pd.Timestamp("2025-09-01")
OUT = pathlib.Path(f"reports/video-tweaks-{sys.argv[2] if len(sys.argv) > 2 else 'all'}-2026-11-26.json")


def trades(fr, msnr_params=None):
    if msnr_params:
        orig = b.msnr_trades
        def patched(x, tf, setup, side, rand_seed=None, P=msnr_params):
            real = b.g.clean(x); df = b.mirror(real) if side == "short" else real
            zs = b.mr.filt(b.SETUPS[setup](df, k=P.get("k", 2), storyline_on=False), real, df, True, side)
            w, h = {"1h": (20, 48), "2h": (10, 24), "4h": (10, 20)}[tf]
            from src.smc import simulate
            t = simulate(df, zs, wait=max(1, round(w * P.get("wait", 1))), hold=max(1, round(h * P.get("hold", 1))),
                         rr=P.get("rr", 2.0), cost=b.MSNR_COST / float(real.close.mean()))
            if t.empty:
                return pd.DataFrame(columns=["t_in", "t_out", "side", "r"])
            return pd.DataFrame(dict(t_in=df.index[t.entry_bar.values], t_out=df.index[t.exit_bar.values],
                                     side=1 if side == "long" else -1, r=t.r.values))
        b.msnr_trades = patched
    try:
        cand = b.candidates(fr)
        mix = pd.concat([cand[k]().assign(strategy=k) for k in LIVE])
    finally:
        if msnr_params:
            b.msnr_trades = orig
    ea = em.ea_rules_trades(fr)[["t_in", "t_out", "side", "r", "strategy"]]
    return pd.concat([mix[["t_in", "t_out", "side", "r", "strategy"]], ea]).reset_index(drop=True)


def evaluate(allt, fr, kw=KW, name=""):
    p, mt, ck = S.run(allt, fr, kw)
    d = S.daily_table(ck)
    m = p.groupby(pd.to_datetime(p.t_close).dt.to_period("M")).pnl.sum()
    a = E.sim(d); pas = a[a.result == "pass"]; fin = a[a.result != "open"]; full = pas[pas.full] if len(pas) else pas
    tc = pd.to_datetime(p.t_close)
    r = dict(name=name, trades=len(p), net_usd=round(float(p.pnl.sum())), net_before_split=round(float(p.pnl[tc < SPLIT].sum())),
             net_after_split=round(float(p.pnl[tc >= SPLIT].sum())), positive_months=f"{int((m > 0).sum())}/{len(m)}",
             worst_month=round(float(m.min())), worst_day=round(float(d.low.min())), lowest_equity=round(float(ck['eq'].min())),
             pass_pct=round(len(pas) / max(len(fin), 1) * 100, 1),
             days_to_pass=float(pas.days.median()) if len(pas) else None,
             funded_breach_pct=round(float(full.funded_breach.mean() * 100), 1) if len(full) else None,
             payouts_6m=float(full.payouts_usd.median()) if len(full) else None)
    print(json.dumps(r), flush=True)
    return r


def kronos_probs(allt, h1, paths=5, ahead=12, ctx=256):
    sys.path.insert(0, "/tmp/kronos")
    import torch
    from model import Kronos, KronosTokenizer, KronosPredictor
    torch.set_num_threads(2)
    tok = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-2k"); mdl = Kronos.from_pretrained("NeoQuasar/Kronos-mini")
    tok.eval(); mdl.eval()                                   # the video's fix: predict in eval mode, not training mode
    pr = KronosPredictor(mdl, tok, device="cpu", max_context=2048)
    cache = pathlib.Path("/tmp/kronos_probs.json")
    done = json.loads(cache.read_text()) if cache.exists() else {}
    h = h1.copy(); h["volume"] = 0.0
    keys = sorted({str(t) for t in pd.to_datetime(allt.t_in).dt.floor("h")} - set(done))
    t0 = time.time()
    for i in range(0, len(keys), 8):
        batch = []
        for k in keys[i:i + 8]:
            ctxdf = h[h.index < pd.Timestamp(k)].iloc[-ctx:]
            if len(ctxdf) < ctx:
                done[k] = 0.5; continue
            batch.append((k, ctxdf))
        if batch:
            xs = [c[["open", "high", "low", "close", "volume"]].reset_index(drop=True) for _, c in batch]
            xts = [pd.Series(c.index) for _, c in batch]
            yts = [pd.Series(pd.date_range(c.index[-1], periods=ahead + 1, freq="h")[1:]) for _, c in batch]
            ups = np.zeros(len(batch))
            with torch.no_grad():
                for _ in range(paths):
                    out = pr.predict_batch(xs, xts, yts, pred_len=ahead, T=1.0, top_p=0.9, sample_count=1, verbose=False)
                    ups += np.array([o["close"].iloc[-1] > x["close"].iloc[-1] for o, x in zip(out, xs)])
            for (k, _), u in zip(batch, ups):
                done[k] = float(u / paths)
        if i % 80 == 0:
            cache.write_text(json.dumps(done)); print(f"kronos {i}/{len(keys)} {time.time()-t0:.0f}s", flush=True)
    cache.write_text(json.dumps(done))
    pu = pd.to_datetime(allt.t_in).dt.floor("h").astype(str).map(done).astype(float)
    return np.where(allt.side.values > 0, pu, 1 - pu)        # P(trade's own direction)


def main():
    what = sys.argv[2] if len(sys.argv) > 2 else "all"
    fr = b.frames(); h1 = fr["1h"]
    res = json.loads(OUT.read_text()) if OUT.exists() else {}
    allt = trades(fr)
    if "base" not in res:
        res["base"] = evaluate(allt, fr, name="final bot (E8 $10K)")
    if what in ("reversal", "all"):
        past = h1.close.pct_change(120)
        mv = past.reindex(pd.to_datetime(allt.t_in).dt.floor("h"), method="ffill").values
        against = np.sign(mv) != allt.side.values
        res["R1"] = evaluate(allt[against].reset_index(drop=True), fr, name="R1 only trades against last week")
        res["R2"] = evaluate(allt[~((~against) & (np.abs(mv) > 0.02))].reset_index(drop=True), fr,
                             name="R2 skip trades with a >2% last-week move")
        OUT.write_text(json.dumps(res, indent=1))
    if what in ("nearby", "all"):
        for nm, P in [("k1", {"k": 1}), ("k3", {"k": 3}), ("rr1.6", {"rr": 1.6}), ("rr2.4", {"rr": 2.4}),
                      ("wait0.7", {"wait": 0.7}), ("wait1.3", {"wait": 1.3}), ("hold0.7", {"hold": 0.7}), ("hold1.3", {"hold": 1.3})]:
            res["N_" + nm] = evaluate(trades(fr, P), fr, name="nearby " + nm)
            OUT.write_text(json.dumps(res, indent=1))
        for nm, ch in [("risk0.30", {"mix_risk": 0.003}), ("risk0.50", {"mix_risk": 0.005}),
                       ("minstop1.2", {"min_stop": 1.2}), ("minstop1.8", {"min_stop": 1.8})]:
            res["N_" + nm] = evaluate(allt, fr, dict(KW, **ch), name="nearby " + nm)
            OUT.write_text(json.dumps(res, indent=1))
    if what in ("kronos", "all"):
        ps = kronos_probs(allt, h1)
        res["K1"] = evaluate(allt[ps >= 0.5].reset_index(drop=True), fr, name="K1 only trades Kronos agrees with")
        res["K2"] = evaluate(allt[~(ps <= 0.2)].reset_index(drop=True), fr, name="K2 skip trades Kronos strongly rejects")
        hit = pd.Series(ps >= 0.5)
        res["K_info"] = dict(agree_share=round(float(hit.mean()), 3),
                             avg_r_agree=round(float(allt.r[hit.values].mean()), 3),
                             avg_r_disagree=round(float(allt.r[~hit.values].mean()), 3))
        print(res["K_info"])
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

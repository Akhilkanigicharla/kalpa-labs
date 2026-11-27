"""What would the final bot do right now? Fresh 1h gold (GC=F) from Yahoo, the 7 live MSNR strategies with their
live weights, 0.30% risk on $10K. Lists (1) trades the bot would be holding now and (2) limit orders it would
have waiting, with entry, stop, target and lot size. The main EA+MSNR strategy (rare, ~2 trades/month) is not
replayed here. Price alignment (Akhil 27 Nov 2026: "live market price and our bot should be same"): Yahoo's GC=F is the
NEXT futures contract (Feb), which trades ~$25-30 above spot gold. Levels are shifted to spot by the gap
between GC=F and the nearest contract (FRONT, e.g. GCZ26 = Dec 2026) at their last common minute, and the live
XAUUSD spot quote from Swissquote's free public feed is used to say what each trade looks like right now.
On the live server none of this is needed: the EA reads E8's own XAUUSD prices tick by tick."""
import sys, pathlib, json
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent.parent))
import pandas as pd
import ea_msnr_gold as m
m.CACHE = pathlib.Path("/tmp/gc_h1_today.parquet"); m.CACHE.unlink(missing_ok=True)
import best_combo_gold as b
import ea_mix_backtest as em
from src.smc import simulate
W = em.WEIGHTS_2026_11_21
RISK = 0.003 * 10000


FRONT = "GCZ26.CMX"          # nearest gold futures contract; roll to GCG27.CMX after late-Dec expiry


def live_spot():
    import urllib.request
    u = "https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD"
    with urllib.request.urlopen(u, timeout=20) as r:
        p = json.loads(r.read())[0]["spreadProfilePrices"][0]
    return round((p["bid"] + p["ask"]) / 2, 2), round(p["bid"], 2), round(p["ask"], 2)


def basis():
    import yfinance as yf
    a = yf.download("GC=F", period="2d", interval="1m", progress=False)["Close"].iloc[:, 0]
    f = yf.download(FRONT, period="2d", interval="1m", progress=False)["Close"].iloc[:, 0]
    j = pd.concat([a, f], axis=1, join="inner").dropna()
    return round(float(j.iloc[-1, 0] - j.iloc[-1, 1]), 2), str(j.index[-1])


def run():
    fr = b.frames(); out = []
    last = fr["1h"].index[-1]
    for name, w in W.items():
        if w <= 0 or not name.startswith("MSNR"):
            continue
        _, setup, side, tf = name.split()
        x = fr[tf]; real = b.g.clean(x); df = b.mirror(real) if side == "short" else real
        zs = b.mr.filt(b.SETUPS[setup](df, k=2, storyline_on=False), real, df, True, side)
        wait, hold = {"1h": (20, 48), "2h": (10, 24), "4h": (10, 20)}[tf]
        t = simulate(df, zs, wait=wait, hold=hold, rr=2.0, cost=b.MSNR_COST / float(real.close.mean()))
        conv = (lambda p: 1 / p) if side == "short" else (lambda p: p)
        n = len(df)
        busy = int(t.exit_bar.max()) if len(t) else -1
        for _, r in t.iterrows():                                   # still open at the last bar?
            if r.exit_bar == n - 1 and r.entry_bar + hold > n - 1:
                z = next(z for z in zs if z.known_at == r.known_at)
                tgt_m = r.entry + 2 * (z.top - z.stop)
                stop_px, tgt_px = conv(z.stop), conv(tgt_m)
                lots = RISK * w / (abs(conv(r.entry) - stop_px) * 100)
                out.append(dict(status="OPEN", strategy=name, side=("SELL" if side == "short" else "BUY"),
                                filled_utc=str(df.index[int(r.entry_bar)]), entry=round(conv(r.entry), 2),
                                stop=round(stop_px, 2), target=round(tgt_px, 2),
                                time_exit_utc=str(df.index[int(r.entry_bar)] + pd.Timedelta(tf) * hold),
                                risk_usd=round(RISK * w, 1), lots=round(lots, 3),
                                bot_takes_it=bool(lots >= 0.01 or 0.01 * abs(conv(r.entry) - stop_px) * 100 <= 1.5 * RISK * w)))
        for z in zs:                                                # waiting limit orders
            if z.known_at <= busy or z.known_at < n - 1 - wait or z.top - z.stop <= 0:
                continue
            seg = df.iloc[z.known_at + 1:]
            if len(seg) and (seg.low <= z.top).any():
                continue                                            # would already have filled
            entry, stop = conv(z.top), conv(z.stop); tgt = conv(z.top + 2 * (z.top - z.stop))
            lots = RISK * w / (abs(entry - stop) * 100)
            out.append(dict(status="WAITING", strategy=name, side=("SELL LIMIT" if side == "short" else "BUY LIMIT"),
                            known=str(df.index[z.known_at]), expires_after_bars=wait - (n - 1 - z.known_at),
                            entry=round(entry, 2), stop=round(stop, 2), target=round(tgt, 2),
                            risk_usd=round(RISK * w, 1), lots=round(lots, 3),
                            bot_takes_it=bool(lots >= 0.01 or 0.01 * abs(entry - stop) * 100 <= 1.5 * RISK * w)))
    px = fr["1h"].iloc[-1]
    gap, gap_at = basis(); mid, bid, ask = live_spot()
    for o in out:                                    # to spot prices, then status at the live quote
        for k in ("entry", "stop", "target"):
            o[k] = round(o[k] - gap, 2)
        buy = o["side"].startswith("BUY")
        if o["status"] == "OPEN":
            if (bid <= o["stop"]) if buy else (ask >= o["stop"]):
                o["now"] = "STOPPED OUT by the live price"
            elif (bid >= o["target"]) if buy else (ask <= o["target"]):
                o["now"] = "TARGET HIT by the live price"
            else:
                o["now"] = f"still open, {'+' if (bid - o['entry']) * (1 if buy else -1) >= 0 else ''}{round((bid - o['entry']) * (1 if buy else -1), 2)} $/oz"
        else:
            o["now"] = "waiting" if ((ask > o["entry"]) if buy else (bid < o["entry"])) else "price is already through the entry"
    return dict(history_last_bar_utc=str(last), futures_last=round(float(px.close), 2), futures_minus_spot=gap,
                gap_measured_at=gap_at, live_spot_mid=mid, live_bid=bid, live_ask=ask,
                live_utc=str(pd.Timestamp.utcnow().floor("s")), signals=out)


if __name__ == "__main__":
    r = run(); print(json.dumps(r, indent=1, default=str))

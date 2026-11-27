"""Akhil 27 Nov 2026: "do back test for 20 years on both".
Same 13 strategies / scenario-G weights / R-based portfolio as btc_test.py, on long free histories:
  gold  : XAU/USD 1h 2004-06 .. 2025-07, HF dataset ZombitX64/xauusd-gold-price-historical-data-2004-2025
          (from Kaggle novandraanugrah/xauusd-gold-price-historical-data-2004-2024; broker-time bars)
  BTC   : BTCUSDT 1h 2017-08 .. 2026-10, Binance public archive data.binance.vision (BTC has no 20-year market)
Year-by-year results + first half vs second half. Research only, not investment advice."""
import glob, json, sys, pathlib, zipfile
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pandas as pd
import btc_test as T

DATA = pathlib.Path("/tmp/data20")


def gold():
    d = pd.read_json(DATA / "xau1h.jsonl", lines=True)
    d.index = pd.to_datetime(d.Date, format="%Y.%m.%d %H:%M")
    return T.e._ohlc(d[["Open", "High", "Low", "Close"]].sort_index())


def btc():
    parts = []
    for f in sorted(glob.glob(str(DATA / "btc" / "*.zip"))):
        with zipfile.ZipFile(f) as z:
            x = pd.read_csv(z.open(z.namelist()[0]), header=None, usecols=[0, 1, 2, 3, 4])
        x = x[pd.to_numeric(x[0], errors="coerce").notna()].astype(float)
        unit = "us" if x[0].iloc[0] > 1e14 else "ms"          # Binance spot files use microseconds from 2025
        x.index = pd.to_datetime(x[0].astype("int64"), unit=unit)
        parts.append(x[[1, 2, 3, 4]].set_axis(["Open", "High", "Low", "Close"], axis=1))
    return T.e._ohlc(pd.concat(parts).sort_index())


def by_year(name, h1, cost):
    t, _ = T.trades(h1, cost)
    t["y"] = pd.to_datetime(t.t_out).dt.year
    t["usd"] = t.r * t.w * T.RISK * 10_000
    years = {int(y): dict(**T.stats(g), usd=round(float(g.usd.sum()))) for y, g in t.groupby("y")}
    half = t.t_in.iloc[len(t) // 2]
    return dict(market=name, period=f"{h1.index[0].date()} to {h1.index[-1].date()}", cost_round_trip_pct=round(cost * 100, 3),
                all=T.stats(t), first_half=T.stats(t[t.t_in < half]), second_half=T.stats(t[t.t_in >= half]),
                years_positive=f"{sum(v['usd'] > 0 for v in years.values())}/{len(years)}", years=years,
                per_strategy={k: T.stats(g) for k, g in t.groupby("strategy")}, portfolio_0_30pct=T.portfolio(t))


def main():
    case = sys.argv[1]
    if case.startswith("gold"):
        h = gold(); c = 0.40 / float(h.close.tail(5000).mean()) * (2 if case.endswith("x2") else 1); name = "XAUUSD"
    else:
        h = btc(); c = 0.0005 * (2 if case.endswith("x2") else 1); name = "BTCUSDT"
    r = by_year(name, h, c)
    out = HERE.parent.parent / "reports" / f"long-history-{case}-2026-11-27.json"
    out.write_text(json.dumps(r, indent=1, default=str))
    print(case, r["period"], r["all"], "| halves", r["first_half"]["avg_r"], r["second_half"]["avg_r"],
          "| years+", r["years_positive"], "| worst drop", r["portfolio_0_30pct"]["worst_drop_usd"], flush=True)
    print("   ", {y: (s["avg_r"], s["usd"]) for y, s in r["years"].items()}, flush=True)


if __name__ == "__main__":
    main()

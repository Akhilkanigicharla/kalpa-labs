"""A280: Quant Brain, an intraday master agent over 25 strategy agents (Akhil 14 Nov 2026). PAPER ONLY.

Akhil: "AI quant trading master whose one task is to run as many trades as it can, up to 25, that make
profit on Rs 10k; a quant brain that explores different markets and charts and tests different intraday
strategies, based on market volume, sentiment, news, fundamentals, technicals and liquidity."

Setup (same as A275 so results compare): 5-minute bars, 20 liquid Nifty 50 stocks + NIFTYBEES + BANKBEES,
Rs 10,000 at 5x MIS = Rs 50,000 of positions, entry at the next bar's open + 0.02% slippage, stop assumed
first when one bar hits both, everything closed by 15:15, every NSE intraday charge (src/costs.py).

What each input means here (honest mapping; nothing is invented):
- technicals : EMA 9/21, VWAP, RSI(2)/(14), opening range, Bollinger squeeze, day high.
- volume     : bar volume vs its 20-bar average (relative volume).
- liquidity  : skip a bar whose range is > 1.5% (thin or news-shocked) and size by the Rs 50,000 limit.
- sentiment  : market breadth = share of the 22 symbols above their own VWAP, and NIFTYBEES vs its VWAP.
               Longs only when the market is above VWAP, shorts only when below.
- news       : no free archive of Indian intraday news exists (GDELT is unreachable from our cloud), so the
               measurable footprint of overnight news is used: the opening gap (gap-and-go, gap-fade).
- fundamentals: they change quarterly, so they cannot time 5-minute trades. They pick the universe:
               only large, liquid Nifty 50 companies. src/fundamentals.py scores a stock from its filings.

25 agents = 10 signal families x exits (5 families x 3 exits + 5 families x 2 exits). Each agent trades on
its own paper account every day, one position at a time.

Master agent ("brain"), every morning, using only past days:
- scores each agent by its net rupees (after charges) over the last 10 trading days, needing >= 5 trades;
- funds only agents with a positive score, money in proportion to score (max 50% per agent, total <= 100%);
- the account takes the funded agents' trades at that share of Rs 50,000, at most 25 trades a day;
- daily loss cap: stop for the day at -Rs 300 (3% of the account); no agent with a positive score = no trade.

Research:  python -m src.quant_brain --research
Paper:     python -m src.quant_brain --paper paper/quant-brain   (replays today's session after the close)
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from . import costs

IST = timezone(timedelta(hours=5, minutes=30))
ROOT = Path(__file__).resolve().parents[1]
NOTIONAL, CAPITAL, SLIP = 50_000.0, 10_000.0, 0.0002
MAX_TRADES_DAY, DAY_LOSS_CAP = 25, -300.0
SCORE_DAYS, MIN_TRADES, CAP_AGENT = 10, 5, 0.5
MAX_BAR_RANGE = 0.015
TICKERS = """RELIANCE HDFCBANK ICICIBANK INFY TCS SBIN BHARTIARTL AXISBANK KOTAKBANK LT ITC TATASTEEL
BAJFINANCE MARUTI SUNPHARMA HINDUNILVR M&M NTPC TATACONSUM ADANIPORTS NIFTYBEES BANKBEES""".split()
CACHE = ROOT / "data" / "a280" / "bars5m.parquet"


# ---------------- data ----------------
def _split(raw: pd.DataFrame) -> dict[str, pd.DataFrame]:
    out = {}
    for t in TICKERS:
        try:
            df = raw[f"{t}.NS"][["Open", "High", "Low", "Close", "Volume"]].dropna()
        except KeyError:
            continue
        df.columns = ["open", "high", "low", "close", "volume"]
        idx = pd.DatetimeIndex(df.index)
        df.index = idx.tz_convert("Asia/Kolkata").tz_localize(None) if idx.tz is not None else idx
        df = df[(df[["open", "high", "low", "close"]] > 0).all(axis=1)].between_time("09:15", "15:25")
        if len(df) > 300:
            out[t] = df
    return out


def load(refresh: bool = False) -> dict[str, pd.DataFrame]:
    """Last ~60 trading days of 5-min bars (Yahoo's free limit), cached outside git."""
    if CACHE.exists() and not refresh:
        raw = pd.read_parquet(CACHE)
    else:
        import yfinance as yf
        raw = yf.download([f"{t}.NS" for t in TICKERS], period="60d", interval="5m", progress=False,
                          auto_adjust=False, group_by="ticker", threads=True)
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        raw.to_parquet(CACHE)
    return _split(raw)


# ---------------- features ----------------
def features(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    day = d.index.date
    tp = (d.high + d.low + d.close) / 3
    d["vwap"] = (tp * d.volume).groupby(day).cumsum() / d.volume.groupby(day).cumsum().replace(0, np.nan)
    d["ema9"] = d.close.ewm(span=9, adjust=False).mean()
    d["ema21"] = d.close.ewm(span=21, adjust=False).mean()
    delta = d.close.diff()
    up, dn = delta.clip(lower=0), -delta.clip(upper=0)
    for n in (2, 14):
        rs = up.ewm(alpha=1 / n, adjust=False).mean() / dn.ewm(alpha=1 / n, adjust=False).mean().replace(0, np.nan)
        d[f"rsi{n}"] = 100 - 100 / (1 + rs)
    d["rvol"] = d.volume / d.volume.rolling(20).mean()
    d["bar_pos"] = (d.close - d.low) / (d.high - d.low).replace(0, np.nan)
    d["bar_range"] = (d.high - d.low) / d.close
    g = d.groupby(day)
    d["bar_no"] = g.cumcount()
    first = d[d.bar_no < 3]
    d["or_high"] = pd.Series(day, index=d.index).map(first.high.groupby(first.index.date).max())
    d["or_low"] = pd.Series(day, index=d.index).map(first.low.groupby(first.index.date).min())
    d["day_high"] = g.high.cummax()
    d["day_low"] = g.low.cummin()
    day_open = g.open.transform("first")
    prev_close = pd.Series(day, index=d.index).map(d.close.groupby(day).last().shift())
    d["gap"] = day_open / prev_close - 1
    d["from_open"] = d.close / day_open - 1
    ma, sd = d.close.rolling(20).mean(), d.close.rolling(20).std()
    d["bb_width"] = 4 * sd / ma
    d["bb_up"], d["bb_dn"] = ma + 2 * sd, ma - 2 * sd
    d["sqz"] = d.bb_width < d.bb_width.rolling(100).quantile(0.2)
    return d


def market_context(feat: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Sentiment per bar: breadth (share of symbols above VWAP) and NIFTYBEES vs VWAP / open."""
    above = pd.DataFrame({t: (f.close > f.vwap) for t, f in feat.items()})
    nb = feat["NIFTYBEES"]
    return pd.DataFrame({"breadth": above.mean(axis=1),
                         "mkt_up": (nb.close > nb.vwap).reindex(above.index).ffill().fillna(False).astype(bool),
                         "mkt_ret": nb.from_open.reindex(above.index).ffill()})


# ---------------- signals: +1 long, -1 short on the CLOSED bar ----------------
def s_ema(d, m):
    up = (d.ema9 > d.ema21) & (d.ema9.shift() <= d.ema21.shift()) & (d.close > d.vwap)
    dn = (d.ema9 < d.ema21) & (d.ema9.shift() >= d.ema21.shift()) & (d.close < d.vwap)
    return up.astype(int) - dn.astype(int)


def s_vwap_revert(d, m):
    return (((d.close <= d.vwap * 0.996) & (d.rsi14 < 30)).astype(int)
            - ((d.close >= d.vwap * 1.004) & (d.rsi14 > 70)).astype(int))


def s_volume(d, m):
    return (((d.close > d.open) & (d.bar_pos > 0.75) & (d.rvol > 3)).astype(int)
            - ((d.close < d.open) & (d.bar_pos < 0.25) & (d.rvol > 3)).astype(int))


def s_orb(d, m):
    after = d.bar_no >= 3
    return ((after & (d.close > d.or_high) & (d.close.shift() <= d.or_high)).astype(int)
            - (after & (d.close < d.or_low) & (d.close.shift() >= d.or_low)).astype(int))


def s_rsi2(d, m):
    return ((d.rsi2 < 5) & (d.close > d.vwap)).astype(int) - ((d.rsi2 > 95) & (d.close < d.vwap)).astype(int)


def s_gap_go(d, m):
    """News footprint: a gap over 1% that holds after 15 minutes, traded in the gap's direction."""
    t = d.bar_no == 3
    return ((t & (d.gap > 0.01) & (d.close > d.or_high * 0.999)).astype(int)
            - (t & (d.gap < -0.01) & (d.close < d.or_low * 1.001)).astype(int))


def s_gap_fade(d, m):
    t = d.bar_no == 3
    return ((t & (d.gap < -0.01) & (d.close > d.or_high)).astype(int)
            - (t & (d.gap > 0.01) & (d.close < d.or_low)).astype(int))


def s_breadth(d, m):
    """Sentiment: most of the market above VWAP and this stock reclaims its VWAP (mirror for shorts)."""
    b = m.breadth.reindex(d.index)
    return (((b > 0.7) & (d.close > d.vwap) & (d.close.shift() <= d.vwap.shift())).astype(int)
            - ((b < 0.3) & (d.close < d.vwap) & (d.close.shift() >= d.vwap.shift())).astype(int))


def s_squeeze(d, m):
    sq = d.sqz.shift().fillna(False).astype(bool)
    return ((sq & (d.close > d.bb_up) & (d.rvol > 1.5)).astype(int)
            - (sq & (d.close < d.bb_dn) & (d.rvol > 1.5)).astype(int))


def s_rel_strength(d, m):
    """Stock beats the market since the open by 0.5% and makes a new day high (mirror for shorts)."""
    rel = d.from_open - m.mkt_ret.reindex(d.index)
    nh = d.high >= d.day_high.shift()
    nl = d.low <= d.day_low.shift()
    return (((rel > 0.005) & nh & (d.bar_no >= 6)).astype(int)
            - ((rel < -0.005) & nl & (d.bar_no >= 6)).astype(int))


@dataclass(frozen=True)
class Agent:
    name: str
    signal: Callable
    tp: float
    sl: float


_E3 = [(0.004, 0.002), (0.006, 0.003), (0.010, 0.005)]
_E2 = [(0.006, 0.003), (0.010, 0.005)]
AGENTS: list[Agent] = (
    [Agent(f"{n}_{int(tp*1000)}/{int(sl*1000)}", f, tp, sl)
     for n, f in [("ema_vwap", s_ema), ("vwap_revert", s_vwap_revert), ("volume_spike", s_volume),
                  ("orb", s_orb), ("rsi2", s_rsi2)] for tp, sl in _E3]
    + [Agent(f"{n}_{int(tp*1000)}/{int(sl*1000)}", f, tp, sl)
       for n, f in [("gap_go", s_gap_go), ("gap_fade", s_gap_fade), ("breadth", s_breadth),
                    ("squeeze", s_squeeze), ("rel_strength", s_rel_strength)] for tp, sl in _E2]
)
assert len(AGENTS) == 25 and len({a.name for a in AGENTS}) == 25


# ---------------- simulation ----------------
def _filtered(sig: pd.Series, d: pd.DataFrame, m: pd.DataFrame) -> pd.Series:
    """Liquidity + market-direction filters shared by every agent."""
    up = m.mkt_up.reindex(d.index).fillna(False).astype(bool)
    ok = d.bar_range <= MAX_BAR_RANGE
    return sig.where(ok, 0).where(~((sig > 0) & ~up), 0).where(~((sig < 0) & up), 0).fillna(0).astype(int)


def agent_trades(feat: dict[str, pd.DataFrame], m: pd.DataFrame, agent: Agent) -> pd.DataFrame:
    """One position at a time; when flat take the signal with the highest relative volume."""
    syms = list(feat)
    sigs = {t: _filtered(agent.signal(feat[t], m), feat[t], m) for t in syms}
    times = m.index
    arr = {t: feat[t].reindex(times) for t in syms}
    S = {t: sigs[t].reindex(times).fillna(0).to_numpy() for t in syms}
    O = {t: arr[t].open.to_numpy() for t in syms}
    H = {t: arr[t].high.to_numpy() for t in syms}
    L = {t: arr[t].low.to_numpy() for t in syms}
    C = {t: arr[t].close.to_numpy() for t in syms}
    RV = {t: np.nan_to_num(arr[t].rvol.to_numpy()) for t in syms}
    tod = times.time
    dates = times.date
    t1515, t1505 = pd.Timestamp("15:15").time(), pd.Timestamp("15:05").time()
    pos, out = None, []
    for i in range(len(times) - 1):
        if pos is not None:
            t = pos["sym"]
            if i > pos["i_in"] and not np.isnan(C[t][i]):
                s = pos["side"]
                hit_sl = L[t][i] <= pos["sl"] if s > 0 else H[t][i] >= pos["sl"]
                hit_tp = H[t][i] >= pos["tp"] if s > 0 else L[t][i] <= pos["tp"]
                px = pos["sl"] if hit_sl else pos["tp"] if hit_tp else None
                if px is None and (tod[i] >= t1515 or dates[i + 1] != dates[i]):
                    px = C[t][i]
                if px is not None:
                    out.append(_close(pos, px, times[i]))
                    pos = None
            continue
        if tod[i] >= t1505 or dates[i + 1] != dates[i]:
            continue
        best = None
        for t in syms:
            s = S[t][i]
            if s and not np.isnan(O[t][i + 1]) and (best is None or RV[t][i] > best[2]):
                best = (t, int(s), RV[t][i])
        if best:
            t, s, _ = best
            px = O[t][i + 1] * (1 + SLIP * s)
            qty = math.floor(NOTIONAL / px)
            if qty > 0:
                pos = {"sym": t, "side": s, "qty": qty, "px": px, "i_in": i + 1, "t_in": times[i + 1],
                       "tp": px * (1 + agent.tp * s), "sl": px * (1 - agent.sl * s)}
    df = pd.DataFrame(out)
    if not df.empty:
        df.insert(0, "agent", agent.name)
    return df


def _close(pos: dict, exit_px: float, ts) -> dict:
    exit_px *= 1 - SLIP * pos["side"]
    buy, sell = (pos["px"], exit_px) if pos["side"] > 0 else (exit_px, pos["px"])
    return {"day": ts.date(), "t_in": pos["t_in"], "t_out": ts, "sym": pos["sym"], "side": pos["side"],
            "qty": pos["qty"], "buy": buy, "sell": sell, "gross": (exit_px - pos["px"]) * pos["qty"] * pos["side"],
            "charges": costs.intraday(buy * pos["qty"], sell * pos["qty"]).total}


def all_trades(feat, m) -> pd.DataFrame:
    parts = [agent_trades(feat, m, a) for a in AGENTS]
    tr = pd.concat([p for p in parts if not p.empty], ignore_index=True)
    tr["net"] = tr.gross - tr.charges
    return tr


def allocation(tr: pd.DataFrame, days: list, day) -> pd.Series:
    """Master's money per agent for `day`, from the previous SCORE_DAYS days only."""
    i = days.index(day)
    past = set(days[max(0, i - SCORE_DAYS):i])
    p = tr[tr.day.isin(past)]
    g = p.groupby("agent").net.agg(["sum", "count"])
    sc = g["sum"].where((g["count"] >= MIN_TRADES) & (g["sum"] > 0), 0.0)
    sc = sc[sc > 0]
    if sc.empty or i < SCORE_DAYS:
        return pd.Series(dtype=float)
    w = (sc / sc.sum()).clip(upper=CAP_AGENT)
    return w


def master_day(tr: pd.DataFrame, w: pd.Series, day) -> pd.DataFrame:
    """Take funded agents' trades for one day in time order, scaled by their money share,
    with the 25-trade limit and the daily loss cap."""
    today = tr[(tr.day == day) & tr.agent.isin(w.index)].sort_values("t_in")
    rows, pnl, n = [], 0.0, 0
    for r in today.itertuples():
        if n >= MAX_TRADES_DAY or pnl <= DAY_LOSS_CAP:
            break
        f = float(w[r.agent])
        q = math.floor(r.qty * f)
        if q < 1:
            continue
        gross = (r.sell - r.buy) * q
        ch = costs.intraday(r.buy * q, r.sell * q).total
        rows.append({"day": day, "agent": r.agent, "sym": r.sym, "side": r.side, "qty": q,
                     "gross": gross, "charges": ch, "net": gross - ch})
        pnl += gross - ch
        n += 1
    return pd.DataFrame(rows)


def run_master(tr: pd.DataFrame, days: list) -> pd.DataFrame:
    out = []
    for d in days[SCORE_DAYS:]:
        w = allocation(tr, days, d)
        md = master_day(tr, w, d) if not w.empty else pd.DataFrame()
        out.append(md if not md.empty else pd.DataFrame([{"day": d, "agent": None, "net": 0.0,
                                                          "gross": 0.0, "charges": 0.0, "qty": 0}]))
    return pd.concat(out, ignore_index=True)


def day_summary(tr: pd.DataFrame, days: list) -> dict:
    real = tr[tr.qty > 0] if "qty" in tr else tr
    daily = tr.groupby("day").net.sum().reindex(days, fill_value=0.0)
    return {"days": len(days), "trades": int(len(real)), "trades_per_day": round(len(real) / len(days), 1),
            "win_rate_%": round(100 * (real.net > 0).mean(), 1) if len(real) else 0.0,
            "gross_rs": round(real.gross.sum()), "charges_rs": round(real.charges.sum()),
            "net_rs": round(real.net.sum()), "net_per_day_rs": round(daily.mean(), 1),
            "best_day_rs": round(daily.max()), "worst_day_rs": round(daily.min()),
            "green_days_%": round(100 * (daily > 0).mean(), 1),
            "no_trade_days": int((tr.groupby("day").qty.sum().reindex(days, fill_value=0) == 0).sum())
            if "qty" in tr else 0}


def research(out_dir: Path) -> dict:
    data = load()
    feat = {t: features(d) for t, d in data.items()}
    m = market_context(feat)
    tr = all_trades(feat, m)
    days = sorted(set(m.index.date))
    test = days[SCORE_DAYS:]
    master = run_master(tr, days)
    rows = [{"line": "Quant Brain master (score-funded agents, <=25 trades/day, -Rs300 day cap)",
             **day_summary(master, test)}]
    per = []
    for a in AGENTS:
        t = tr[(tr.agent == a.name) & tr.day.isin(test)].assign(qty=1)
        per.append({"agent": a.name, **day_summary(t, test)})
    per = pd.DataFrame(per).sort_values("net_rs", ascending=False)
    allt = tr[tr.day.isin(test)].assign(qty=1)
    rows.append({"line": "All 25 agents, each on its own full Rs 50,000 (no master)", **day_summary(allt, test)})
    best = per.iloc[0]
    rows.append({"line": f"Best single agent, picked AFTER the fact ({best.agent})",
                 **{k: best[k] for k in per.columns if k != "agent"}})
    summ = pd.DataFrame(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    summ.to_csv(out_dir / "a280_summary.csv", index=False)
    per.to_csv(out_dir / "a280_agents.csv", index=False)
    funded = pd.Series({d: len(allocation(tr, days, d)) for d in test})
    return {"summary": summ, "per": per, "funded": funded, "span": (days[0], days[-1]), "tr": tr, "days": days}


def paper(out: Path) -> str:
    """After the close: replay today with the agents the master funded this morning (past days only)."""
    data = load(refresh=True)
    feat = {t: features(d) for t, d in data.items()}
    m = market_context(feat)
    tr = all_trades(feat, m)
    days = sorted(set(m.index.date))
    today = days[-1]
    w = allocation(tr, days, today)
    md = master_day(tr, w, today) if not w.empty else pd.DataFrame()
    out.mkdir(parents=True, exist_ok=True)
    net = float(md.net.sum()) if not md.empty else 0.0
    state = {"date": str(today), "run_ist": datetime.now(IST).strftime("%Y-%m-%d %H:%M"), "paper_only": True,
             "funded": {k: round(float(v), 3) for k, v in w.items()}, "trades": int(len(md)),
             "net_rs": round(net, 2), "charges_rs": round(float(md.charges.sum()), 2) if not md.empty else 0.0}
    (out / "state.json").write_text(json.dumps(state, indent=1))
    log = out / "log.csv"
    row = pd.DataFrame([{k: state[k] for k in ("date", "trades", "net_rs", "charges_rs")}
                        | {"funded_agents": len(w)}])
    if log.exists():
        old = pd.read_csv(log)
        row = pd.concat([old[old.date.astype(str) != state["date"]], row], ignore_index=True)
    row.to_csv(log, index=False)
    return (f"Quant Brain paper {today} (PAPER ONLY): {len(w)} agents funded, {len(md)} trades, "
            f"net Rs {net:.0f} after charges")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--research", action="store_true")
    ap.add_argument("--paper", type=Path)
    a = ap.parse_args(argv)
    if a.research:
        r = research(ROOT / "research")
        pd.set_option("display.width", 250)
        print(r["summary"].to_string(index=False))
        print(r["per"].to_string(index=False))
        print("funded agents per day: mean", round(r["funded"].mean(), 1), "max", r["funded"].max(),
              "days with none", int((r["funded"] == 0).sum()), r["span"])
    if a.paper:
        print(paper(a.paper))


if __name__ == "__main__":
    main()

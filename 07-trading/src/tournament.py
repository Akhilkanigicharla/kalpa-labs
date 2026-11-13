"""A279: 25-strategy tournament with a master agent (Akhil 14 Nov 2026). PAPER ONLY.

Akhil: "25 trades, 25 different strategies, see which strategy works quicker; if it works, increase
trades; based on the chart and market increase and decrease trades; a master agent that maintains
the strategies, with a number of agents testing in each market and time frame."

How it works
- 25 strategy agents. Each is one fixed rule on one market (5 NSE ETFs). The rules and settings are
  fixed here BEFORE any result is seen (no tuning on the test years). Every agent paper-trades every
  day on its own, so each one has a live score even when the master gives it no money.
- Master agent. Every Friday it scores each agent on its last 126 trading days (excess return over
  cash divided by risk, after charges). Agents with a score above MIN_SCORE get money in proportion
  to their score, max 15% each, max 40% per market. Losers get zero ("benched") but keep paper-trading,
  so a benched agent comes back when it starts working again. More money to a winner = bigger trades;
  more agents scoring well = more trades.
- Risk agent. If the whole account falls 12% from its peak, every position is halved until the fall
  is back under 6%. Agents on the same ETF are netted, so the account only trades the net change.
- Costs: every NSE delivery charge, 0.1% slippage each side, Rs 15.34 DP charge per ETF sold per day
  on a Rs 10,000 account, idle cash 4.7%/yr (liquid ETF). Signal at close, trade next close.

Run research:  python -m src.tournament --research
Paper (daily): python -m src.tournament --paper paper/tournament
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from . import costs, data, strategies as S

IST = timezone(timedelta(hours=5, minutes=30))
MARKETS = ["NIFTYBEES", "BANKBEES", "JUNIORBEES", "GOLDBEES", "MON100"]
CAPITAL = 10_000.0
CASH_RATE = 0.047
SLIPPAGE = 0.001
LOOKBACK = 126         # master scoring window (trading days)
MIN_SCORE = 0.25       # yearly excess Sharpe an agent needs before it gets money
CAP_AGENT = 0.15
CAP_MARKET = 0.40
DD_BRAKE, DD_RELEASE = 0.12, 0.06
BAND = 0.05            # no-trade band: change a market only when it moves 5% of the account (Rs 500)
START = "2012-01-01"


# ---------- extra rules (long only, weight 0..1) ----------
def rsi(close: pd.Series, n: int) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d).clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def rsi2_reversion(close: pd.Series, trend: int = 200, buy: float = 10, sell: float = 70) -> pd.Series:
    """Connors-style: in an uptrend, buy when RSI(2) is very low, sell when it recovers."""
    r, up = rsi(close, 2), close > close.rolling(trend).mean()
    w = pd.Series(np.nan, index=close.index)
    w[(r < buy) & up] = 1.0
    w[(r > sell) | ~up] = 0.0
    return w.ffill().fillna(0.0)


def bollinger_reversion(close: pd.Series, n: int = 20, k: float = 2.0, trend: int = 200) -> pd.Series:
    ma, sd = close.rolling(n).mean(), close.rolling(n).std()
    up = close > close.rolling(trend).mean()
    w = pd.Series(np.nan, index=close.index)
    w[(close < ma - k * sd) & up] = 1.0
    w[(close > ma) | ~up] = 0.0
    return w.ffill().fillna(0.0)


def macd(close: pd.Series, fast: int = 12, slow: int = 26, sig: int = 9) -> pd.Series:
    line = close.ewm(span=fast, adjust=False).mean() - close.ewm(span=slow, adjust=False).mean()
    return (line > line.ewm(span=sig, adjust=False).mean()).astype(float).where(close.notna(), 0.0)


def high52(close: pd.Series, near: float = 0.95, exit_ma: int = 100) -> pd.Series:
    """Hold while price is within 5% of its 52-week high; leave below the 100-day average."""
    hi = close.rolling(252).max()
    w = pd.Series(np.nan, index=close.index)
    w[close >= near * hi] = 1.0
    w[close < close.rolling(exit_ma).mean()] = 0.0
    return w.ffill().fillna(0.0)


@dataclass(frozen=True)
class Agent:
    name: str
    market: str
    rule: Callable[[pd.Series], pd.Series]


def _reg(name: str, **kw) -> Callable[[pd.Series], pd.Series]:
    return lambda c: S.weights(name, c, **kw)


AGENTS: list[Agent] = [
    # Nifty 50 (NIFTYBEES): 10 agents
    Agent("nifty_tsmom252", "NIFTYBEES", _reg("tsmom", lookback=252)),
    Agent("nifty_tsmom126", "NIFTYBEES", _reg("tsmom", lookback=126)),
    Agent("nifty_ma200", "NIFTYBEES", _reg("ma_filter", window=200)),
    Agent("nifty_ma100", "NIFTYBEES", _reg("ma_filter", window=100)),
    Agent("nifty_turtle55", "NIFTYBEES", _reg("turtle", entry=55, exit=20)),
    Agent("nifty_ema12_50", "NIFTYBEES", _reg("ema_cross", fast=12, slow=50)),
    Agent("nifty_rsi2", "NIFTYBEES", rsi2_reversion),
    Agent("nifty_bollinger", "NIFTYBEES", bollinger_reversion),
    Agent("nifty_macd", "NIFTYBEES", macd),
    Agent("nifty_regime200", "NIFTYBEES", _reg("regime_filter", trend=200, vol_cap=0.20)),
    # Bank Nifty (BANKBEES): 5
    Agent("bank_tsmom252", "BANKBEES", _reg("tsmom", lookback=252)),
    Agent("bank_ma200", "BANKBEES", _reg("ma_filter", window=200)),
    Agent("bank_turtle20", "BANKBEES", _reg("turtle", entry=20, exit=10)),
    Agent("bank_rsi2", "BANKBEES", rsi2_reversion),
    Agent("bank_macd", "BANKBEES", macd),
    # Nifty Next 50 (JUNIORBEES): 3
    Agent("junior_tsmom252", "JUNIORBEES", _reg("tsmom", lookback=252)),
    Agent("junior_ma150", "JUNIORBEES", _reg("ma_filter", window=150)),
    Agent("junior_high52", "JUNIORBEES", high52),
    # Gold (GOLDBEES): 4
    Agent("gold_hold", "GOLDBEES", _reg("hold")),
    Agent("gold_tsmom126", "GOLDBEES", _reg("tsmom", lookback=126)),
    Agent("gold_ma200", "GOLDBEES", _reg("ma_filter", window=200)),
    Agent("gold_turtle55", "GOLDBEES", _reg("turtle", entry=55, exit=20)),
    # Nasdaq 100 (MON100): 3
    Agent("us_hold", "MON100", _reg("hold")),
    Agent("us_tsmom252", "MON100", _reg("tsmom", lookback=252)),
    Agent("us_ema12_50", "MON100", _reg("ema_cross", fast=12, slow=50)),
]
assert len(AGENTS) == 25 and len({a.name for a in AGENTS}) == 25


# ---------- data ----------
def load_prices(start: str = START, cache_dir: str | None = None) -> pd.DataFrame:
    cols = {}
    for m in MARKETS:
        df = data.get_daily(m, strict=False, cache_dir=cache_dir)
        df = df[(df[["open", "high", "low", "close"]] > 0).all(axis=1)]
        df, _ = data.repair_spikes(df)
        cols[m] = df["close"]
    px = pd.DataFrame(cols).sort_index()
    px = px[px.index >= pd.Timestamp(start)].ffill()
    return px.dropna()


# ---------- engine ----------
def banded(exposure: pd.DataFrame, band: float = BAND) -> pd.DataFrame:
    """Only trade a market when the wanted position differs from what we hold by at least `band`
    of the account, or when an agent wants it fully closed. Stops tiny trades that the Rs 15.34
    DP charge per sell would eat (first run without a band: gross 14.7%/yr, charges 17.0%/yr)."""
    if band <= 0:
        return exposure
    vals = exposure.to_numpy(copy=True)
    cur = vals[0].copy()                 # the first row is what we already hold
    for i in range(1, len(vals)):
        want = vals[i]
        move = (np.abs(want - cur) >= band) | ((want < 1e-6) & (cur > 0))
        cur = np.where(move, want, cur)
        if cur.sum() > 1 + 1e-9:       # stale holdings + new buys would spend more than the account
            cur = want.copy()
        vals[i] = cur
    return pd.DataFrame(vals, index=exposure.index, columns=exposure.columns)


def _rates() -> tuple[float, float, float]:
    b, s = costs.delivery_side_rates()
    return b + SLIPPAGE, s + SLIPPAGE, costs.rate("dp_per_scrip_sell") / CAPITAL


def signals(px: pd.DataFrame) -> pd.DataFrame:
    """Each agent's wanted position (0..1) at each close."""
    return pd.DataFrame({a.name: a.rule(px[a.market]).reindex(px.index).fillna(0.0).clip(0, 1)
                         for a in AGENTS})


def _account(px: pd.DataFrame, exposure: pd.DataFrame) -> pd.DataFrame:
    """Daily net return of an account whose wanted exposure per market (decided at close t) is
    `exposure`; traded at close t+1. Returns columns: ret, cost, invested, sells."""
    b, s, dp = _rates()
    held = exposure.shift(1).fillna(0.0)
    r = px.pct_change().fillna(0.0)
    cash_d = (1 + CASH_RATE) ** (1 / 252) - 1
    gross = (held * r).sum(axis=1) + (1 - held.sum(axis=1)).clip(lower=0) * cash_d
    change = held.shift(-1).fillna(held.iloc[-1]) - held
    buys, sells = change.clip(lower=0), (-change).clip(lower=0)
    sell_days = (sells > 1e-4).sum(axis=1)
    cost = (b * buys).sum(axis=1) + (s * sells).sum(axis=1) + dp * sell_days
    return pd.DataFrame({"ret": gross - cost, "cost": cost, "invested": held.sum(axis=1),
                         "trades": (change.abs() > 1e-4).sum(axis=1)})


def agent_returns(px: pd.DataFrame, sig: pd.DataFrame) -> pd.DataFrame:
    """Each agent alone with the whole account (its own paper track, used for scoring)."""
    out = {}
    for a in AGENTS:
        exp = pd.DataFrame(0.0, index=px.index, columns=px.columns)
        exp[a.market] = sig[a.name]
        out[a.name] = _account(px, exp)["ret"]
    return pd.DataFrame(out)


def score(rets: pd.DataFrame, lookback: int = LOOKBACK) -> pd.DataFrame:
    """Yearly Sharpe of return above cash over the last `lookback` days (0 when flat)."""
    cash_d = (1 + CASH_RATE) ** (1 / 252) - 1
    ex = rets - cash_d
    mu, sd = ex.rolling(lookback).mean(), ex.rolling(lookback).std()
    sc = (mu / sd.where(sd > 1e-9)) * np.sqrt(252)
    return sc.fillna(0.0)


def allocate(sc_row: pd.Series, min_score: float = MIN_SCORE) -> pd.Series:
    """Master agent: money in proportion to score, capped per agent and per market."""
    w = sc_row.where(sc_row > min_score, 0.0)
    if w.sum() <= 0:
        return w * 0.0
    w = (w / w.sum()).clip(upper=CAP_AGENT)
    mk = pd.Series({a.name: a.market for a in AGENTS})
    for m in MARKETS:
        tot = w[mk == m].sum()
        if tot > CAP_MARKET:
            w[mk == m] *= CAP_MARKET / tot
    return w


def master_weights(sc: pd.DataFrame, *, min_score: float = MIN_SCORE, warmup: int = LOOKBACK) -> pd.DataFrame:
    """Weekly (Friday or last day of the week) allocations, held until the next rebalance."""
    idx = sc.index
    week_end = pd.Series(idx, index=idx).groupby(idx.to_period("W")).transform("max") == idx
    w = pd.DataFrame(np.nan, index=idx, columns=sc.columns)
    for i, t in enumerate(idx):
        if i >= warmup and week_end.iloc[i]:
            w.loc[t] = allocate(sc.loc[t], min_score).values
    return w.ffill().fillna(0.0)


def run_master(px: pd.DataFrame, sig: pd.DataFrame, rets: pd.DataFrame, *, lookback: int = LOOKBACK,
               min_score: float = MIN_SCORE, brake: bool = True, band: float = BAND
               ) -> tuple[pd.DataFrame, pd.DataFrame]:
    sc = score(rets, lookback)
    w = master_weights(sc, min_score=min_score, warmup=lookback)
    mk = {a.name: a.market for a in AGENTS}
    contrib = sig * w                                  # each agent's slice of the account in the market
    exposure = contrib.T.groupby(mk).sum().T.reindex(columns=px.columns, fill_value=0.0)
    if brake:
        exposure = _with_brake(px, exposure)
    acct = _account(px, banded(exposure, band))
    return acct, w


def _with_brake(px: pd.DataFrame, exposure: pd.DataFrame) -> pd.DataFrame:
    """Risk agent: halve exposure after a 12% fall from peak, restore when the fall is under 6%.
    Decided day by day from the account's own past returns (no look-ahead)."""
    b, s, dp = _rates()
    r = px.pct_change().fillna(0.0)
    cash_d = (1 + CASH_RATE) ** (1 / 252) - 1
    out = exposure.copy()
    eq, peak, braked = 1.0, 1.0, False
    prev_held = pd.Series(0.0, index=px.columns)
    for i, t in enumerate(px.index):
        held = prev_held
        day = float((held * r.loc[t]).sum() + max(0.0, 1 - held.sum()) * cash_d)
        eq *= 1 + day
        peak = max(peak, eq)
        dd = 1 - eq / peak
        if not braked and dd > DD_BRAKE:
            braked = True
        elif braked and dd < DD_RELEASE:
            braked = False
        want = exposure.loc[t] * (0.5 if braked else 1.0)
        out.loc[t] = want
        chg = want - held
        eq *= 1 - float((b * chg.clip(lower=0)).sum() + (s * (-chg).clip(lower=0)).sum()
                        + dp * ((-chg) > 1e-4).sum())
        prev_held = want
    return out


# ---------- stats ----------
def stats(ret: pd.Series, trades: pd.Series | None = None) -> dict:
    ret = ret.dropna()
    yrs = len(ret) / 252
    eq = (1 + ret).cumprod()
    cagr = eq.iloc[-1] ** (1 / yrs) - 1 if yrs > 0 else np.nan
    dd = (eq / eq.cummax() - 1).min()
    yearly = (1 + ret).groupby(ret.index.year).prod() - 1
    out = {"cagr": cagr, "max_dd": dd, "worst_year": yearly.min(),
           "sharpe": ret.mean() / ret.std() * np.sqrt(252) if ret.std() > 0 else 0.0,
           "end_value": CAPITAL * eq.iloc[-1]}
    if trades is not None:
        out["trades_per_year"] = trades.loc[ret.index].sum() / yrs
    return out


def research(out_dir: Path, test_start: str = "2019-01-01") -> dict:
    px = load_prices()
    sig = signals(px)
    rets = agent_returns(px, sig)
    acct, w = run_master(px, sig, rets)
    first = px.index[LOOKBACK]   # master needs LOOKBACK days before its first allocation
    periods = {"2013-2026 (after warm-up)": first, "2019-2026": pd.Timestamp(test_start)}

    rows = []
    # baselines
    mk = {a.name: a.market for a in AGENTS}
    eq_exp = (sig / 25).T.groupby(mk).sum().T.reindex(columns=px.columns, fill_value=0.0)
    eq_acct = _account(px, banded(eq_exp))
    bot_exp = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    bot_exp["NIFTYBEES"] = 0.5 * sig["nifty_tsmom252"]
    bot_exp["GOLDBEES"] = 0.5
    bot_acct = _account(px, bot_exp)
    nifty_exp = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    nifty_exp["NIFTYBEES"] = 1.0
    nifty_acct = _account(px, nifty_exp)
    nobrake, _ = run_master(px, sig, rets, brake=False)
    noband, _ = run_master(px, sig, rets, band=0.0)
    lines = {"Master agent (25 agents, weekly, risk brake)": acct,
             "Master agent without the risk brake": nobrake,
             "Master agent with no trade band (first run)": noband,
             "All 25 agents, equal money (4% each), same band": eq_acct,
             "Current bot: Nifty trend 50% + gold held 50%": bot_acct,
             "Buy and hold Nifty (NIFTYBEES)": nifty_acct}
    for label, a in lines.items():
        for p, t0 in periods.items():
            st = stats(a["ret"].loc[t0:], a["trades"])
            yrs = len(a.loc[t0:]) / 252
            rows.append({"line": label, "period": p, **st,
                         "charges_pct_per_year": a["cost"].loc[t0:].sum() / yrs,
                         "avg_invested": a["invested"].loc[t0:].mean()})
    summary = pd.DataFrame(rows)

    # sensitivity of the master's two settings (reported, not used to choose)
    sens = []
    for lb in (63, 126, 252):
        for ms in (0.0, 0.25, 0.5):
            for bd in (0.05, 0.10):
                a, _ = run_master(px, sig, rets, lookback=lb, min_score=ms, band=bd)
                st = stats(a["ret"].loc[pd.Timestamp(test_start):], a["trades"])
                sens.append({"lookback": lb, "min_score": ms, "band": bd, **st})
    sens = pd.DataFrame(sens)

    # per agent, 2019-2026, plus how often and how much the master funded it
    trades_agent = {}
    for ag in AGENTS:
        ch = sig[ag.name].shift(1).diff().abs()
        trades_agent[ag.name] = ch
    per = []
    t0 = pd.Timestamp(test_start)
    for ag in AGENTS:
        st = stats(rets[ag.name].loc[t0:])
        per.append({"agent": ag.name, "market": ag.market, **st,
                    "trades_per_year": float((trades_agent[ag.name].loc[t0:] > 0.01).sum() / (len(rets.loc[t0:]) / 252)),
                    "weeks_funded_pct": float((w[ag.name].loc[t0:] > 0).mean()),
                    "avg_money_pct": float(w[ag.name].loc[t0:].mean())})
    per = pd.DataFrame(per).sort_values("cagr", ascending=False)
    active = (w > 0).sum(axis=1)

    out_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_dir / "a279_summary.csv", index=False, float_format="%.4f")
    sens.to_csv(out_dir / "a279_sensitivity.csv", index=False, float_format="%.4f")
    per.to_csv(out_dir / "a279_agents.csv", index=False, float_format="%.4f")
    return {"summary": summary, "sens": sens, "per": per, "active": active.loc[t0:],
            "span": (px.index[0].date(), px.index[-1].date())}


# ---------- daily paper run ----------
def paper(out: Path, flags: Path | None = None) -> str:
    """Today's master decision on paper: scores, money per agent, wanted ETF positions in rupees.
    No broker, no keys. A KILL flag file means: report only, no new buys."""
    px = load_prices()
    sig = signals(px)
    rets = agent_returns(px, sig)
    sc = score(rets)
    t = px.index[-1]
    w = allocate(sc.loc[t])
    mk = {a.name: a.market for a in AGENTS}
    exposure = (sig.loc[t] * w).groupby(mk).sum().reindex(MARKETS, fill_value=0.0)
    kill = bool(flags and (flags / "KILL").exists())
    out.mkdir(parents=True, exist_ok=True)
    prev_path = out / "state.json"
    prev = pd.Series(0.0, index=MARKETS)
    if prev_path.exists():
        old = json.loads(prev_path.read_text()).get("positions_rs", {})
        prev = pd.Series({m: old.get(m, 0) / CAPITAL for m in MARKETS})
    both = pd.DataFrame([prev, exposure], columns=MARKETS)
    exposure = banded(both).iloc[-1]                  # same Rs 500 no-trade band as the backtest
    if kill:                                          # KILL: no new buys, sells still allowed
        exposure = exposure.where(exposure <= prev, prev)
    state = {"date": str(t.date()), "run_ist": datetime.now(IST).strftime("%Y-%m-%d %H:%M"),
             "kill": kill, "paper_only": True,
             "agents": [{"agent": a.name, "market": a.market, "score": round(float(sc.loc[t, a.name]), 3),
                         "money_pct": round(float(w[a.name]) * 100, 2), "signal": float(sig.loc[t, a.name])}
                        for a in AGENTS],
             "positions_rs": {m: round(float(exposure[m]) * CAPITAL) for m in MARKETS},
             "cash_rs": round(CAPITAL * (1 - float(exposure.sum())))}
    (out / "state.json").write_text(json.dumps(state, indent=1))
    log = out / "log.csv"
    row = pd.DataFrame([{"date": state["date"], **{f"{m}_rs": v for m, v in state["positions_rs"].items()},
                         "cash_rs": state["cash_rs"], "funded_agents": int((w > 0).sum()), "kill": kill}])
    if log.exists():
        old = pd.read_csv(log)
        if state["date"] in old["date"].astype(str).values:
            old = old[old["date"].astype(str) != state["date"]]
        row = pd.concat([old, row], ignore_index=True)
    row.to_csv(log, index=False)
    top = sorted(state["agents"], key=lambda x: -x["money_pct"])[:8]
    lines = [f"Tournament paper run {state['date']} (PAPER ONLY{', KILL on' if kill else ''})",
             f"Funded agents: {int((w > 0).sum())} of 25"]
    lines += [f"- {a['agent']}: {a['money_pct']}% (score {a['score']})" for a in top if a["money_pct"] > 0]
    lines.append("Wanted positions: " + ", ".join(f"{m} Rs{v}" for m, v in state["positions_rs"].items())
                 + f", cash Rs{state['cash_rs']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--research", action="store_true")
    ap.add_argument("--paper", type=Path)
    ap.add_argument("--flags", type=Path)
    a = ap.parse_args(argv)
    if a.research:
        res = research(Path(__file__).resolve().parents[1] / "research")
        pd.set_option("display.width", 200)
        print(res["summary"].round(3).to_string(index=False))
        print(res["sens"].round(3).to_string(index=False))
        print(res["per"].round(3).to_string(index=False))
        print("active agents (2019-26): mean", round(res["active"].mean(), 1),
              "min", res["active"].min(), "max", res["active"].max(), res["span"])
    if a.paper:
        print(paper(a.paper, a.flags))


if __name__ == "__main__":
    main()

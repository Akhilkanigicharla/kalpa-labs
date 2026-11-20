"""MSNR (Malaysian support & resistance) setups, tested honestly (Akhil, 20 Nov 2026). PAPER ONLY.

Source: Akhil's playlist "MSNR basics (english)" by Sujith Surya (youtube.com/playlist?list=PLItFSHK6vT0Y,
36 videos, GBPUSD intraday). The videos could not be watched from the cloud (YouTube bot wall), so the
rules below come from the playlist's video titles plus two public, open-source MSNR implementations
that agree with each other (TradingView: "MSNR Key Levels Pro [Abusuhil]", "MSnR Fresh & Unfresh
Level", "MSnR QM Level"; read 20 Nov 2026). Notes: research/msnr-2026-11-20.md.

Levels come from candle CLOSES, not wicks (the MSNR rule):
  A level  green candle then red candle -> resistance at the green candle's close.
  V level  red candle then green candle -> support at the red candle's close.
  key      with k > 0 only "key" levels are kept: the close is the highest (A) / lowest (V) close of
           the k bars on each side, so the level is known only k bars after the pair (no look-ahead).
State (checked on every later bar):
  fresh    not touched since it formed or flipped.
  unfresh  a wick touched it and the close stayed on its side (rejection).
  flip     a close through the level turns resistance into support (RBS) or support into resistance
           (SBR), and the flipped level is fresh again.
Storyline: the higher-timeframe (weekly) direction. It turns up when a finished weekly candle
rejects a weekly support or closes above a weekly resistance, and down on the mirror image.

Setups (long only: no overnight shorts in Indian cash; zones go to smc.simulate, stop first, 2R target):
  fresh_v     buy the FIRST touch of a fresh support (V level or flipped A level = RBS)   [videos 4, 10]
  qm          buy the retest of a Buy QM level (V level, broken down, A level broken up) [videos 5, 6]
  eq_sweep    two equal V levels (within 0.15 ATR), a candle wicks below both and closes
              back above them: buy the retest of that close                              [video 9, setup 2]
Session setups (Asia range, 30-minute entries: setups 1, 4, 5, 7) need intraday bars and wait on A181.
Research code only. Not investment advice; nothing here trades real money.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .smc import Zone, _ohlc, atr, placebo, simulate, summarize

MARKETS = ["NIFTYBEES", "BANKBEES", "JUNIORBEES", "GOLDBEES", "MON100"]
SPLIT = "2019-01-01"          # in-sample before, test after; fixed before any result was seen
GRID = {"k": [2, 5], "storyline": [True, False]}       # 4 configs per setup (even, for PBO-style ranks)
PASS_RULES = {"min_test_trades": 30, "min_avg_r": 0.10, "min_pf": 1.2}


@dataclass
class Level:
    known_at: int        # bar whose close makes the level known
    price: float
    kind: str            # "A" (resistance) or "V" (support)
    origin: int          # first bar of the candle pair


def _colour(o: np.ndarray, c: np.ndarray) -> np.ndarray:
    return np.sign(c - o)          # +1 green, -1 red, 0 doji (forms no level)


def levels(df: pd.DataFrame, k: int = 0) -> list[Level]:
    """A and V levels from consecutive candle pairs, optionally only key (k-bar extreme) closes."""
    d = _ohlc(df)
    o, c = d.open.values, d.close.values
    col = _colour(o, c)
    out = []
    for i in range(1, len(d)):
        a, b = col[i - 1], col[i]
        if a == 1 and b == -1:
            kind = "A"
        elif a == -1 and b == 1:
            kind = "V"
        else:
            continue
        p = i - 1                                   # the candle whose close sets the level
        known = i
        if k:
            lo, hi = p - k, p + k + 1
            if lo < 0 or hi > len(d):
                continue
            win = c[lo:hi]
            if (kind == "A" and c[p] < win.max()) or (kind == "V" and c[p] > win.min()):
                continue
            known = max(i, p + k)
        out.append(Level(known, float(c[p]), kind, p))
    return out


def track(df: pd.DataFrame, lv: Level, start: int | None = None) -> list[tuple[int, str, str]]:
    """Events for one level after it is known: (bar, role, event) with event in
    fresh (formed or flipped), unfresh (wick touch + rejection)."""
    d = _ohlc(df)
    h, lo, c = d.high.values, d.low.values, d.close.values
    role = "support" if lv.kind == "V" else "resistance"
    ev = [(lv.known_at, role, "fresh")]
    for t in range((start or lv.known_at) + 1, len(d)):
        if role == "support":
            if c[t] < lv.price:
                role = "resistance"
                ev.append((t, role, "fresh"))
            elif lo[t] <= lv.price:
                ev.append((t, role, "unfresh"))
        else:
            if c[t] > lv.price:
                role = "support"
                ev.append((t, role, "fresh"))
            elif h[t] >= lv.price:
                ev.append((t, role, "unfresh"))
    return ev


def storyline(df: pd.DataFrame, k: int = 0) -> pd.Series:
    """Weekly storyline mapped to daily bars: +1 up, -1 down, 0 unknown. A week counts only once its
    last daily bar has closed, so day t never sees a week that is still running."""
    d = _ohlc(df)
    wk_id = d.index.to_period("W-FRI")
    last_bar = pd.Series(np.arange(len(d)), index=d.index).groupby(wk_id).max().values
    w = d.groupby(wk_id).agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
                             close=("close", "last"))
    w.index = w.index.to_timestamp()
    wl = levels(w, k)
    h, lo, c = w.high.values, w.low.values, w.close.values
    state = np.zeros(len(w))
    cur = 0.0
    for j in range(len(w)):
        for lv in wl:
            if lv.known_at >= j:            # only levels known before this week
                continue
            if lv.kind == "V" and lo[j] <= lv.price < c[j]:
                cur = 1.0                    # support rejected
            elif lv.kind == "A" and c[j] > lv.price and c[j - 1] <= lv.price:
                cur = 1.0                    # resistance broken
            elif lv.kind == "A" and h[j] >= lv.price > c[j]:
                cur = -1.0                   # resistance rejected
            elif lv.kind == "V" and c[j] < lv.price and c[j - 1] >= lv.price:
                cur = -1.0                   # support broken
        state[j] = cur
    daily = np.zeros(len(d))
    for j, b in enumerate(last_bar):
        daily[b:] = state[j]                 # known from the close of the week's last day onward
    return pd.Series(daily, index=d.index)


def _gate(zones: list[Zone], story: pd.Series | None) -> list[Zone]:
    if story is None:
        return zones
    s = story.values
    return [z for z in zones if s[z.known_at] > 0]


def fresh_v(df: pd.DataFrame, k: int = 2, storyline_on: bool = True) -> list[Zone]:
    """First touch of a fresh support: a V level, or an A level after it flips (RBS)."""
    d = _ohlc(df)
    a = atr(d).values
    c = d.close.values
    out = []
    for lv in levels(d, k):
        for t, role, e in track(d, lv):
            if role != "support" or e != "fresh" or not np.isfinite(a[t]) or c[t] <= lv.price:
                continue
            out.append(Zone(t, lv.price, lv.price - 0.25 * a[t], lv.price - 1.0 * a[t], "fresh_v"))
    return _gate(out, storyline(d, k) if storyline_on else None)


def qm(df: pd.DataFrame, k: int = 2, storyline_on: bool = True) -> list[Zone]:
    """Buy QM: V level -> a red close below it (breakdown) -> the A level between them is closed above.
    Zone at the V level; stop under the lowest low made between the breakdown and the break up."""
    d = _ohlc(df)
    a = atr(d).values
    o, lo, c = d.open.values, d.low.values, d.close.values
    lv = levels(d, k)
    vs = [x for x in lv if x.kind == "V"]
    as_ = [x for x in lv if x.kind == "A"]
    out = []
    for v in vs:
        brk = next((t for t in range(v.known_at + 1, len(d)) if c[t] < o[t] and c[t] < v.price), None)
        if brk is None:
            continue
        mids = [x for x in as_ if v.origin < x.origin and x.known_at <= brk]
        if not mids:
            continue
        a_lv = mids[-1]
        up = next((t for t in range(brk + 1, len(d)) if c[t] > o[t] and c[t] > a_lv.price), None)
        if up is None or not np.isfinite(a[up]):
            continue
        head = lo[brk:up + 1].min()
        if head >= v.price or c[up] <= v.price:
            continue
        out.append(Zone(up, v.price, head, head - 0.1 * a[up], "qm"))
    return _gate(out, storyline(d, k) if storyline_on else None)


def eq_sweep(df: pd.DataFrame, k: int = 2, storyline_on: bool = True, tol: float = 0.15) -> list[Zone]:
    """Equal lows (two V levels within tol x ATR) swept by a wick and closed back above."""
    d = _ohlc(df)
    a = atr(d).values
    lo, c = d.low.values, d.close.values
    vs = [x for x in levels(d, k) if x.kind == "V"]
    out, used = [], set()
    for i in range(1, len(vs)):
        v1, v2 = vs[i - 1], vs[i]
        t0 = max(v1.known_at, v2.known_at)
        if not np.isfinite(a[t0]) or abs(v1.price - v2.price) > tol * a[t0]:
            continue
        floor = min(v1.price, v2.price)
        for t in range(t0 + 1, min(t0 + 60, len(d))):
            if c[t] < floor:
                break                                   # a real break, not a sweep
            if lo[t] < floor <= c[t] and t not in used:
                used.add(t)
                out.append(Zone(t, c[t], floor, lo[t] - 0.1 * a[t], "eq_sweep"))
                break
    return _gate(out, storyline(d, k) if storyline_on else None)


SETUPS = {"fresh_v": fresh_v, "qm": qm, "eq_sweep": eq_sweep}


def mirror(df: pd.DataFrame) -> pd.DataFrame:
    """Price turned upside down (1/price) so the long-only setups test the SHORT side in research.
    A long trade on the mirror is a short on the original (returns match to first order)."""
    d = _ohlc(df)
    return pd.DataFrame({"open": 1 / d.open, "high": 1 / d.low, "low": 1 / d.high, "close": 1 / d.close}, index=d.index)


def configs() -> list[dict]:
    return [{"k": k, "storyline_on": s} for k in GRID["k"] for s in GRID["storyline"]]


def _zones(df: pd.DataFrame, setup: str, cfg: dict, cache: dict | None = None, key=None) -> list[Zone]:
    if cache is not None and (key, setup, tuple(cfg.items())) in cache:
        return cache[(key, setup, tuple(cfg.items()))]
    z = SETUPS[setup](df, **cfg)
    if cache is not None:
        cache[(key, setup, tuple(cfg.items()))] = z
    return z


def _trades(df: pd.DataFrame, zones: list[Zone], cost: float = 0.0025) -> pd.DataFrame:
    t = simulate(df, zones, wait=20, hold=20, rr=2.0, cost=cost)
    if not t.empty:
        t["date"] = _ohlc(df).index[t.entry_bar.values]
    return t


def _pool(parts: list[pd.DataFrame]) -> pd.DataFrame:
    parts = [x for x in parts if not x.empty]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["ret", "r", "date"])


def research(frames: dict[str, pd.DataFrame], split: str = SPLIT, placebo_seeds: int = 5,
             cost: float = 0.0025) -> dict:
    """Pick each setup's config on the in-sample years only, then report the test years once,
    pooled over all markets, next to a same-shape placebo."""
    cut = pd.Timestamp(split)
    cache: dict = {}
    out = {}
    for setup in SETUPS:
        rows = []
        for cfg in configs():
            per = {m: _trades(df, _zones(df, setup, cfg, cache, m), cost) for m, df in frames.items()}
            t = _pool(list(per.values()))
            rows.append((cfg, per, t, summarize(t[t.date < cut])))
        best_cfg, best_per, best_t, best_is = max(rows, key=lambda r: (r[3]["trades"] >= 20, r[3]["avg_r"]))
        test = best_t[best_t.date >= cut]
        pl = _pool([_trades(df, placebo(df, _zones(df, setup, best_cfg, cache, m), seed=s), cost)
                    for m, df in frames.items() for s in range(placebo_seeds)])
        ts, ps = summarize(test), summarize(pl[pl.date >= cut])
        rng = np.random.default_rng(0)
        boot = [rng.choice(test.r.values, len(test)).mean() for _ in range(2000)] if len(test) else [0.0]
        ts["p_not_better_than_placebo"] = float(np.mean(np.array(boot) <= ps["avg_r"]))
        per_mkt = {m: summarize(x[x.date >= cut]) if len(x) else summarize(x) for m, x in best_per.items()}
        ok = (ts["trades"] >= PASS_RULES["min_test_trades"] and ts["avg_r"] >= PASS_RULES["min_avg_r"]
              and ts["pf"] >= PASS_RULES["min_pf"] and ts["avg_r"] > ps["avg_r"])
        out[setup] = {"config": best_cfg, "in_sample": best_is, "test": ts, "placebo_test": ps,
                      "per_market_test": per_mkt, "verdict": "PASS" if ok else "FAIL",
                      "all_configs_in_sample": [{"config": r[0], **r[3]} for r in rows]}
    return out


def report_md(res: dict, src: str, split: str = SPLIT) -> str:
    L = ["# MSNR setups on NSE ETFs (daily) — research only", "",
         f"Data: {src}. In-sample before {split} picks the config; the test years after it are looked at once.",
         "Costs 0.25% per round trip. Stop counted first when a bar hits stop and target. Long only.",
         f"PASS needs ≥{PASS_RULES['min_test_trades']} test trades, average R ≥ {PASS_RULES['min_avg_r']}, "
         f"profit factor ≥ {PASS_RULES['min_pf']}, and a better average R than the same-shape placebo.", "",
         "| Setup | Config | Test trades | Win % | Avg R | PF | Placebo avg R | Chance it is no better than placebo | Verdict |",
         "|---|---|---|---|---|---|---|---|---|"]
    for s, r in res.items():
        t, p = r["test"], r["placebo_test"]
        L.append(f"| {s} | k={r['config']['k']}, storyline={'on' if r['config']['storyline_on'] else 'off'} | "
                 f"{t['trades']} | {t['win']:.0%} | {t['avg_r']:+.2f} | {t['pf']:.2f} | {p['avg_r']:+.2f} | {t.get('p_not_better_than_placebo', 1):.0%} | **{r['verdict']}** |")
    L += ["", "## Per market (test years)", "", "| Setup | " + " | ".join(MARKETS) + " |",
          "|---|" + "---|" * len(MARKETS)]
    for s, r in res.items():
        L.append(f"| {s} | " + " | ".join(
            f"{r['per_market_test'][m]['trades']} tr, {r['per_market_test'][m]['avg_r']:+.2f}R"
            if m in r["per_market_test"] else "—" for m in MARKETS) + " |")
    L += ["", "The placebo buys zones of the same shape at random days, so it shows what simply buying dips in a",
          "rising market earns. A setup is only interesting if it beats that by a margin chance can't explain",
          "(the 'chance' column, from 2,000 bootstrap resamples of the test trades; under 5% is convincing).",
          "Only a PASS setup may join the paper tournament. Not investment advice."]
    return "\n".join(L) + "\n"


RISK_RS = 50.0          # paper risk per trade: 1% of a Rs 5,000 account
CAPITAL_RS = 5_000.0    # never buy more than the account holds (a gap fill next to the stop gives a tiny risk)


def _load(start: str = "2012-01-01") -> tuple[dict[str, pd.DataFrame], list[str]]:
    from . import data
    frames, fixes = {}, []
    for m in MARKETS:
        df = data.get_daily(m, start, strict=False)
        df = df[(df[["open", "high", "low", "close"]] > 0).all(axis=1)]
        df, dropped = data.repair_spikes(df)          # same cleaning as the tournament (bad split rows)
        frames[m] = df
        fixes += [f"{m} {x}" for x in dropped]
    return frames, fixes


def passing(report_dir: Path) -> dict[str, dict]:
    """Setups whose latest research verdict is PASS, with the config the in-sample years chose."""
    reps = sorted(report_dir.glob("msnr-*.json"))
    if not reps:
        return {}
    res = json.loads(reps[-1].read_text())
    return {s: r["config"] for s, r in res.items() if r.get("verdict") == "PASS" and s in SETUPS}


def paper(out: Path, *, report_dir: Path = Path("reports"), flags: Path | None = None,
          frames: dict[str, pd.DataFrame] | None = None, today: str | None = None) -> str:
    """Daily paper run. Replays each PASS setup over full history (no look-ahead: a zone is known at a
    close and fills only on later bars) and keeps the trades from the paper start date on. A KILL
    file in `flags` stops new entries from the day it is first seen; open trades run to their exits."""
    out.mkdir(parents=True, exist_ok=True)
    st_path = out / "state.json"
    frames = frames if frames is not None else _load()[0]
    last = max(f.index[-1] for f in frames.values())
    today = pd.Timestamp(today) if today else last
    state = json.loads(st_path.read_text()) if st_path.exists() else {"start": str(today.date()), "kill": None}
    if flags is not None and (flags / "KILL").exists() and not state.get("kill"):
        state["kill"] = str(today.date())
    start, kill = pd.Timestamp(state["start"]), (pd.Timestamp(state["kill"]) if state.get("kill") else None)
    setups = passing(report_dir)
    rows, waiting = [], []
    for m, df in frames.items():
        d = _ohlc(df)
        for s, cfg in setups.items():
            cfg = {"k": int(cfg["k"]), "storyline_on": bool(cfg["storyline_on"])}
            zs = SETUPS[s](df, **cfg)
            t = _trades(df, zs)
            for _, r in t.iterrows():
                if r.date <= start or (kill is not None and r.date > kill):
                    continue
                risk = r.entry * r.ret / r.r if r.r else 0.0      # entry - stop
                qty = min(int(RISK_RS // abs(risk)) if risk else 0, int(CAPITAL_RS // r.entry))
                rows.append({"market": m, "setup": s, "entry_date": str(r.date.date()),
                             "exit_date": str(d.index[int(r.exit_bar)].date()), "entry": round(r.entry, 2),
                             "exit": round(r.exit, 2), "reason": r.reason, "r": round(r.r, 2), "qty": qty,
                             "pnl_rs": round(qty * r.entry * r.ret, 2),
                             "open": bool(int(r.exit_bar) >= len(d) - 1 and r.reason == "time")})
            lo = d.low.values
            for z in zs:                                # limit orders still live after the last close
                live = z.known_at >= len(d) - 20 and not (lo[z.known_at + 1:] <= z.top).any()
                if live and kill is None:
                    waiting.append({"market": m, "setup": s, "known": str(d.index[z.known_at].date()),
                                    "buy_at": round(z.top, 2), "stop": round(z.stop, 2)})
    led = pd.DataFrame(rows)
    led.to_csv(out / "ledger.csv", index=False)
    st_path.write_text(json.dumps(state, indent=1))
    closed = led[~led.open] if len(led) else led
    lines = [f"MSNR paper bot {today.date()} (started {state['start']}; setups: {', '.join(setups) or 'none passed'})"
             + (f"; KILL since {state['kill']}" if state.get("kill") else ""),
             f"closed trades {len(closed)}, total R {closed.r.sum() if len(closed) else 0:+.2f}, "
             f"P&L Rs {closed.pnl_rs.sum() if len(closed) else 0:+.2f}; open {int(led.open.sum()) if len(led) else 0}",
             "limit orders waiting: " + (", ".join(f"{s} {sum(w['setup'] == s for w in waiting)}" for s in setups) or "0")]
    order = {s: i for i, s in enumerate(sorted(setups, key=lambda x: x != "qm"))}     # strongest evidence first
    lines += [f"  {w['market']} {w['setup']}: buy at {w['buy_at']}, stop {w['stop']} (zone from {w['known']})"
              for w in sorted(waiting, key=lambda w: (order[w['setup']], w['known']), reverse=False)[:8]]
    msg = "\n".join(lines)
    (out / "latest.txt").write_text(msg + "\n")
    return msg


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="MSNR research on NSE ETFs (paper only)")
    ap.add_argument("--research", action="store_true")
    ap.add_argument("--out", default="reports")
    ap.add_argument("--start", default="2012-01-01")
    ap.add_argument("--paper", help="paper ledger folder, e.g. paper/msnr")
    ap.add_argument("--flags", help="folder with an optional KILL file")
    a = ap.parse_args(argv)
    if a.paper:
        print(paper(Path(a.paper), report_dir=Path(a.out), flags=Path(a.flags) if a.flags else None))
        return 0
    if not a.research:
        ap.print_help()
        return 0
    frames, fixes = _load(a.start)
    res = research(frames)
    last = min(f.index[-1] for f in frames.values()).date()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    src = f"Yahoo daily, {a.start} to {last}, 5 NSE ETFs; rows dropped as bad data: {', '.join(fixes) or 'none'}"
    (out / f"msnr-{last}.md").write_text(report_md(res, src))
    (out / f"msnr-{last}.json").write_text(json.dumps(res, indent=1, default=str))
    print(report_md(res, f"Yahoo daily, {a.start} to {last}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""HTML tear-sheet for the backtest workflow (Q7.6).

One self-contained HTML page per run: equity curves (inline SVG) and a table of
CAGR, Sharpe, max drawdown, trades and costs for buy-and-hold and each strategy
at its default parameters. Uses the Kalpa design tokens (b7 colour --l7), light
and dark. No external requests, no quantstats needed.

This is a research picture, NOT the gate: in-sample numbers at default params
flatter every rule. Only src/gate.py (walk-forward, PSR, PBO, DSR) decides.
Paper only. Not advice.

Usage (from 07-trading/):
  python -m src.tearsheet --symbol ^NSEI --out reports/
  python -m src.tearsheet --synthetic --out reports/      # offline
"""
from __future__ import annotations

import argparse
import html
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from . import backtest, data, metrics
from .strategies import REGISTRY, weights

ROOT = Path(__file__).resolve().parents[2]
TOKENS = ROOT / "00-hq" / "design" / "tokens.css"
DEFAULT_STRATEGIES = ["tsmom", "ma_filter", "sma_cross"]
COLOURS = ["var(--muted)", "var(--l7)", "var(--gold)", "var(--madder)", "var(--accent)", "var(--ok)"]


def _row(name: str, res: backtest.Result) -> dict:
    r = res.returns
    return {"name": name, "cagr": backtest.cagr(r), "sharpe": metrics.sharpe(r),
            "max_dd": backtest.max_drawdown(r), "trades": res.trades,
            "cost": res.total_cost, "equity": backtest.equity(r)}


def rows(close: pd.Series, strategies: list[str]) -> list[dict]:
    out = [_row("Buy and hold", backtest.buy_and_hold(close))]
    for s in strategies:
        out.append(_row(s, backtest.run(close, weights(s, close))))
    return out


def _svg(rs: list[dict], width: int = 720, height: int = 260, max_points: int = 600) -> str:
    eqs = [r["equity"] for r in rs]
    n = len(eqs[0])
    step = max(1, n // max_points)
    idx = list(range(0, n, step)) + ([n - 1] if (n - 1) % step else [])
    logs = [np.log(e.to_numpy()[idx]) for e in eqs]
    lo, hi = min(float(l.min()) for l in logs), max(float(l.max()) for l in logs)
    span = (hi - lo) or 1.0
    pad = 8
    lines = []
    for i, l in enumerate(logs):
        pts = " ".join(f"{pad + (width - 2 * pad) * k / max(len(l) - 1, 1):.1f},"
                       f"{pad + (height - 2 * pad) * (1 - (v - lo) / span):.1f}" for k, v in enumerate(l))
        lines.append(f'<polyline fill="none" stroke="{COLOURS[i % len(COLOURS)]}" stroke-width="2" '
                     f'vector-effect="non-scaling-stroke" points="{pts}"/>')
    y1 = pad + (height - 2 * pad) * (1 - (0 - lo) / span)
    base = f'<line x1="{pad}" x2="{width - pad}" y1="{y1:.1f}" y2="{y1:.1f}" stroke="var(--rule)"/>' \
        if lo <= 0 <= hi else ""
    return (f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Equity curves, log scale" '
            f'preserveAspectRatio="none">{base}{"".join(lines)}</svg>')


def _pct(x: float) -> str:
    return "–" if x != x else f"{x * 100:.1f}%"


def render(symbol: str, close: pd.Series, rs: list[dict], *, source: str, note: str = "") -> str:
    tokens = TOKENS.read_text(encoding="utf-8") if TOKENS.exists() else ""
    synthetic = source != "real"
    banner = (f'<p class="banner">SYNTHETIC DATA. These numbers say nothing about any real market.'
              f'{" " + html.escape(note) if note else ""}</p>') if synthetic else ""
    legend = "".join(f'<li><i style="background:{COLOURS[i % len(COLOURS)]}"></i>{html.escape(r["name"])}</li>'
                     for i, r in enumerate(rs))
    trs = "".join(
        f'<tr><td>{html.escape(r["name"])}</td><td>{_pct(r["cagr"])}</td><td>{r["sharpe"]:.2f}</td>'
        f'<td>{_pct(r["max_dd"])}</td><td>{r["trades"]}</td><td>{_pct(r["cost"])}</td></tr>' for r in rs)
    period = f"{close.index[0]:%d %b %Y} to {close.index[-1]:%d %b %Y} ({len(close)} days)"
    made = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trading Lab tear-sheet · {html.escape(symbol)}</title>
<style>{tokens}
body{{margin:0;background:var(--bg);color:var(--fg);font-family:var(--f-body);line-height:1.5}}
main{{max-width:760px;margin:0 auto;padding:16px}}
h1{{font-family:var(--f-display);font-weight:400;margin:.2em 0;color:var(--l7)}}
.card{{background:var(--panel);border:1px solid var(--rule);border-radius:var(--r-m);padding:12px;margin:12px 0;box-shadow:var(--shadow)}}
svg{{width:100%;height:220px;display:block}}
ul.legend{{list-style:none;padding:0;margin:8px 0 0;display:flex;flex-wrap:wrap;gap:4px 14px;font-size:.9em}}
ul.legend i{{display:inline-block;width:12px;height:3px;margin-right:6px;vertical-align:middle}}
.scroll{{overflow-x:auto}}
table{{border-collapse:collapse;width:100%;font-family:var(--f-mono);font-size:.85em}}
th,td{{text-align:right;padding:6px 8px;border-bottom:1px solid var(--rule);white-space:nowrap}}
th:first-child,td:first-child{{text-align:left}}
.banner{{background:var(--warn);color:var(--bg);padding:8px 12px;border-radius:var(--r-s);font-weight:600}}
.muted{{color:var(--muted);font-size:.9em}}
</style></head><body><main>
<p class="muted">Kalpa Trading Lab · b7 · research tear-sheet</p>
<h1>{html.escape(symbol)}</h1>
{banner}
<p>{period}. Data: {html.escape(source)}. Indian delivery costs included. Made {made}.</p>
<div class="card">{_svg(rs)}<ul class="legend">{legend}</ul><p class="muted">Equity, log scale.</p></div>
<div class="card scroll"><table><thead><tr><th>Rule</th><th>CAGR</th><th>Sharpe</th><th>Max DD</th><th>Trades</th><th>Costs</th></tr></thead>
<tbody>{trs}</tbody></table></div>
<p class="muted">In-sample at default settings, so these numbers flatter every rule. Only the Overfit Gatekeeper
(walk-forward, PSR, PBO, DSR) can move a rule to paper trading. Paper only. Research, not advice. No buy or sell call.</p>
</main></body></html>
"""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Write an HTML tear-sheet.")
    p.add_argument("--symbol", default="^NSEI")
    p.add_argument("--start", default="2010-01-01")
    p.add_argument("--strategies", default=",".join(DEFAULT_STRATEGIES))
    p.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "reports")
    p.add_argument("--cache", type=Path, default=None, help="Parquet cache dir (default 07-trading/data)")
    p.add_argument("--synthetic", action="store_true", help="offline run on synthetic prices")
    a = p.parse_args(argv)
    strategies = [s.strip() for s in a.strategies.split(",") if s.strip()]
    unknown = [s for s in strategies if s not in REGISTRY]
    if unknown:
        p.error(f"unknown strategies: {', '.join(unknown)} (known: {', '.join(REGISTRY)})")

    note, source, symbol = "", "real", a.symbol
    if a.synthetic:
        source, symbol = "synthetic", "SYNTHETIC"
    else:
        try:
            close = data.get_daily(a.symbol, a.start, cache_dir=a.cache)["close"]
        except Exception as e:  # network, Yahoo limits, validation
            note = f"Real data was unavailable: {e}"
            print(f"::warning::{note}. Falling back to synthetic data.")
            source = "synthetic"
    if source == "synthetic":
        close = data.synthetic_prices(2520, seed=7, regime_days=120, regime_drift=0.2)["close"]

    rs = rows(close, strategies)
    a.out.mkdir(parents=True, exist_ok=True)
    name = "".join(c if c.isalnum() else "_" for c in symbol).strip("_") or "report"
    path = a.out / f"tearsheet-{name}.html"
    path.write_text(render(symbol, close, rs, source=source, note=note), encoding="utf-8")
    for r in rs:
        print(f"{r['name']:<14} CAGR {_pct(r['cagr']):>7}  Sharpe {r['sharpe']:5.2f}  "
              f"MaxDD {_pct(r['max_dd']):>7}  trades {r['trades']}")
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""F-17 (A33): daily budget + spend-spike alerts over `usage_daily` rows.

Input rows need only: day (IST date, ISO), cost_paise, and optional feature /
customer_id_hash. Hashes only, never raw customer ids (same as usage_daily).

Spike rule (robust, no deps): compare today's spend with up to 14 earlier days
(missing days count as zero, at least 7 needed). Fires when today is above
3x the median AND above median + 6 x 1.4826 x MAD, and the rise is at least
Rs 50 so tiny tenants are not spammed.

Delivery: Slack incoming webhook from env LP_SLACK_WEBHOOK (a secret the
customer sets); without it the message is printed (dry run). Email is not
wired: no free email tier has been verified for this yet.

CLI: python -m alerts.alerts usage_daily.csv [--today YYYY-MM-DD] [--budget RUPEES]
Exit code 1 when any alert fired, so a GitHub Action / cron can flag it.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import sys
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

WINDOW_DAYS = 14
MIN_HISTORY = 7
MULTIPLE = 3.0
MAD_K = 6.0
FLOOR_PAISE = 5000  # Rs 50
SLACK_PREFIX = "https://hooks.slack.com/"


@dataclass(frozen=True)
class Alert:
    kind: str      # "budget" | "anomaly"
    scope: str     # "total" | "feature:<name>" | "customer:<hash>"
    paise: int     # today's spend in this scope
    baseline: int  # median of history (anomaly) or the budget (budget)


def rupees(paise: int) -> str:
    return f"₹{paise / 100:,.2f}"


def _scopes(row: dict) -> list[str]:
    out = ["total", f"feature:{row.get('feature') or 'untagged'}"]
    if row.get("customer_id_hash"):
        out.append(f"customer:{row['customer_id_hash']}")
    return out


def _series(rows: list[dict]) -> dict[str, dict[date, int]]:
    by: dict[str, dict[date, int]] = defaultdict(lambda: defaultdict(int))
    for r in rows:
        d = date.fromisoformat(str(r["day"])[:10])
        for s in _scopes(r):
            by[s][d] += int(r.get("cost_paise") or 0)
    return by


def _is_spike(today_p: int, history: list[int]) -> bool:
    med = statistics.median(history)
    mad = statistics.median(abs(h - med) for h in history)
    return (today_p > MULTIPLE * med and today_p > med + MAD_K * 1.4826 * mad
            and today_p - med >= FLOOR_PAISE)


def check(rows: list[dict], today: date, budget_paise: int | None = None) -> list[Alert]:
    series = _series(rows)
    total_today = series.get("total", {}).get(today, 0)
    found: list[Alert] = []
    if budget_paise is not None and total_today > budget_paise:
        found.append(Alert("budget", "total", total_today, budget_paise))
    for scope in sorted(series, key=lambda s: (s != "total", s)):
        days = series[scope]
        first = min(days)
        start = max(first, today - timedelta(days=WINDOW_DAYS))
        history = [days.get(start + timedelta(days=i), 0) for i in range((today - start).days)]
        if len(history) < MIN_HISTORY:
            continue
        p = days.get(today, 0)
        if _is_spike(p, history):
            found.append(Alert("anomaly", scope, p, int(statistics.median(history))))
    return found


def format_message(found: list[Alert], today: date) -> str:
    if not found:
        return f"Ledger Peaks {today.isoformat()}: no alerts."
    lines = [f"Ledger Peaks alerts for {today.isoformat()} (IST):"]
    for a in found:
        if a.kind == "budget":
            lines.append(f"- Over budget: spent {rupees(a.paise)} today, budget {rupees(a.baseline)}.")
        else:
            lines.append(f"- Spend spike ({a.scope}): {rupees(a.paise)} today vs usual {rupees(a.baseline)}.")
    return "\n".join(lines)


def load_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return [{"day": r["day"], "feature": r.get("feature") or None,
                 "customer_id_hash": r.get("customer_id_hash") or None,
                 "cost_paise": int(r.get("cost_paise") or 0)} for r in csv.DictReader(f)]


def send(text: str) -> str:
    url = os.environ.get("LP_SLACK_WEBHOOK", "").strip()
    if not url:
        print(text)
        return "dry-run"
    if not url.startswith(SLACK_PREFIX):
        raise ValueError("LP_SLACK_WEBHOOK must be a https://hooks.slack.com/ URL")
    req = urllib.request.Request(url, data=json.dumps({"text": text}).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310 (prefix checked)
        return f"slack {resp.status}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("csv", type=Path)
    ap.add_argument("--today", type=date.fromisoformat, default=None)
    ap.add_argument("--budget", type=float, default=None, help="daily budget in rupees")
    a = ap.parse_args(argv)
    rows = load_csv(a.csv)
    today = a.today or max(date.fromisoformat(r["day"][:10]) for r in rows)
    budget = None if a.budget is None else round(a.budget * 100)
    found = check(rows, today, budget)
    if found:
        send(format_message(found, today))
        return 1
    print(format_message(found, today))
    return 0


if __name__ == "__main__":
    sys.exit(main())

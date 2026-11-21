"""A225: does the n8n keep-awake schedule fit Render's 750 free hours a month?

Render (docs/free, fetched 22 Nov 2026): 750 Free instance hours per workspace per
calendar month; spun-down services use none; a service spins down after 15 min
with no inbound traffic; out of hours = all Free services suspended to month end.

Usage: python3 00-hq/n8n-selfhost/hours_budget.py   (exit 0 fits, 1 does not)
"""
import re
import sys
from pathlib import Path

POOL = 750            # hours per workspace per month (Render docs/free)
IDLE_MIN = 15         # spin-down after 15 min idle
DAYS = 31             # plan for the longest month
ROUTER_H_DAY = 3.0    # llm-router allowance; measured 1.6 h/day (15-21 Nov), x2 margin
SAFETY = 0.95         # never plan above 95% of the pool
WF = Path(__file__).resolve().parents[2] / ".github/workflows/n8n-keepalive.yml"


def _field(spec, lo, hi):
    out = set()
    for part in spec.split(","):
        if part == "*":
            out.update(range(lo, hi + 1))
        elif "-" in part:
            a, b = map(int, part.split("-"))
            out.update(range(a, b + 1))
        else:
            out.add(int(part))
    return sorted(out)


def awake_hours_per_day(cron):
    """Hours a day the service stays up if pinged on this cron (minute hour * * *)."""
    minute, hour = cron.split()[:2]
    pings = sorted(h * 60 + m for h in _field(hour, 0, 23) for m in _field(minute, 0, 59))
    if not pings:
        return 0.0
    awake = 0
    for a, b in zip(pings, pings[1:] + [pings[0] + 1440]):
        awake += min(b - a, IDLE_MIN)  # up until the next ping, or 15 min after the last
    return round(awake / 60, 2)


def crons(text):
    return re.findall(r'cron:\s*"([^"]+)"', text)


def budget(n8n_h_day, router_h_day=ROUTER_H_DAY, days=DAYS):
    used = (n8n_h_day + router_h_day) * days
    return round(used, 1), used <= POOL * SAFETY


def main():
    specs = crons(WF.read_text())
    if len(specs) != 1:
        print(f"expected 1 cron in {WF.name}, found {len(specs)}")
        return 1
    h = awake_hours_per_day(specs[0])
    used, ok = budget(h)
    print(f"n8n awake {h} h/day + router {ROUTER_H_DAY} h/day x {DAYS} days = {used} h "
          f"of {POOL} ({'OK' if ok else 'TOO MUCH'}; limit {POOL * SAFETY:.0f})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

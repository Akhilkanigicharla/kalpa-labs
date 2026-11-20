#!/usr/bin/env python3
"""A222 Netlify credit budget: read 00-hq/log/deploys.csv, say if a deploy is allowed.

Netlify Free = 300 credits/month hard limit, production deploy = 15 credits
(netlify.com/pricing + docs.netlify.com credit-based plans, both fetched 2026-11-21).
At the limit the site pauses until the next billing cycle, so we stop at 240.

Rules: OK only if this cycle's credits + 15 <= 240 and the site has no deploy today (IST).
Usage: python3 00-hq/tools/deploy_budget.py [--site kalpa-labs] [--csv path] [--today YYYY-MM-DD] [--json]
Exit 0 = OK to deploy, 2 = wait (one deploy a day), 3 = STOP (cap). Env KL_NETLIFY_CYCLE_DAY sets the
billing-cycle start day (default 1; set it from Netlify's Usage page).
"""
import argparse, csv, datetime as dt, json, os, sys

CAP, LIMIT, DEPLOY_COST = 240, 300, 15
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(HERE, "..", "log", "deploys.csv")
FIELDS = ["date_ist", "site", "deploy_id", "why", "approx_credits"]


def cycle_start(today, day):
    day = max(1, min(28, day))
    if today.day >= day:
        return today.replace(day=day)
    prev = (today.replace(day=1) - dt.timedelta(days=1))
    return prev.replace(day=day)


def read_rows(path):
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                d = dt.date.fromisoformat((r.get("date_ist") or "").strip()[:10])
                c = int(float((r.get("approx_credits") or "0").strip() or 0))
            except ValueError:
                continue  # bad row: skip, never crash the sprint
            if c < 0 or c > 1000:
                continue
            rows.append({"date": d, "site": (r.get("site") or "").strip(), "credits": c})
    return rows


def check(rows, site, today, cycle_day=1):
    start = cycle_start(today, cycle_day)
    used = sum(r["credits"] for r in rows if start <= r["date"] <= today)
    today_site = sum(1 for r in rows if r["date"] == today and r["site"] == site)
    if used + DEPLOY_COST > CAP:
        verdict, code = "STOP", 3
    elif today_site:
        verdict, code = "WAIT", 2
    else:
        verdict, code = "OK", 0
    return {"verdict": verdict, "code": code, "cycle_start": start.isoformat(), "used": used,
            "cap": CAP, "limit": LIMIT, "left_before_cap": max(0, CAP - used),
            "deploys_left": max(0, (CAP - used) // DEPLOY_COST), "site": site,
            "site_deploys_today": today_site}


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--site", default="kalpa-labs")
    p.add_argument("--csv", default=DEFAULT_CSV)
    p.add_argument("--today")
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    ist_now = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30)))
    today = dt.date.fromisoformat(a.today) if a.today else ist_now.date()
    try:
        day = int(os.environ.get("KL_NETLIFY_CYCLE_DAY", "1"))
    except ValueError:
        day = 1
    r = check(read_rows(a.csv), a.site, today, day)
    if a.json:
        print(json.dumps(r))
    else:
        print(f"{r['verdict']}: Netlify credits {r['used']}/{CAP} cap since {r['cycle_start']} "
              f"({r['deploys_left']} deploys left); {a.site} deploys today: {r['site_deploys_today']}")
    return r["code"]


if __name__ == "__main__":
    sys.exit(main())

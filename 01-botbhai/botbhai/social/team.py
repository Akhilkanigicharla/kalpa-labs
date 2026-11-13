"""The zero-employee social media team, run as one command.

  python -m social.team --setup salon --start 2026-10-19 --weeks 4 --out out/social
    -> out/social/plan.csv, manifest.json, approval.txt and every image/Reel

  python -m social.team --reply "skip 3, rest ok" --out out/social        # apply the owner's WhatsApp answer
  python -m social.team --publish --base-url https://<public folder>/ --ig-user <id> --out out/social --now "2026-10-19 19:30"
    (dry run unless --live; --live also needs IG_ACCESS_TOKEN in the environment)

Roles: strategist (plan.py) -> copywriter -> compliance -> designer -> owner approval (approve.py) -> publisher -> analyst.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import pathlib
import sys

from . import analyst, approve, compliance, copywriter, design, plan, publish


def build(setup: str, start: dt.date, weeks: int, out: pathlib.Path, *, overrides: dict | None = None,
          photos: dict | None = None, weights: dict | None = None, render: bool = True, cfg: dict | None = None,
          times: dict | None = None) -> dict:
    cfg = cfg or plan.load_setup(setup, overrides)
    out.mkdir(parents=True, exist_ok=True)
    items = []
    for i, slot in enumerate(plan.month_plan(cfg, start, weeks, weights, times)):
        copy = copywriter.write(slot, cfg, i)
        chk = compliance.check(copy["caption"], setup=setup, cfg=cfg)
        files = [p.name for p in design.render(slot, copy, cfg, out, photos)] if render else []
        items.append({**slot, **{k: copy[k] for k in ("caption", "headline", "alt", "needs", "script", "telugu", "image_prompt")},
                      "check": chk, "files": files, "status": "draft"})
    with (out / "plan.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["#", "date", "time", "kind", "pillar", "headline", "needs", "compliance", "files"])
        for n, it in enumerate(items, 1):
            w.writerow([n, it["date"], it["time"], it["kind"], it["pillar"], it["headline"], " | ".join(it["needs"]),
                        "OK" if it["check"]["ok"] else "HELD: " + "; ".join(it["check"]["blocked"]), " ".join(it["files"])])
    week = f"{items[0]['date']} to {items[-1]['date']}" if items else ""
    msg = approve.batch_message(items, cfg, week)
    (out / "approval.txt").write_text(msg, encoding="utf-8")
    manifest = {"setup": setup, "business": cfg.get("business"), "start": start.isoformat(), "weeks": weeks, "items": items}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--setup", default="salon", choices=["salon", "gym", "realestate", "examkits"])
    ap.add_argument("--start", default=dt.date.today().isoformat())
    ap.add_argument("--weeks", type=int, default=4)
    ap.add_argument("--out", default="out/social")
    ap.add_argument("--reply")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--base-url", default="https://example.invalid/social/")
    ap.add_argument("--ig-user", default="IG_USER_ID")
    ap.add_argument("--page", default=None)
    ap.add_argument("--now", default=dt.datetime.now().strftime("%Y-%m-%d %H:%M"))
    ap.add_argument("--views", help="insights CSV export -> posting time per format learned from real views (8+ posts)")
    ap.add_argument("--channel", default=None, help="only rows of this channel in --views, e.g. instagram")
    ap.add_argument("--insights", help="JSON list of post results -> weekly report + new pillar weights")
    a = ap.parse_args(argv)
    out = pathlib.Path(a.out)
    if a.insights:
        rows = json.loads(pathlib.Path(a.insights).read_text())
        print(analyst.report(rows))
        print(json.dumps(analyst.new_weights(rows)))
        return 0
    if a.reply or a.publish:
        m = json.loads((out / "manifest.json").read_text())
        if a.reply:
            r = approve.parse_reply(a.reply, len(m["items"]))
            if r["unknown"]:
                print("Couldn't understand the reply; ask the owner again.")
                return 2
            approve.apply(m["items"], r)
        if a.publish:
            pub = publish.Publisher(a.ig_user, a.base_url, page_id=a.page, dry_run=not a.live)
            for it in publish.due(m["items"], a.now):
                try:
                    it.update(pub.publish(it))
                    print("posted" if a.live else "dry run", it["id"])
                except publish.GraphError as e:
                    it["error"] = str(e)
                    print("skipped", it["id"], e)
        (out / "manifest.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
        print({s: sum(1 for i in m["items"] if i["status"] == s) for s in {i["status"] for i in m["items"]}})
        return 0
    times = None
    if a.views:
        now = {k: v[1] for k, v in plan.DEFAULT_SLOTS.items()} | {"story": "10:00"}
        times = analyst.best_times(analyst.read_views_csv(a.views), now, a.channel)
        moved = {k: f"{now[k]} -> {v}" for k, v in times.items() if v != now[k]}
        print("Posting times learned from views:", moved or "no change (need 8+ posts per format and a clear winner)")
    m = build(a.setup, dt.date.fromisoformat(a.start), a.weeks, out, times=times)
    held = sum(1 for i in m["items"] if not i["check"]["ok"] or i["needs"])
    print(f"{len(m['items'])} items for {m['business']} in {out} ({held} wait for the owner's photo/review/RERA no.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Kalpa marketing team: the BotBhai Social Team engine run for every Kalpa world, in the Kalpa design system.

  python3 00-hq/marketing/run.py --world b6 --start 2026-10-19 --weeks 4 --out out/marketing
  python3 00-hq/marketing/run.py --world all --weeks 1 --out out/marketing          # every enabled world
  python3 00-hq/marketing/run.py --world b6 --out out/marketing --reply "ok"         # Akhil's approval

Brand profiles live in brands/<world>.json. Each uses its world colour (--lN in 00-hq/design/tokens.css) and the
Kalpa fonts (Rozha One headlines, Anek Latin body, Anek Telugu). Posts stay held until Akhil adds the real link,
screenshots and reviews, and approves. Trading Lab (b7) is switched off on purpose (SEBI finfluencer rules).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys

HQ = pathlib.Path(__file__).resolve().parents[1]
ROOT = HQ.parent
sys.path.insert(0, str(ROOT / "01-botbhai" / "botbhai"))
from social import approve, plan, team  # noqa: E402

BRANDS = HQ / "marketing" / "brands"
FONTS = HQ / "design" / "fonts"
KALPA_FONTS = {"display": str(FONTS / "rozha-one-latin-400-normal.woff"), "body": str(FONTS / "anek-latin-latin-600-normal.woff"),
               "bold": str(FONTS / "anek-latin-latin-700-normal.woff"), "telugu": str(FONTS / "anek-telugu-telugu-700-normal.woff")}


def load(world: str) -> dict:
    cfg = plan.load_profile(BRANDS / f"{world}.json")
    cfg.setdefault("fonts", KALPA_FONTS)
    cfg["world"] = world
    return cfg


def worlds() -> list[str]:
    return sorted(p.stem for p in BRANDS.glob("*.json"))


def build(world: str, start: dt.date, weeks: int, out: pathlib.Path, render: bool = True) -> dict | None:
    cfg = load(world)
    if cfg.get("enabled") is False:
        return None
    return team.build(cfg["setup"], start, weeks, out / world, cfg=cfg, render=render)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--world", default="all")
    ap.add_argument("--start", default=dt.date.today().isoformat())
    ap.add_argument("--weeks", type=int, default=4)
    ap.add_argument("--out", default="out/marketing")
    ap.add_argument("--reply")
    a = ap.parse_args(argv)
    out = pathlib.Path(a.out)
    targets = worlds() if a.world == "all" else [a.world]
    for w in targets:
        if a.reply:
            mf = out / w / "manifest.json"
            m = json.loads(mf.read_text())
            approve.apply(m["items"], approve.parse_reply(a.reply, len(m["items"])))
            mf.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
            print(w, {s: sum(1 for i in m["items"] if i["status"] == s) for s in {i["status"] for i in m["items"]}})
            continue
        m = build(w, dt.date.fromisoformat(a.start), a.weeks, out)
        if m is None:
            print(f"{w}: switched off ({load(w).get('disabled_reason', '')})")
            continue
        held = sum(1 for i in m["items"] if not i["check"]["ok"] or i["needs"])
        print(f"{w}: {len(m['items'])} posts for {m['business']} ({held} wait for a link, screenshot or review)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

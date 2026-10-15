"""Strategist: a month of posts and stories from the business's own services, offers and the festival calendar.

Evidence used (see research/social-team.md):
- Small accounts (< 1,000 followers) get the most reach from Reels (median 134 views) vs carousels (56) and
  single images (23); carousels earn more likes/saves as accounts grow (Metricool x HypeAuditor, 700M posts, H1 2025).
  So each week mixes 1 Reel (reach), 1 carousel (saves) and 1 single post, plus stories.
- Value before selling: most posts teach, show the work or thank customers; offers are a minority.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Telangana festival dates (same source as seo_bot.py: cleartax Telangana 2026 holiday list).
FESTIVALS = [("2026-01-14", "Sankranti"), ("2026-03-04", "Holi"), ("2026-03-08", "Women's Day"), ("2026-03-20", "Ugadi"),
             ("2026-10-11", "Bathukamma"), ("2026-10-20", "Dussehra"), ("2026-11-08", "Diwali"), ("2026-12-25", "Christmas"),
             ("2027-01-14", "Sankranti"), ("2027-03-08", "Women's Day")]

# Content pillars and their share of feed posts (tuned per client by analyst.py after 4 weeks).
PILLARS = {"tip": 0.30, "work": 0.25, "proof": 0.15, "offer": 0.20, "team": 0.10}
FORMATS_PER_WEEK = ["reel", "carousel", "post"]        # 3 feed posts a week + stories
STORIES_PER_WEEK = 2
DEFAULT_SLOTS = {"reel": (2, "19:30"), "carousel": (4, "19:00"), "post": (6, "11:00")}  # (weekday Mon=0, IST time)


def load_setup(setup: str, overrides: dict | None = None) -> dict:
    cfg = json.loads((ROOT / "setups" / setup / "bot.config.json").read_text())
    cfg.update(overrides or {})
    cfg.setdefault("areas", ["Jubilee Hills", "Banjara Hills", "Madhapur", "Kukatpally", "Gachibowli"])
    cfg.setdefault("whatsapp", re.sub(r"\D", "", cfg.get("phone", "")))
    cfg["setup"] = setup
    return cfg


def _pillar_sequence(n: int, weights: dict[str, float]) -> list[str]:
    """Deterministic largest-remainder spread of n slots over pillars, interleaved so no pillar repeats back to back."""
    total = sum(weights.values()) or 1
    quota = {k: n * v / total for k, v in weights.items()}
    counts = {k: int(q) for k, q in quota.items()}
    for k in sorted(quota, key=lambda k: quota[k] - counts[k], reverse=True)[: n - sum(counts.values())]:
        counts[k] += 1
    seq: list[str] = []
    while len(seq) < n:
        for k in sorted(counts, key=lambda k: -counts[k]):
            if counts[k] and (not seq or seq[-1] != k or all(c == 0 for kk, c in counts.items() if kk != k)):
                seq.append(k); counts[k] -= 1; break
    return seq


def festival_near(day: dt.date, within: int = 6) -> str | None:
    for d, name in FESTIVALS:
        delta = (dt.date.fromisoformat(d) - day).days
        if 0 <= delta <= within:
            return name
    return None


def month_plan(cfg: dict, start: dt.date, weeks: int = 4, weights: dict | None = None) -> list[dict]:
    """Returns slots: {id, date, time, kind: reel|carousel|post|story, pillar, service, festival}."""
    weights = weights or PILLARS
    monday = start - dt.timedelta(days=start.weekday())
    feed = _pillar_sequence(weeks * len(FORMATS_PER_WEEK), weights)
    catalog = cfg.get("catalog") or [{"name": cfg.get("business", "")}]
    slots, k = [], 0
    for w in range(weeks):
        wk = monday + dt.timedelta(weeks=w)
        for i, kind in enumerate(FORMATS_PER_WEEK):
            wd, t = DEFAULT_SLOTS[kind]
            day = wk + dt.timedelta(days=wd)
            if day < start:  # first week already under way: post on the start day instead of skipping
                day = start
            fest = festival_near(day)
            pillar = "festival" if fest and i == 0 else feed[k]
            slots.append({"id": f"W{w + 1}-{kind}", "date": day.isoformat(), "time": t, "kind": kind, "pillar": pillar,
                          "service": catalog[k % len(catalog)]["name"], "festival": fest})
            k += 1
        for s in range(STORIES_PER_WEEK):
            day = wk + dt.timedelta(days=1 + s * 3)
            slots.append({"id": f"W{w + 1}-story{s + 1}", "date": max(day, start).isoformat(), "time": "10:00", "kind": "story",
                          "pillar": "offer" if s == 0 else "proof", "service": catalog[(w * 2 + s) % len(catalog)]["name"],
                          "festival": festival_near(day)})
    return sorted(slots, key=lambda x: (x["date"], x["time"]))

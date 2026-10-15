"""Analyst: reads post results and moves next month's mix toward what worked for THIS business.

Input rows come from the Instagram Insights API (GET /{media-id}/insights?metric=reach,saved,shares,likes,comments)
or a CSV the owner exports; each row carries the slot's pillar and kind from the manifest.
Score = reach-weighted engagement. Saves and shares count more than likes because Instagram has said they signal
value to its ranking (Mosseri, 2024-25); comments count double. The new weights blend 50% old plan + 50% results,
with a floor so no pillar disappears (a small sample should nudge, not flip, the plan).
"""
from __future__ import annotations

from .plan import PILLARS

WEIGHTS = {"likes": 1, "comments": 2, "saved": 3, "shares": 3}
FLOOR = 0.05


def score(row: dict) -> float:
    eng = sum(WEIGHTS[k] * float(row.get(k, 0) or 0) for k in WEIGHTS)
    reach = float(row.get("reach", 0) or 0)
    return eng / reach if reach else 0.0


def new_weights(rows: list[dict], old: dict | None = None) -> dict:
    old = dict(old or PILLARS)
    by: dict[str, list[float]] = {}
    for r in rows:
        if r.get("pillar") in old:
            by.setdefault(r["pillar"], []).append(score(r))
    if not by:
        return old
    avg = {p: (sum(v) / len(v)) for p, v in by.items()}
    mean = sum(avg.values()) / len(avg) or 1
    perf = {p: old[p] * (avg[p] / mean if p in avg else 1.0) for p in old}
    tot = sum(perf.values()) or 1
    mixed = {p: 0.5 * old[p] + 0.5 * perf[p] / tot for p in old}
    mixed = {p: max(FLOOR, w) for p, w in mixed.items()}
    s = sum(mixed.values())
    return {p: round(w / s, 3) for p, w in mixed.items()}


def report(rows: list[dict], old: dict | None = None) -> str:
    """Plain-English WhatsApp summary for the owner."""
    if not rows:
        return "No post results yet. Your first report comes after a week of posting."
    best = max(rows, key=score)
    kinds: dict[str, list[float]] = {}
    for r in rows:
        kinds.setdefault(r.get("kind", "post"), []).append(float(r.get("reach", 0) or 0))
    reach_by_kind = {k: round(sum(v) / len(v)) for k, v in kinds.items()}
    top_kind = max(reach_by_kind, key=reach_by_kind.get)
    nw = new_weights(rows, old)
    up = max(nw, key=lambda p: nw[p] - (old or PILLARS).get(p, 0))
    total_reach = sum(int(r.get("reach", 0) or 0) for r in rows)
    return "\n".join([
        f"📊 This week: {len(rows)} posts reached {total_reach:,} people.",
        f"⭐ Best post: {best.get('id')} ({best.get('pillar')}, {best.get('kind')}): {int(best.get('saved', 0) or 0)} saves, {int(best.get('shares', 0) or 0)} shares.",
        f"🎬 {top_kind.title()}s reached the most people (avg {reach_by_kind[top_kind]:,}).",
        f"➡️ Next month we'll make a few more '{up}' posts.",
    ])

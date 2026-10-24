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


# --- A97: best posting time per format, learned from the owner's own insights export (CSV) ---
MIN_POSTS, MIN_PER_HOUR, MIN_GAIN = 8, 2, 1.10  # need 8+ posts of a format; best hour needs 2+ posts and 10% more views
KIND_WORDS = (("reel", "reel"), ("video", "reel"), ("carousel", "carousel"), ("album", "carousel"),
              ("story", "story"), ("photo", "post"), ("image", "post"), ("post", "post"))


def _col(headers: list[str], *words: str) -> str | None:
    for w in words:  # first word wins, so "publish time" beats a generic "date"
        for h in headers:
            if w in h.lower():
                return h
    return None


def read_views_csv(path) -> list[dict]:
    """Rows {channel, kind, hour, views} from a Meta Business Suite / Instagram insights CSV export.
    Header names vary by export, so columns are found by words (publish/time/date, type, views/plays/reach)."""
    import csv
    import datetime as _dt
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        hs = rd.fieldnames or []
        tc, kc = _col(hs, "publish", "time", "date"), _col(hs, "post type", "type", "format")
        vc, cc = _col(hs, "views", "plays", "reach", "impressions"), _col(hs, "channel", "platform", "account")
        if not (tc and kc and vc):
            raise ValueError(f"CSV needs time, type and views columns; found {hs}")
        rows = []
        for r in rd:
            raw, kind_txt = (r.get(tc) or "").strip(), (r.get(kc) or "").lower()
            try:
                views = float((r.get(vc) or "").replace(",", ""))
                when = None
                for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y %H:%M", "%d/%m/%Y %H:%M", "%Y-%m-%dT%H:%M"):
                    try:
                        when = _dt.datetime.strptime(raw[:19] if "T" in raw else raw[:16], fmt)
                        break
                    except ValueError:
                        continue
            except ValueError:
                continue
            kind = next((k for w, k in KIND_WORDS if w in kind_txt), None)
            if when and kind:
                rows.append({"channel": (r.get(cc) or "").strip().lower() if cc else "", "kind": kind,
                             "hour": when.hour, "views": views})
        return rows


def best_times(rows: list[dict], current: dict, channel: str | None = None) -> dict:
    """{kind: "HH:MM"} for formats whose best hour clearly wins; formats with < 8 posts keep `current`.
    `current` is {kind: "HH:MM"} (the planner's slots). Times are IST, as exported for an Indian account."""
    out = dict(current)
    for kind, now in current.items():
        mine = [r for r in rows if r["kind"] == kind and (not channel or r["channel"] in ("", channel))]
        if len(mine) < MIN_POSTS:
            continue
        by_hour: dict[int, list[float]] = {}
        for r in mine:
            by_hour.setdefault(r["hour"], []).append(r["views"])
        avg = {h: sum(v) / len(v) for h, v in by_hour.items() if len(v) >= MIN_PER_HOUR}
        if not avg:
            continue
        best = max(avg, key=avg.get)
        now_h = int(now[:2])
        base = avg.get(now_h) or (sum(sum(v) for v in by_hour.values()) / len(mine))
        if best != now_h and avg[best] >= base * MIN_GAIN:
            out[kind] = f"{best:02d}:00"
    return out

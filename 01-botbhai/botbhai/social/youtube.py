"""YouTube helper for the Social Team: rule checks from the MIT youtube-agent-skill (00-hq/vendor/youtube-agent).

The writing (script, title ideas, SEO text, comment replies) goes to free models through n8n (DELEGATE.md);
this file does the parts that must be exact and cost nothing: chapter lists YouTube will accept, title length
checks, and a description with chapters, the business CTA and an ad disclosure when needed.

    python3 -m social.youtube chapters segments.json     # [{"start": 0.0, "text": "..."}...] from faster-whisper
    python3 -m social.youtube title "3 BHK walkthrough in Kondapur | price, parking, sunlight"
"""
from __future__ import annotations

import json
import sys

TITLE_MAX, DESKTOP_CUT, MOBILE_CUT = 100, 60, 40  # YouTube hard limit; search and home-feed truncation (yt-package)
DESC_MAX, TAGS_MAX = 5000, 500  # YouTube limits for description and all tags together
MIN_CHAPTERS, MIN_CHAPTER_S = 3, 10  # YouTube rules (yt-chapters): >= 3 chapters, first at 00:00, each >= 10 s


def stamp(sec: float) -> str:
    s = int(sec)
    h, m, s = s // 3600, s % 3600 // 60, s % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def validate_chapters(chapters: list[tuple[float, str]], duration: float) -> list[str]:
    """Problems that would make YouTube ignore the chapters. Empty list = valid."""
    errs = []
    if len(chapters) < MIN_CHAPTERS:
        errs.append(f"need at least {MIN_CHAPTERS} chapters, have {len(chapters)}")
    if chapters and chapters[0][0] != 0:
        errs.append("first chapter must start at 00:00")
    ends = [c[0] for c in chapters[1:]] + [duration]
    for (start, title), end in zip(chapters, ends):
        if end - start < MIN_CHAPTER_S:
            errs.append(f"'{title}' at {stamp(start)} is shorter than {MIN_CHAPTER_S} s")
        if not title.strip():
            errs.append(f"chapter at {stamp(start)} has no title")
    return errs


def chapters_from(segments: list[dict], duration: float, every: float = 60.0) -> list[tuple[float, str]]:
    """Rough chapters from transcript segments: a new chapter at the first segment after each `every` seconds,
    titled with its first words. A person (or the n8n writer) renames them; the timing is already valid."""
    out: list[tuple[float, str]] = []
    for seg in sorted(segments, key=lambda s: s["start"]):
        start = 0.0 if not out else float(seg["start"])
        if out and (start - out[-1][0] < every or duration - start < MIN_CHAPTER_S):
            continue
        words = " ".join(str(seg.get("text", "")).split()[:6]).strip(" .,") or "Part"
        out.append((start, words[:1].upper() + words[1:]))
    return out


def chapter_text(chapters: list[tuple[float, str]]) -> str:
    return "\n".join(f"{stamp(s)} {t}" for s, t in chapters)


def title_check(title: str) -> dict:
    t = title.strip()
    return {"chars": len(t), "ok": 0 < len(t) <= TITLE_MAX,
            "desktop_cut": t[:DESKTOP_CUT] if len(t) > DESKTOP_CUT else "",
            "mobile_cut": t[:MOBILE_CUT] if len(t) > MOBILE_CUT else ""}


def tags_fit(tags: list[str]) -> list[str]:
    """Keep tags in order until the 500-character total is reached (YouTube counts commas between them)."""
    kept, total = [], 0
    for tag in (t.strip() for t in tags):
        if not tag:
            continue
        extra = len(tag) + (2 if " " in tag else 0) + (1 if kept else 0)  # multi-word tags are counted with quotes
        if total + extra > TAGS_MAX:
            break
        kept.append(tag)
        total += extra
    return kept


def description(cfg: dict, summary: str, chapters: list[tuple[float, str]] | None = None,
                paid: bool = False, affiliate: bool = False) -> str:
    """Description: summary, chapters, how to reach the business, and ASCI disclosure when paid/affiliate."""
    parts = []
    if paid or affiliate:  # ASCI: disclosure up front, where it is seen before "show more"
        parts.append("#ad · Paid partnership" if paid else "Affiliate links below: we may earn a commission.")
    parts.append(summary.strip())
    if chapters:
        parts.append(chapter_text(chapters))
    reach = cfg["cta"]["url"] if cfg.get("cta") else f"WhatsApp {cfg.get('phone', '')}"
    parts.append(f"{cfg.get('business', '')} · {reach}".strip(" ·"))
    return "\n\n".join(p for p in parts if p)[:DESC_MAX]


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    if a[:1] == ["chapters"] and len(a) == 2:
        segs = json.loads(open(a[1], encoding="utf-8").read())
        dur = max(float(s.get("end", s["start"])) for s in segs)
        ch = chapters_from(segs, dur)
        print(chapter_text(ch))
        for e in validate_chapters(ch, dur):
            print("!", e)
        return 0
    if a[:1] == ["title"] and len(a) == 2:
        print(json.dumps(title_check(a[1]), ensure_ascii=False))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())

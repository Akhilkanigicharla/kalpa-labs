#!/usr/bin/env python3
"""A197 · Monthly "what people say" research per Kalpa world.

Our own small engine (idea: mvanhorn/last30days-skill, MIT). Looks back 30 days
on four free sources only: Hacker News (Algolia API, no key), GitHub (search API,
GITHUB_TOKEN in Actions), Reddit (public JSON, may be blocked from cloud IPs) and
YouTube (Data API, only if YOUTUBE_API_KEY is set; otherwise skipped).
Rules built in: no other sources (never Instagram/X/TikTok/Facebook/Maps/Justdial),
no queries about named people, no author names stored, every finding has its link.

  python3 00-hq/tools/whatpeoplesay.py [--world b1] [--out 00-hq/knowledge/whatpeoplesay]
"""
import argparse, datetime as dt, json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOPICS = os.path.join(ROOT, "00-hq/research/whatpeoplesay/topics.json")
ALLOWED_SOURCES = ("hackernews", "github", "reddit", "youtube")
BLOCKED_WORDS = ("instagram", "insta", "twitter", "tweet", "x.com", "tiktok", "facebook",
                 "fb.com", "threads", "linkedin", "google maps", "justdial", "snapchat",
                 "phone number", "mobile number", "address of", "contact of", "who is",
                 "profile of", "home address", "email of")
HONORIFICS = r"\b(mr|mrs|ms|dr|sri|shri|smt|garu|ji|sir|madam)\b\.?"
UA = "kalpa-labs-research/1.0 (monthly topic research; github.com/Akhilkanigicharla/kalpa-labs)"


class Refused(ValueError):
    pass


def check_query(q):
    """Raise Refused unless q is a plain topic phrase (no people, no blocked sources)."""
    s = (q or "").strip()
    low = s.lower()
    if not s or len(s) > 120:
        raise Refused("empty or too long")
    if "@" in s or re.search(r"https?://", low):
        raise Refused("handles and links are not topics")
    for w in BLOCKED_WORDS:
        if re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", low):
            raise Refused(f"blocked source or person lookup: {w}")
    if re.search(HONORIFICS, low):
        raise Refused("looks like a person's name")
    if re.search(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b", s):
        raise Refused("looks like a person's name (two capitalised words)")
    return s


def check_sources(sources):
    bad = [x for x in sources if x not in ALLOWED_SOURCES]
    if bad:
        raise Refused(f"source not allowed: {', '.join(bad)}")
    return list(sources)


def _get(url, headers=None, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def hackernews(q, since, get=_get):
    p = urllib.parse.urlencode({"query": q, "tags": "(story,comment)", "hitsPerPage": 8,
                                "numericFilters": f"created_at_i>{int(since.timestamp())}"})
    out = []
    for h in get("https://hn.algolia.com/api/v1/search?" + p).get("hits", []):
        title = h.get("title") or h.get("story_title") or (h.get("comment_text") or "")[:120]
        out.append({"source": "hackernews", "title": re.sub(r"<[^>]+>", "", title).strip(),
                    "url": f"https://news.ycombinator.com/item?id={h['objectID']}",
                    "date": (h.get("created_at") or "")[:10], "score": h.get("points") or 0})
    return out


def github(q, since, get=_get, pause=time.sleep):
    tok = os.environ.get("GITHUB_TOKEN")
    if get is _get:  # search API limit: 10/min without a token, 30/min with one
        pause(2.1 if tok else 6.5)
    hdr = {"Accept": "application/vnd.github+json", **({"Authorization": f"Bearer {tok}"} if tok else {})}
    p = urllib.parse.urlencode({"q": f"{q} is:issue created:>{since:%Y-%m-%d}", "per_page": 8, "sort": "reactions"})
    return [{"source": "github", "title": i.get("title", ""), "url": i["html_url"],
             "date": (i.get("created_at") or "")[:10], "score": (i.get("reactions") or {}).get("total_count", 0)}
            for i in get("https://api.github.com/search/issues?" + p, hdr).get("items", [])]


def reddit(q, since, get=_get):
    p = urllib.parse.urlencode({"q": q, "t": "month", "limit": 8, "sort": "relevance"})
    out = []
    for c in get("https://www.reddit.com/search.json?" + p).get("data", {}).get("children", []):
        d = c.get("data", {})
        if d.get("over_18"):
            continue
        out.append({"source": "reddit", "title": d.get("title", ""), "url": "https://www.reddit.com" + d.get("permalink", ""),
                    "date": dt.datetime.fromtimestamp(d.get("created_utc", 0), dt.timezone.utc).strftime("%Y-%m-%d"),
                    "score": d.get("score", 0)})
    return out


def youtube(q, since, get=_get):
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        raise LookupError("skipped: no YOUTUBE_API_KEY secret")
    p = urllib.parse.urlencode({"part": "snippet", "q": q, "type": "video", "maxResults": 8, "key": key,
                                "publishedAfter": since.strftime("%Y-%m-%dT%H:%M:%SZ"), "safeSearch": "strict"})
    return [{"source": "youtube", "title": i["snippet"]["title"], "url": f"https://www.youtube.com/watch?v={i['id']['videoId']}",
             "date": i["snippet"]["publishedAt"][:10], "score": 0}
            for i in get("https://www.googleapis.com/youtube/v3/search?" + p).get("items", [])]


FETCHERS = {"hackernews": hackernews, "github": github, "reddit": reddit, "youtube": youtube}


def research_world(wid, world, now, sources=ALLOWED_SOURCES, get=_get):
    since = now - dt.timedelta(days=30)
    check_sources(sources)
    findings, notes = [], []
    for q in world["queries"]:
        try:
            check_query(q)
        except Refused as e:
            notes.append(f"refused query `{q}`: {e}")
            continue
        for src in sources:
            try:
                for f in FETCHERS[src](q, since, get):
                    if f["url"].startswith("https://") and f["title"]:
                        findings.append({**f, "query": q})
            except LookupError as e:
                notes.append(f"{src}: {e}")
            except Exception as e:  # one source down never stops the run
                notes.append(f"{src} `{q}`: {type(e).__name__} {str(e)[:80]}")
    seen, uniq = set(), []
    for f in sorted(findings, key=lambda f: -f["score"]):
        if f["url"] not in seen:
            seen.add(f["url"]); uniq.append(f)
    return uniq, sorted(set(notes))


def _md(t):
    return re.sub(r"\s+", " ", t.replace("[", "(").replace("]", ")"))[:140]


def render(wid, world, findings, notes, now):
    lines = [f"# What people say · {world['name']} ({wid}) · {now:%B %Y}", "",
             f"_Last 30 days to {now:%Y-%m-%d}. Sources: Hacker News, GitHub, Reddit, YouTube only. "
             "Titles and links only, no author names. Built by `00-hq/tools/whatpeoplesay.py` (A197)._", ""]
    for q in world["queries"]:
        rows = [f for f in findings if f["query"] == q][:10]
        lines += [f"## {q}", ""] + ([f"- [{_md(f['title'])}]({f['url']}) · {f['source']} · {f['date']}" for f in rows] or ["- nothing found this month"]) + [""]
    if notes:
        lines += ["## Run notes", ""] + [f"- {n}" for n in notes] + [""]
    lines += ["## For Scout/Kavi", "", "- Read the titles, open 3-5 links, write what changes our plan in that world's `research/`.", ""]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", action="append")
    ap.add_argument("--out", default=os.path.join(ROOT, "00-hq/knowledge/whatpeoplesay"))
    ap.add_argument("--sources", default=",".join(ALLOWED_SOURCES))
    a = ap.parse_args(argv)
    now = dt.datetime.now(dt.timezone.utc)
    sources = check_sources([s.strip() for s in a.sources.split(",") if s.strip()])
    worlds = json.load(open(TOPICS))["worlds"]
    folder = os.path.join(a.out, f"{now:%Y-%m}")
    os.makedirs(folder, exist_ok=True)
    empty = 0
    for wid in a.world or worlds:
        findings, notes = research_world(wid, worlds[wid], now, sources)
        open(os.path.join(folder, f"{wid}.md"), "w").write(render(wid, worlds[wid], findings, notes, now))
        print(f"{wid}: {len(findings)} findings, {len(notes)} notes")
        empty += not findings
    return 1 if empty == len(a.world or worlds) else 0


if __name__ == "__main__":
    sys.exit(main())

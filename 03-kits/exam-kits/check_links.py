#!/usr/bin/env python3
"""Check every link in the exam kits (A160/A180). Runs weekly in GitHub Actions; the kits never ship a dead link.

YouTube videos and channels are checked through YouTube's public oEmbed endpoint / channel page (no API key);
other links with a normal GET. Writes 03-kits/exam-kits/link-report.json and exits 1 if anything is broken.
Usage: python3 03-kits/exam-kits/check_links.py [--only <exam-id>]
"""
import json, pathlib, sys, urllib.parse, urllib.request, urllib.error

HERE = pathlib.Path(__file__).parent
UA = "Mozilla/5.0 (compatible; KalpaKitLinkCheck/1.0)"


def links(exam):
    """Every (kind, url) the kit shows to a buyer."""
    out = [("official", exam["official_url"])]
    res = exam.get("resources") or {}
    for kind in ("official", "mocks", "channels"):
        out += [(kind, o["url"]) for o in res.get(kind, [])]
    out += [("video", v["url"]) for v in exam.get("topic_videos", {}).values()]
    return list(dict.fromkeys(out))


def probe_url(kind, url):
    if kind == "video":
        return "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(url, safe="")
    return url


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def check(exams, get=fetch):
    report = {}
    for e in exams:
        rows = []
        for kind, url in links(e):
            code = get(probe_url(kind, url))
            rows.append({"kind": kind, "url": url, "status": code, "ok": 200 <= code < 400})
        report[e["id"]] = rows
    return report


def main(argv):
    sys.path.insert(0, str(HERE))
    import build as B
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    exams = [e for e in B.load_exams(only) if e.get("resources")]
    report = check(exams)
    (HERE / "link-report.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    bad = [(eid, r["url"], r["status"]) for eid, rows in report.items() for r in rows if not r["ok"]]
    total = sum(len(v) for v in report.values())
    print(f"{total - len(bad)}/{total} links OK across {len(report)} kits")
    for b in bad:
        print("BROKEN", *b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

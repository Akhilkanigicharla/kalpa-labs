"""Outside-in check of every live Kalpa site (CLAUDE.md: test it live like a customer would).

For each site: home page 200 over HTTPS, a real 404 page for a missing path, favicon, security headers,
robots.txt + sitemap.xml, and that secret-looking paths bots probe (/.env, /.git/config) are NOT served.
Standard library only.  Run:  python3 00-hq/tools/live_check.py [--json]
"""
from __future__ import annotations

import json
import ssl
import sys
import urllib.error
import urllib.request

SITES = {  # world -> live URL (keep in step with 00-hq/LINKS.md)
    "hq": "https://kalpalabs.dpdns.org",
    "b1 BotBhai": "https://kalpa-botbhai.netlify.app",
    "b4 Tab Lifeboat": "https://akhilkanigicharla.github.io/kalpa-labs",
}
HEADERS = ["strict-transport-security", "x-content-type-options", "referrer-policy", "content-security-policy"]
PROBES = ["/.env", "/.git/config", "/secrets.txt"]
UA = {"User-Agent": "kalpa-live-check/1.0 (+https://kalpalabs.dpdns.org)"}


def fetch(url: str, timeout: int = 25):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as r:
            return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read(200_000)
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in e.headers.items()}, e.read(200_000)
    except Exception as e:  # network trouble is a failed check, never a crash
        return 0, {}, str(e).encode()


def check(base: str) -> list[tuple[str, bool, str]]:
    out = []
    st, hd, body = fetch(base + "/")
    out.append(("home page 200", st == 200, str(st)))
    pages = "github.io" in base  # GitHub Pages cannot send custom headers: CSP + referrer must be <meta> tags there
    low = body.lower()
    meta = {"content-security-policy": b'http-equiv="content-security-policy"' in low,
            "referrer-policy": b'name="referrer"' in low}
    for h in HEADERS:
        ok = h in hd or meta.get(h, False) or (pages and h == "x-content-type-options")
        why = "" if h in hd else ("as <meta>" if meta.get(h) else ("not settable on GitHub Pages" if ok else "missing"))
        out.append((f"header {h}", ok, why))
    st404, _, b404 = fetch(base + "/this-page-does-not-exist-kalpa")
    out.append(("custom 404 page", st404 == 404 and len(b404) > 300, f"{st404}, {len(b404)} bytes"))
    stf, hf, bf = fetch(base + "/favicon.ico")
    linked = b'rel="icon"' in body or b"rel='icon'" in body or b"rel=icon" in body
    out.append(("favicon", stf == 200 or linked, f"/favicon.ico {stf}, <link rel=icon> {'yes' if linked else 'no'}"))
    for p in ("/robots.txt", "/sitemap.xml"):
        s, _, _ = fetch(base + p)
        out.append((p, s == 200, str(s)))
    for p in PROBES:
        s, _, b = fetch(base + p)
        leak = s == 200 and b"<html" not in b[:500].lower()
        out.append((f"{p} not served", not leak, str(s)))
    return out


def main():
    report = {name: check(url) for name, url in SITES.items()}
    if "--json" in sys.argv:
        print(json.dumps({n: [{"check": c, "ok": ok, "detail": d} for c, ok, d in r] for n, r in report.items()}, indent=1))
    else:
        for name, rows in report.items():
            bad = [r for r in rows if not r[1]]
            print(f"{name:16} {SITES[name]}  {len(rows) - len(bad)}/{len(rows)} ok")
            for c, ok, d in bad:
                print(f"   FAIL {c}: {d}")
    sys.exit(1 if any(not ok for rows in report.values() for _, ok, _ in rows) else 0)


if __name__ == "__main__":
    main()

"""Licence-clean images for Deals (b5) and Kits (b3) pages from the Openverse API (A209).

Only CC0, Public Domain Mark and CC BY, commercial use, mature off. Each result carries a
credit line to print under the image and the source page to check by hand before publishing:
Openverse says it "cannot make any claims about the accuracy of license information".
Anonymous limits (response headers, 13 Nov 2026): 20/min, 200/day. The API returns 504
often, so calls retry with backoff. No key, no account.
CLI: python3 00-hq/tools/openverse_images.py "pressure cooker" [n]"""
import html, json, re, sys, time, urllib.error, urllib.parse, urllib.request

API = "https://api.openverse.org/v1/images/"
SAFE = {"cc0": "CC0", "pdm": "Public Domain Mark", "by": "CC BY"}
TIMEOUT, MAX_TRIES = 20, 3
UA = "KalpaLabs-images/1.0"

class OpenverseError(RuntimeError):
    pass

def _fetch(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def _clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]*>|[<>]", "", html.unescape(str(s or "")))).strip()[:120]

def credit(r):
    lic = SAFE[r["license"]]
    ver = r.get("license_version") or ""
    lic = f"{lic} {ver}".strip() if r["license"] != "pdm" else lic
    by = f" by {_clean(r.get('creator'))}" if _clean(r.get("creator")) else ""
    return f'"{_clean(r.get("title")) or "Untitled"}"{by} ({lic}), via {_clean(r.get("source"))}'

def shape(r):
    return {"url": r["url"], "thumbnail": r.get("thumbnail", ""), "license": r["license"],
            "license_url": r.get("license_url", ""), "credit": credit(r),
            "verify_at": r.get("foreign_landing_url", ""), "width": r.get("width"), "height": r.get("height")}

def _ok(r):
    return (r.get("license") in SAFE and not r.get("mature")
            and str(r.get("url", "")).startswith("https://"))

def search(query, n=5, fetch=_fetch, sleep=time.sleep):
    q = (query or "").strip()
    if not q or len(q) > 200 or re.search(r"[\x00-\x1f]", q):
        raise ValueError("query must be 1-200 printable characters")
    if not 1 <= int(n) <= 20:
        raise ValueError("n must be 1-20")
    url = API + "?" + urllib.parse.urlencode({"q": q, "license": "cc0,pdm,by", "license_type": "commercial",
                                               "mature": "false", "page_size": min(20, n * 2)})
    err = None
    for i in range(MAX_TRIES):
        try:
            body = fetch(url, TIMEOUT)
            break
        except urllib.error.HTTPError as e:
            err = e
            if e.code != 429 and e.code < 500:
                raise OpenverseError(f"Openverse HTTP {e.code}") from e
        except (urllib.error.URLError, TimeoutError) as e:
            err = e
        if i < MAX_TRIES - 1:
            sleep(2 ** (i + 1))
    else:
        raise OpenverseError(f"Openverse failed after {MAX_TRIES} tries: {getattr(err, 'code', err)}")
    try:
        rows = json.loads(body)["results"]
    except (ValueError, KeyError, TypeError) as e:
        raise OpenverseError("Openverse sent a reply that is not the expected JSON") from e
    return [shape(r) for r in rows if isinstance(r, dict) and _ok(r)][:n]

if __name__ == "__main__":
    for r in search(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 5):
        print(r["credit"], "|", r["url"], "| check:", r["verify_at"])

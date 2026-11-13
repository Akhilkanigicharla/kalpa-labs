"""Tests for openverse_images.py (A209). Offline: a fake fetch stands in for the API.
Run: python3 00-hq/tools/test_openverse_images.py   (add --live for one real call)"""
import json, pathlib, sys, urllib.error

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import openverse_images as ov

def row(**kw):
    r = {"id": "a1", "title": "phone call", "creator": "Sean MacEntee", "license": "by", "license_version": "2.0",
         "license_url": "https://creativecommons.org/licenses/by/2.0/", "url": "https://live.staticflickr.com/x.jpg",
         "thumbnail": "https://api.openverse.org/v1/images/a1/thumb/", "foreign_landing_url": "https://www.flickr.com/photos/x",
         "source": "flickr", "mature": False, "width": 500, "height": 375}
    r.update(kw)
    return r

def fake(rows, fail=0, code=504):
    calls = []
    def fetch(url, timeout):
        calls.append((url, timeout))
        if len(calls) <= fail:
            raise urllib.error.HTTPError(url, code, "err", {}, None)
        return json.dumps({"result_count": len(rows), "results": rows}).encode()
    fetch.calls = calls
    return fetch

checks = 0
def ok(cond, name):
    global checks
    assert cond, name
    checks += 1

# 1 query: only licences safe for a commercial page, mature off, size capped
f = fake([row()])
ov.search("mobile phone", fetch=f, sleep=lambda s: None)
url = f.calls[0][0]
ok("license=cc0%2Cpdm%2Cby" in url and "license_type=commercial" in url and "mature=false" in url, "query filters")
ok(f.calls[0][1] == ov.TIMEOUT, "timeout passed")

# 2 result shape + credit line
got = ov.search("phone", fetch=f, sleep=lambda s: None)[0]
ok(got["credit"] == '"phone call" by Sean MacEntee (CC BY 2.0), via flickr', got["credit"])
ok(got["verify_at"].startswith("https://www.flickr.com"), "verify link kept")

# 3 CC0 / PDM credit wording, unknown creator
ok(ov.credit(row(license="cc0", license_version="1.0", creator="")) == '"phone call" (CC0 1.0), via flickr', "cc0 credit")
ok("Public Domain Mark" in ov.credit(row(license="pdm", license_version="1.0")), "pdm credit")

# 4 drops: SA/NC/ND licences, mature, missing url, http (not https) url
bad = [row(id="b1", license="by-sa"), row(id="b2", license="by-nc"), row(id="b3", mature=True),
       row(id="b4", url=""), row(id="b5", url="http://x.jpg")]
ok(ov.search("phone", fetch=fake(bad + [row()]), sleep=lambda s: None) == [ov.shape(row())], "unsafe rows dropped")

# 5 retries 5xx/429 with backoff, then succeeds
waits = []
f = fake([row()], fail=2)
ok(len(ov.search("phone", fetch=f, sleep=waits.append)) == 1 and waits == [2, 4], f"backoff {waits}")
f = fake([row()], fail=1, code=429)
ok(len(ov.search("phone", fetch=f, sleep=lambda s: None)) == 1, "429 retried")

# 6 gives up after MAX_TRIES and says so; 4xx (not 429) is not retried
f = fake([row()], fail=99)
try:
    ov.search("phone", fetch=f, sleep=lambda s: None); ok(False, "should raise")
except ov.OpenverseError as e:
    ok(len(f.calls) == ov.MAX_TRIES and "504" in str(e), str(e))
f = fake([row()], fail=99, code=400)
try:
    ov.search("phone", fetch=f, sleep=lambda s: None); ok(False, "should raise")
except ov.OpenverseError:
    ok(len(f.calls) == 1, "400 not retried")

# 7 input validation: empty, too long, control chars, emoji + Telugu ok
for q in ["", "   ", "x" * 201, "phone\x00drop"]:
    try:
        ov.search(q, fetch=fake([]), sleep=lambda s: None); ok(False, f"accepted {q!r}")
    except ValueError:
        ok(True, "")
ok(ov.search("ఫోన్ 📱", fetch=fake([row()]), sleep=lambda s: None), "unicode query")
try:
    ov.search("phone", n=0, fetch=fake([]), sleep=lambda s: None); ok(False, "n=0")
except ValueError:
    ok(True, "")

# 8 hostile API data: html in title/creator is stripped from the credit, junk JSON raises
c = ov.credit(row(title='<script>x</script>Phone', creator='<b>Me</b>'))
ok("<" not in c and ">" not in c, c)
try:
    ov.search("phone", fetch=lambda u, timeout: b"not json", sleep=lambda s: None); ok(False, "junk")
except ov.OpenverseError:
    ok(True, "")

if "--live" in sys.argv:
    res = ov.search("smartphone", n=3)
    ok(res and all(r["license"] in ov.SAFE for r in res), "live")
    print("live:", res[0]["credit"])

print(f"openverse_images: {checks} checks PASS")

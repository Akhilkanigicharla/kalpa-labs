"""Engineering checks for the public site (00-hq/design/ENGINEERING-CHECKS.md).

- cache busting: index.html loads app.js?v=<first 8 hex of its sha256>   (--fix rewrites it)
- security headers in netlify.toml: CSP with script-src 'self', frame-ancestors 'none', X-Frame-Options, Permissions-Policy
- no inline <script> that runs code (CSP would block it), no inline on*= handlers
- performance budget: index.html + app.js under 160 KB, 404 page under 20 KB
- 404 page shows a hostile address as text, never as HTML, and cut to 80 characters (browser test)

Run: python3 00-hq/site/tests/test_assets.py [--fix]
"""
import hashlib, pathlib, re, sys

SITE = pathlib.Path(__file__).resolve().parents[1]
fails = []


def check(ok, msg):
    if not ok:
        fails.append(msg)


html = (SITE / "index.html").read_text(encoding="utf-8")
js = (SITE / "app.js").read_bytes()
ver = hashlib.sha256(js).hexdigest()[:8]
m = re.search(r'src="app\.js\?v=([0-9a-f]{8})"', html)
if "--fix" in sys.argv and m and m.group(1) != ver:
    html = html.replace(m.group(0), f'src="app.js?v={ver}"')
    (SITE / "index.html").write_text(html, encoding="utf-8")
    m = re.search(r'src="app\.js\?v=([0-9a-f]{8})"', html)
check(m and m.group(1) == ver, f"app.js version is stale: run with --fix (want {ver})")

for page in ("index.html", "404.html"):
    text = (SITE / page).read_text(encoding="utf-8")
    for tag in re.findall(r"<script(?![^>]*\bsrc=)(?![^>]*application/ld\+json)[^>]*>", text):
        check(False, f"{page}: inline script would be blocked by CSP: {tag}")
    check(not re.search(r"\son[a-z]+=\"", text), f"{page}: inline on*= handler")

toml = (SITE / "netlify.toml").read_text(encoding="utf-8")
csp = re.search(r'Content-Security-Policy = "([^"]+)"', toml)
check(csp and "script-src 'self'" in csp.group(1) and "frame-ancestors 'none'" in csp.group(1), "CSP header missing or weak")
for h in ("X-Frame-Options", "Permissions-Policy", "Strict-Transport-Security", "X-Content-Type-Options", "Referrer-Policy"):
    check(h in toml, f"header missing: {h}")

size = len(html.encode()) + len(js)
check(size < 160_000, f"performance budget: index.html + app.js = {size} bytes (budget 160 KB)")
check((SITE / "404.html").stat().st_size < 20_000, "404 page over 20 KB")

# 404 edge case in a real browser: hostile, very long address
from playwright.sync_api import sync_playwright  # noqa: E402
sys.path.insert(0, str(SITE / "tests"))
from test_tap_sweep import serve  # noqa: E402

srv, base = serve()
try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 390, "height": 844})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("dialog", lambda d: (errs.append("dialog opened: XSS"), d.dismiss()))
        evil = "<img src=x onerror=alert(1)>" + "a" * 300
        pg.goto(base.rstrip("/") + "/404.html?q=" + evil)
        pg.wait_for_timeout(400)
        t = pg.inner_text("#tried")
        check("<img" in t and len(t) <= 80, f"404 did not show the address safely as short text: {t[:90]!r}")
        check(pg.locator("#tried img").count() == 0, "404 rendered the address as HTML")
        sw = pg.evaluate("document.documentElement.scrollWidth")
        check(sw <= 390, f"404 scrolls sideways at 390 px ({sw})")
        check(not errs, f"404 errors: {errs}")
        b.close()
finally:
    srv.shutdown()

if fails:
    print("FAIL\n- " + "\n- ".join(fails))
    sys.exit(1)
print("PASS assets: version, CSP + headers, no inline JS, budget, 404 edge cases")

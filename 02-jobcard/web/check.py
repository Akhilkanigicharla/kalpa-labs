"""A37: the "my customers" PWA on a 390 px phone, light + dark, plus what Lighthouse's old PWA audit checked
(Lighthouse 12 removed that category): manifest + icons, service worker in control, works offline, no horizontal
scroll, 16 px inputs, 44 px tap targets, no requests to other sites. Screenshots go to 02-jobcard/design/web/.
Run: node 02-jobcard/web/build.mjs && python3 02-jobcard/web/check.py"""
import functools, http.server, json, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

web = Path(__file__).parent
out = web.parent / "design" / "web"; out.mkdir(parents=True, exist_ok=True)
class H(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".mjs": "text/javascript", ".webmanifest": "application/manifest+json"}
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(H, directory=str(web)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_port}"

m = json.loads((web / "manifest.webmanifest").read_text())
assert m["display"] == "standalone" and m["start_url"].startswith("/") and m["name"] and m["short_name"]
from PIL import Image
for i in m["icons"]:
    w, h = Image.open(web / i["src"].lstrip("/")).size
    assert f"{w}x{h}" == i["sizes"], i
assert {"192x192", "512x512"} <= {i["sizes"] for i in m["icons"]} and any(i["purpose"] == "maskable" for i in m["icons"])

problems = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for theme in ("light", "dark"):
        ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, color_scheme=theme, has_touch=True, is_mobile=True)
        pg = ctx.new_page(); outside = []
        pg.on("request", lambda r: outside.append(r.url) if not r.url.startswith(base) and not r.url.startswith("data:") else None)
        pg.on("pageerror", lambda e: problems.append(f"{theme}: {e}"))
        pg.goto(base + "/?lang=te"); pg.wait_for_selector(".list li")
        pg.evaluate("navigator.serviceWorker.ready"); pg.reload(); pg.wait_for_selector(".list li")
        assert pg.evaluate("!!navigator.serviceWorker.controller"), "service worker not in control"
        for tab in ("due", "customers", "bills", "record"):
            pg.click(f'.tabs button[data-tab="{tab}"]'); pg.wait_for_timeout(250)
            if tab == "record": pg.click("#mic"); pg.wait_for_selector("#heard .card")
            assert pg.evaluate("document.documentElement.scrollWidth") <= 390, f"{theme}/{tab}: horizontal scroll"
            small = pg.evaluate("""[...document.querySelectorAll('.btn,.tabs button,#mic,label.tick')].filter(e => e.offsetParent && e.getBoundingClientRect().height < 44).map(e => e.textContent.trim().slice(0,20))""")
            assert not small, f"{theme}/{tab}: tap targets under 44 px: {small}"
            fonts = pg.evaluate("[...document.querySelectorAll('input')].map(i => parseFloat(getComputedStyle(i).fontSize))")
            assert all(f >= 16 for f in fonts), f"{theme}/{tab}: input font under 16 px (iOS zoom)"
            if tab in ("due", "customers"): pg.screenshot(path=str(out / f"{tab}-390-{theme}.png"), full_page=True)
        ctx.set_offline(True); pg.reload(); pg.wait_for_selector(".list li, #mic", timeout=10000)  # opens offline from the cache
        ctx.set_offline(False)
        assert not outside, f"requests to other sites: {outside[:3]}"
        ctx.close()
    b.close()
srv.shutdown()
assert not problems, problems
print("ok: manifest, icons, service worker, offline, 390 px light + dark, 16 px inputs, 44 px targets, no outside requests")

"""Tap sweep: every visible link/button/input on the site, at 390 px, light + dark.

Fails if a form field runs past the screen edge, if a control is covered by something else (e.g. the bottom bar) after
scrolling to it, or if a button/standalone link is under 44 px tall.
Inline links inside running text are exempt from the size rule (WCAG 2.5.8).

Run:  python3 00-hq/site/tests/test_tap_sweep.py [URL]
Default serves 00-hq/site locally.
"""
import functools, http.server, sys, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

SITE = Path(__file__).resolve().parents[1]
MIN = 44

TOP_JS = """([x,y])=>{const el=document.elementFromPoint(x,y);
 if(!el) return 'none';
 const c=el.closest('a,button,input,select,textarea,label');
 return c?c.outerHTML.slice(0,90):el.tagName+'.'+el.className}"""
INLINE_JS = """el=>el.tagName==='A'&&!!el.closest('p,li,small,figcaption')
 &&!el.matches('.btn,[class*=btn],[role=button]')"""


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    h = functools.partial(Quiet, directory=str(SITE))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/"


def sweep(page):
    bad = []
    els = page.locator("a:visible, button:visible, input:visible, select:visible, textarea:visible")
    for i in range(els.count()):
        e = els.nth(i)
        try:
            e.scroll_into_view_if_needed(timeout=2000)
        except Exception:
            continue
        page.wait_for_timeout(40)
        bb = e.bounding_box()
        if not bb or bb["width"] == 0 or bb["height"] == 0:
            continue
        if e.get_attribute("tabindex") == "-1" and bb["x"] < 0:
            continue  # spam honeypot, hidden off-screen on purpose
        vw = page.viewport_size["width"]
        if (e.evaluate("el=>['INPUT','SELECT','TEXTAREA'].includes(el.tagName)")
                and bb["x"] + bb["width"] > vw + 1):
            bad.append(f"off-screen: field {e.get_attribute('name')!r} ends at "
                       f"{int(bb['x'] + bb['width'])}px on a {vw}px screen")
        label = (e.inner_text(timeout=500) or e.get_attribute("aria-label")
                 or e.get_attribute("href") or "").strip().replace("\n", " ")[:40]
        mine = e.evaluate("el=>el.outerHTML.slice(0,90)")
        top = page.evaluate(TOP_JS, [bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2])
        if top != mine and not top.startswith("<label"):
            bad.append(f"covered: {label!r} under {top[:60]}")
        if (bb["height"] < MIN and e.evaluate("el=>['A','BUTTON'].includes(el.tagName)")
                and not e.evaluate(INLINE_JS)):
            bad.append(f"small: {label!r} {int(bb['width'])}x{int(bb['height'])}px")
    return bad


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else None
    srv = None
    if not url:
        srv, url = serve()
    problems = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for scheme in ("light", "dark"):
            pg = b.new_page(viewport={"width": 390, "height": 844}, is_mobile=True,
                            has_touch=True, color_scheme=scheme)
            errs = []
            pg.on("pageerror", lambda ex: errs.append(str(ex)[:100]))
            pg.goto(url, wait_until="networkidle", timeout=60000)
            problems += [f"[{scheme}] {x}" for x in sweep(pg)]
            problems += [f"[{scheme}] js error: {x}" for x in errs]
            pg.close()
        b.close()
    if srv:
        srv.shutdown()
    # The Netlify "Powered by" badge only exists on the live site; it is a
    # dashboard setting, not our code, so report it separately.
    badge = [x for x in problems if "IFRAME" in x]
    real = [x for x in problems if "IFRAME" not in x]
    for x in badge:
        print("WARN (Netlify badge):", x)
    for x in real:
        print("FAIL", x)
    print("PASS tap sweep" if not real else f"{len(real)} problem(s)")
    sys.exit(1 if real else 0)


if __name__ == "__main__":
    main()

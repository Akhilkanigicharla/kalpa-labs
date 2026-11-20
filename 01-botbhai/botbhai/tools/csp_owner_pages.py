#!/usr/bin/env python3
"""Every page (demo chat, owner screens, sample invoice) runs under the strict CSP from netlify.toml: no inline scripts (A220).

Serves web/dist on localhost, sends BOTH CSP headers Netlify sends for these paths (site-wide + per-page), opens each
page in demo mode in Chromium and fails on any CSP violation or page error. Off-site requests are aborted.
    python3 01-botbhai/botbhai/tools/csp_owner_pages.py      (run python3 build.py first)
"""
import functools, http.server, pathlib, re, sys, threading, tomllib

from playwright.sync_api import sync_playwright

BOT = pathlib.Path(__file__).resolve().parents[1]
DIST = BOT / "web" / "dist"
cfg = tomllib.loads((BOT / "netlify.toml").read_text())
rules = cfg.get("headers", [])
PAGES = ["/", "/inbox.html", "/dashboard.html", "/billing.html", "/invoice-sample.html"]


def csp_for(path):
    out = []
    for r in rules:
        pat = "^" + re.escape(r["for"]).replace(r"\*", ".*") + "$"
        v = r.get("values", {}).get("Content-Security-Policy")
        if v and re.match(pat, path):
            out.append(v.replace("upgrade-insecure-requests", "").strip())
    return out


class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        for v in csp_for(self.path.split("?")[0]):
            self.send_header("Content-Security-Policy", v)
        super().end_headers()

    def log_message(self, *a):
        pass


def main():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(H, directory=str(DIST)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    bad = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for page_path in PAGES:
            srcs = [d.strip() for c in csp_for(page_path) for d in c.split(";") if d.strip().startswith("script-src")]
            assert srcs and all("'self'" in d and "unsafe-inline" not in d and "unsafe-eval" not in d for d in srcs), f"{page_path}: script-src not strict: {srcs}"
            pg = b.new_page(viewport={"width": 390, "height": 844})
            pg.route(re.compile(r"^(?!http://127\.0\.0\.1).*"), lambda r: r.abort())
            msgs = []
            pg.on("console", lambda m: msgs.append(m.text) if "Content Security Policy" in m.text else None)
            pg.on("pageerror", lambda e: msgs.append(f"page error: {e}"))
            pg.goto(f"{base}{page_path}?demo=1", wait_until="networkidle")
            pg.wait_for_timeout(500)
            ran = pg.evaluate("document.body.innerText.length")
            if page_path == "/":  # the page script really ran: niche tabs rendered by app.js
                ran = ran if pg.evaluate("typeof BotBhai === 'object' && document.querySelectorAll('[data-tab]').length > 0") else 0
            if page_path == "/invoice-sample.html":  # the print button works without inline onclick
                pg.evaluate("window.__printed = 0; window.print = () => window.__printed++; 0")  # trailing 0: Playwright calls a returned function
                pg.click("#print-btn")
                ran = ran if pg.evaluate("window.__printed") == 1 else 0
            if msgs or ran < 50:
                bad.append((page_path, msgs[:3], ran))
            print(("PASS" if not msgs and ran >= 50 else "FAIL"), page_path, f"(text {ran} chars, {len(msgs)} CSP/page errors)")
            pg.close()
        b.close()
    srv.shutdown()
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

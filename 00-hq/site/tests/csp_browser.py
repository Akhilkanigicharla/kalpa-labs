#!/usr/bin/env python3
"""Loads every Kalpa Labs site in Chromium with its real security headers and fails on any CSP violation.

    python3 00-hq/site/tests/csp_browser.py      # needs Python Playwright + Chromium (as in quality.yml)

Each site is served from localhost by a tiny server that adds the headers its netlify.toml / _headers sends (read by
00-hq/site/test_headers.py's parser), so what Chromium enforces here is what the host will send. Two changes for plain
http://localhost only: HSTS is left out and 'upgrade-insecure-requests' is dropped (it would turn localhost requests
into https), and frame-ancestors https: becomes http://127.0.0.1:* for the local stand-in client site. Off-site requests (Google Fonts, cdnjs, Turnstile) are aborted after the browser's CSP check, so the test
needs no network yet still catches a host the CSP forgot. It also proves the BotBhai chat page can be framed by another
origin (widget.js) while its owner pages cannot. Builds what it needs first (BotBhai, JobCard, Tab Lifeboat, SEO demo);
the calculators are checked when 05-deals/site/dist exists (npm run build).
"""
import functools, http.server, importlib.util, pathlib, subprocess, sys, tempfile, threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("test_headers", ROOT / "00-hq/site/test_headers.py")
TH = importlib.util.module_from_spec(spec); spec.loader.exec_module(TH)


def local(h):
    out = {k: v for k, v in h.items() if k != "strict-transport-security"}
    if "content-security-policy" in out:
        parts = [p.strip() for p in out["content-security-policy"].split(";") if p.strip() != "upgrade-insecure-requests"]
        # frame-ancestors https: (the widget's client sites) stands in for the plain-http localhost "client site" here
        out["content-security-policy"] = "; ".join(p.replace(" https:", " http://127.0.0.1:*") if p.startswith("frame-ancestors") else p for p in parts)
    return out


def serve(folder, rules):
    class H(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            path = self.path.split("?")[0].split("#")[0]
            for k, v in local(TH.headers_for(rules, path) if rules else {}).items(): self.send_header(k, v)
            super().end_headers()
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(H, directory=str(folder)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_port}"


WATCH = """window.__csp = []; document.addEventListener('securitypolicyviolation', e =>
  window.__csp.push(e.violatedDirective + ' blocked ' + (e.blockedURI || 'inline') + ' @' + (e.sourceFile || '') + ':' + e.lineNumber));"""


def build():
    subprocess.check_call([sys.executable, "build.py"], cwd=ROOT / "01-botbhai/botbhai", stdout=subprocess.DEVNULL)
    subprocess.check_call(["node", "web/build.mjs"], cwd=ROOT / "02-jobcard", stdout=subprocess.DEVNULL)
    subprocess.check_call(["node", "04-extensions/site/build.mjs"], cwd=ROOT, stdout=subprocess.DEVNULL)
    seo = pathlib.Path(tempfile.mkdtemp()) / "seo"
    subprocess.check_call([sys.executable, "seo/seo_bot.py", "--setup", "salon", "--draft", "--out", str(seo)],
                          cwd=ROOT / "01-botbhai/botbhai", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return seo / "site"


def sites(seo_site):
    nt, hf = TH.netlify_rules, lambda p: TH.headers_file_rules(pathlib.Path(p).read_text())
    calc = ROOT / "05-deals/site/dist"
    out = [
        ("HQ site", ROOT / "00-hq/site", nt("00-hq/site/netlify.toml"), ["/index.html"]),
        ("BotBhai", ROOT / "01-botbhai/botbhai/web/dist", nt("01-botbhai/botbhai/netlify.toml"),
         ["/", "/index.html?niche=gym", "/inbox.html?demo=1", "/dashboard.html?demo=1", "/billing.html?demo=1", "/invoice-sample.html"]),
        ("BotBhai SEO client site", seo_site, hf(seo_site / "_headers"), ["/index.html"]),
        ("JobCard", ROOT / "02-jobcard/web", nt("02-jobcard/netlify.toml"), ["/index.html"]),
        ("Jyotish", ROOT / "02-jobcard/apps/jyotish", nt("02-jobcard/apps/jyotish/netlify.toml"), ["/index.html"]),
        ("Photo Studio", ROOT / "02-jobcard/apps/photo-studio", nt("02-jobcard/apps/photo-studio/netlify.toml"), ["/index.html"]),
        ("Bhasha Kids", ROOT / "02-jobcard/apps/bhasha-kids", nt("02-jobcard/apps/bhasha-kids/netlify.toml"), ["/index.html"]),
        ("Tab Lifeboat site (meta CSP)", ROOT / "04-extensions/site/_dist", None, ["/index.html", "/privacy.html", "/terms.html"]),
        ("Exam kit phone pages (meta CSP)", ROOT / "03-kits/engine/dist", None,
         ["/" + str(p.relative_to(ROOT / "03-kits/engine/dist")) for p in sorted((ROOT / "03-kits/engine/dist").glob("*/*-tracker.html"))]),
    ]
    if (calc / "index.html").exists():
        out.append(("Calculators", calc, hf(ROOT / "05-deals/site/public/_headers"),
                    ["/index.html", "/emi/", "/te/income-tax/", "/kits/", "/kits/thanks/?p=pay_TEST123456", "/legal/privacy/"]))
    else:
        print("  (calculators skipped: run npm run build in 05-deals/site)")
    return out


def poke(pg):
    """Exercise the page a little so script-built DOM (innerHTML, styles) is checked too."""
    pg.evaluate("""() => { for (const i of [...document.querySelectorAll('input:not([type=file]):not([type=hidden])')].slice(0, 3)) {
        try { i.value = i.type === 'number' ? '1000' : (i.value || 'a'); i.dispatchEvent(new Event('input', { bubbles: true })); } catch (e) {} }
      for (const d of [...document.querySelectorAll('details')].slice(0, 3)) d.open = true; }""")
    for b in pg.locator("button:visible, [role=tab]:visible").all()[:6]:
        try: b.click(timeout=800, no_wait_after=True)
        except Exception: pass
        pg.wait_for_timeout(120)


def main():
    seo_site = build(); fails = []
    with sync_playwright() as p:
        br = p.chromium.launch()
        for name, folder, rules, pages in sites(seo_site):
            srv, base = serve(folder, rules)
            ctx = br.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
            ctx.add_init_script(WATCH)
            if name == "Bhasha Kids":  # headless Chromium crashes in SpeechRecognition (with or without any CSP), so hide it
                ctx.add_init_script("delete window.SpeechRecognition; delete window.webkitSpeechRecognition;")
            ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("http://127.0.0.1", "data:", "blob:")) else r.abort())
            for path in pages:
                pg = ctx.new_page(); console = []
                pg.on("console", lambda m: console.append(m.text) if "Content Security Policy" in m.text else None)
                pg.on("dialog", lambda d: d.dismiss())
                missing = []  # a moved-out script that 404s shows no CSP violation, so catch missing files too
                pg.on("response", lambda r: missing.append(f"{r.status} {r.url}") if r.status >= 400 and r.url.startswith(base)
                      and "/api/" not in r.url and "/.netlify/" not in r.url and not r.url.endswith("favicon.ico") else None)
                pg.goto(base + path, wait_until="load"); pg.wait_for_timeout(600)
                if not path.startswith("/kits/thanks"): poke(pg)
                pg.wait_for_timeout(400)
                v = pg.evaluate("window.__csp") + console + missing
                if pg.url.startswith(base) is False: v.append("navigated away to " + pg.url)
                (fails.append(f"{name} {path}: " + " | ".join(v[:5])) if v else print(f"  ✓ {name} {path}: no CSP violations"))
                pg.close()
            ctx.close(); srv.shutdown()

        # Control: the harness must see a violation when one happens (inline script + inline style under a strict CSP).
        ctl = pathlib.Path(tempfile.mkdtemp()); (ctl / "x.html").write_text('<!doctype html><p style="color:red">x</p><script>1</script>')
        srv, base = serve(ctl, [("/*", {"content-security-policy": "default-src 'self'"})])
        pg = br.new_page(); pg.add_init_script(WATCH); pg.goto(base + "/x.html"); pg.wait_for_timeout(300)
        n = len(pg.evaluate("window.__csp")); srv.shutdown()
        (print(f"  ✓ control page: harness caught {n} violations") if n >= 2 else fails.append(f"harness missed violations on the control page ({n})"))

        # Framing: client sites (another origin) frame the chat page; owner pages refuse to be framed.
        bot_rules = TH.netlify_rules("01-botbhai/botbhai/netlify.toml")
        srv, base = serve(ROOT / "01-botbhai/botbhai/web/dist", bot_rules)
        host = pathlib.Path(tempfile.mkdtemp())
        (host / "index.html").write_text(f'<!doctype html><script src="{base}/widget.js" data-client="test" data-niche="salon" defer></script>'
                                         f'<iframe id="dash" src="{base}/dashboard.html?demo=1"></iframe><iframe id="inbox" src="{base}/inbox.html"></iframe>')
        hsrv, hbase = serve(host, None)
        pg = br.new_page(); pg.goto(hbase + "/index.html", wait_until="load"); pg.wait_for_timeout(1500)
        frames = {f.url.split("?")[0].rsplit("/", 1)[-1]: f for f in pg.frames if f != pg.main_frame}
        chat = frames.get("index.html")
        if chat and chat.evaluate("document.body.classList.contains('embed') && !!document.querySelector('#msgs')"): print("  ✓ widget.js chat frame loads on a client site")
        else: fails.append("BotBhai: widget.js chat frame did not load on another origin")
        for name in ("dashboard.html", "inbox.html"):
            f = frames.get(name)
            try: blocked = f is None or not f.evaluate("!!document.querySelector('main, header')")
            except Exception: blocked = True
            (print(f"  ✓ {name} refuses to load in another site's frame") if blocked else fails.append(f"BotBhai {name} loaded inside a foreign frame"))
        hsrv.shutdown(); srv.shutdown()

        # The exam kit page is mostly opened straight from the phone's files: meta CSP only, file:// URL.
        pg = br.new_page(); pg.add_init_script(WATCH)
        for f in sorted((ROOT / "03-kits/engine/dist").glob("*/*-tracker.html")):
            pg.goto(f.as_uri(), wait_until="load"); poke(pg); v = pg.evaluate("window.__csp")
            (fails.append(f"{f.name} (file://): {v[:3]}") if v else print(f"  ✓ {f.name} from file://: no CSP violations"))
            if not pg.evaluate("document.querySelectorAll('#syl details, #syl .topic').length"): fails.append(f"{f.name}: syllabus did not render (script blocked?)")
        br.close()
    if fails:
        print("\nCSP FAILURES:\n  " + "\n  ".join(fails)); sys.exit(1)
    print("ALL CSP BROWSER CHECKS PASSED")


if __name__ == "__main__":
    main()

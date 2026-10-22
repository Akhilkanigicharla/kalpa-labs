#!/usr/bin/env python3
"""390 px screen check for the Ledger Peaks mockups (A12; Kalpa design rules 1 + 2).

Landing, every dashboard tab and both X-ray pages, in light AND dark: no sideways scroll,
Kalpavruksha --hero token, Rozha One really loaded (self-hosted), no request leaves this machine,
no JS errors, every [data-lp] figure filled.
    python3 06-finops/design/screens.py [--out DIR]     (needs Python Playwright + Chromium)
"""
import argparse, functools, http.server, pathlib, sys, threading

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
CHECK = """() => {
  const vw = document.documentElement.clientWidth, bad = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect(); if (!r.width || !r.height) continue;
    let p = el.parentElement, scrolls = false;
    while (p && p !== document.body) { const o = getComputedStyle(p).overflowX; if (o === 'auto' || o === 'scroll' || o === 'hidden') { scrolls = true; break; } p = p.parentElement; }
    if (!scrolls && (r.right > vw + 1 || r.left < -1)) bad.push((el.tagName + '.' + el.className).slice(0, 50) + ' ' + Math.round(r.left) + '→' + Math.round(r.right));
  }
  const empty = [...document.querySelectorAll('[data-lp]')].filter((n) => !n.textContent.trim() || /undefined|NaN/.test(n.textContent)).map((n) => n.dataset.lp);
  const small = [...document.querySelectorAll('a.btn,button,.tabs button')].filter((b) => { const r = b.getBoundingClientRect(); return r.width && r.height < 44; }).map((b) => b.textContent.trim().slice(0, 20));
  return { scrollW: document.documentElement.scrollWidth, vw, bad: bad.slice(0, 6), empty, small,
           rozha: document.fonts.check('20px "Rozha One"') && [...document.fonts].some((f) => f.family.includes('Rozha') && f.status === 'loaded'),
           hero: getComputedStyle(document.documentElement).getPropertyValue('--hero').trim().toLowerCase() };
}"""
HERO = {"light": "#1d3a25", "dark": "#17301f"}
SHOTS = [("landing", "landing.html", None), ("xray", "xray.html", None)] + [
    (f"dashboard-{t}", "dashboard.html", t) for t in ("overview", "customers", "savings", "evidence")]


def run(out: pathlib.Path) -> list[str]:
    from playwright.sync_api import sync_playwright
    out.mkdir(parents=True, exist_ok=True)

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(REPO)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    origin = f"http://127.0.0.1:{srv.server_address[1]}"
    base = f"{origin}/06-finops/design/"
    fails = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for scheme in ("light", "dark"):
            ctx = b.new_context(viewport={"width": 390, "height": 844}, color_scheme=scheme)
            for name, page, tab in SHOTS:
                pg = ctx.new_page(); errs, ext = [], []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.on("request", lambda r: ext.append(r.url) if not r.url.startswith(origin) and not r.url.startswith("data:") else None)
                pg.goto(base + page); pg.wait_for_load_state("networkidle")
                if tab:
                    pg.click(f'.tabs button[data-v="{tab}"]'); pg.wait_for_timeout(150)
                    if pg.get_attribute(f'.tabs button[data-v="{tab}"]', "aria-selected") != "true":
                        fails.append(f"{name} {scheme}: tab did not open")
                r = pg.evaluate(CHECK)
                pg.screenshot(path=str(out / f"{name}-{scheme}.png"), full_page=True)
                tag = f"{name} {scheme}"
                if r["scrollW"] > r["vw"] or r["bad"]: fails.append(f"{tag}: sideways scroll {r['scrollW']}>{r['vw']} {r['bad']}")
                if r["hero"] != HERO[scheme]: fails.append(f"{tag}: --hero is {r['hero']!r}, not the Kalpavruksha token")
                if not r["rozha"]: fails.append(f"{tag}: Rozha One did not load from 00-hq/design/fonts")
                if r["empty"]: fails.append(f"{tag}: empty figures {r['empty']}")
                if r["small"]: fails.append(f"{tag}: touch targets under 44 px {r['small']}")
                if ext: fails.append(f"{tag}: external requests {ext[:3]}")
                if errs: fails.append(f"{tag}: JS errors {errs}")
                pg.close()
            ctx.close()
        b.close()
    srv.shutdown()
    return fails


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE / "screens")); a = ap.parse_args()
    fails = run(pathlib.Path(a.out))
    if fails:
        print("\n".join("  ✗ " + f for f in fails)); sys.exit(1)
    print(f"  ✓ {len(SHOTS) * 2} screens at 390 px (light + dark): no sideways scroll, Kalpavruksha tokens, "
          f"self-hosted fonts, no external requests, no JS errors → {a.out}")


if __name__ == "__main__":
    main()

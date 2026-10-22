#!/usr/bin/env python3
"""390 px screen check for the calculator + kits site (Kalpa design rules 1 + 2): every built page in light AND dark must
have no sideways scroll, use the Kalpavruksha tokens, keep Telugu out of fonts without Telugu letters, and raise no JS errors.
Run after `npm run build`:  python3 scripts/screens.py [--out DIR]   (needs Python Playwright + Chromium)"""
import argparse, functools, http.server, pathlib, sys, threading

SITE = pathlib.Path(__file__).resolve().parent.parent
CHECK = """() => {
  const vw = document.documentElement.clientWidth, bad = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect(); if (!r.width || !r.height) continue;
    let p = el.parentElement, scrolls = false;
    while (p && p !== document.body) { const o = getComputedStyle(p).overflowX; if (o === 'auto' || o === 'scroll' || o === 'hidden') { scrolls = true; break; } p = p.parentElement; }
    if (!scrolls && (r.right > vw + 1 || r.left < -1)) bad.push((el.tagName + '.' + el.className).slice(0, 50) + ' ' + Math.round(r.left) + '→' + Math.round(r.right));
  }
  const te = [...document.querySelectorAll('body *')].filter((el) => [...el.childNodes].some((n) => n.nodeType === 3 && /[\\u0C00-\\u0C7F]/.test(n.textContent))
     && /JetBrains|Rozha/.test(getComputedStyle(el).fontFamily.split(',')[0])).map((el) => el.textContent.trim().slice(0, 24));
  return { scrollW: document.documentElement.scrollWidth, vw, bad: bad.slice(0, 6), te,
           hero: getComputedStyle(document.documentElement).getPropertyValue('--hero').trim().toLowerCase() };
}"""
HERO = {"light": "#1d3a25", "dark": "#17301f"}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(SITE / "dist-screens")); a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    dist = SITE / "dist"; out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    pages = sorted(p.relative_to(dist).as_posix() for p in dist.rglob("index.html"))
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(dist)))
    threading.Thread(target=srv.serve_forever, daemon=True).start(); base = f"http://127.0.0.1:{srv.server_address[1]}/"
    fails, n = [], 0
    with sync_playwright() as p:
        b = p.chromium.launch()
        for scheme in ("light", "dark"):
            ctx = b.new_context(viewport={"width": 390, "height": 844}, color_scheme=scheme)
            for rel in pages:
                pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
                url = base + rel.replace("index.html", ""); pg.goto(url); pg.wait_for_load_state("networkidle")
                r = pg.evaluate(CHECK); name = (rel.replace("/index.html", "").replace("index.html", "home") or "home").replace("/", "-")
                pg.screenshot(path=str(out / f"{name}-{scheme}.png"), full_page=True); n += 1
                if r["scrollW"] > r["vw"] or r["bad"]: fails.append(f"{rel} {scheme}: sideways scroll {r['scrollW']}>{r['vw']} {r['bad']}")
                if r["hero"] != HERO[scheme]: fails.append(f"{rel} {scheme}: --hero is {r['hero']!r}, not the Kalpavruksha token")
                if r["te"]: fails.append(f"{rel} {scheme}: Telugu in a font without Telugu letters: {r['te']}")
                if errs: fails.append(f"{rel} {scheme}: JS errors {errs}")
                pg.close()
            ctx.close()
        b.close()
    srv.shutdown()
    if fails:
        print("\n".join("  ✗ " + f for f in fails)); sys.exit(1)
    print(f"  ✓ {n} screens at 390 px (light + dark): no sideways scroll, Kalpavruksha tokens, Telugu fonts, no JS errors → {out}")


if __name__ == "__main__":
    main()

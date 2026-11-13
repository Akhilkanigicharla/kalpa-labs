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
# Tap sweep (CLAUDE.md rule 5, same rules as 00-hq/site/tests/test_tap_sweep.py): every visible link, button and
# summary must be the top element at its own centre once scrolled to (nothing covered, e.g. by the bottom tab bar),
# and 44 px tall unless it is an inline link inside running text.
TAPS = """async () => {
  const bad = [];
  for (const e of document.querySelectorAll('a, button, summary')) {
    if (!e.getClientRects().length || getComputedStyle(e).visibility === 'hidden') continue;
    e.scrollIntoView({ block: 'center' }); await new Promise((r) => requestAnimationFrame(r));
    const r = e.getBoundingClientRect(); if (!r.width || !r.height) continue;
    const top = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
    const label = (e.textContent || e.getAttribute('aria-label') || '').trim().slice(0, 30);
    if (!top || (top !== e && !e.contains(top))) bad.push('covered: ' + label);
    const inline = e.tagName === 'A' && !e.matches('.btn,.card,[role=tab]') && e.closest('p,li,small');
    if (r.height < 44 && !inline) bad.push('small: ' + label + ' ' + Math.round(r.height) + 'px');
  }
  window.scrollTo(0, 0); return bad;
}"""
HERO = {"light": "#1d3a25", "dark": "#17301f"}
SHOTS = [("landing", "landing.html", None), ("xray", "xray.html", None)] + [
    (f"dashboard-{t}", "dashboard.html", t) for t in ("overview", "customers", "savings", "evidence")]


def _with_data(pg, base, data):
    """Serve dashboard.html with its embedded data block swapped (broken JSON or empty lists)."""
    import re
    html = (HERE / "dashboard.html").read_text()
    html = re.sub(r'(<script id="lp-data" type="application/json">).*?(</script>)',
                  lambda m: m.group(1) + data + m.group(2), html, count=1, flags=re.S)
    pg.route(base + "dashboard.html", lambda route: route.fulfill(body=html, content_type="text/html"))


def behaviour(ctx, base, scheme):
    """A188 UX patterns 5, 12, 20: filter chips, empty states, error recovery."""
    import json
    fails, tag = [], f"behaviour {scheme}"
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(base + "dashboard.html"); pg.wait_for_load_state("networkidle")
    total = pg.locator("#cust li").count()
    pg.click('a[data-go="customers"][data-filter="loss"]')
    if pg.get_attribute('.tabs button[data-v="customers"]', "aria-selected") != "true":
        fails.append(f"{tag}: 'Losing money' card did not open Customers")
    shown = pg.locator("#cust li:visible").count()
    loss = pg.evaluate("LP.data.customers.filter((c) => c.margin_pct < 0).length")
    if shown != loss or pg.get_attribute('#chips [data-f="loss"]', "aria-pressed") != "true":
        fails.append(f"{tag}: loss filter shows {shown} rows, want {loss}")
    pg.click('#chips [data-f="all"]')
    if pg.locator("#cust li:visible").count() != total:
        fails.append(f"{tag}: 'All' chip did not bring every customer back")
    if errs: fails.append(f"{tag}: JS errors {errs}")
    pg.close()

    # broken data → plain message + Retry, never a blank page or a JS crash
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    _with_data(pg, base, "{not json")
    pg.goto(base + "dashboard.html"); pg.wait_for_load_state("networkidle")
    box = pg.locator("#lp-error")
    if not box.count() or "safe" not in box.inner_text() or not pg.locator("#lp-error button").count():
        fails.append(f"{tag}: broken data did not show the recovery card with Retry")
    if errs: fails.append(f"{tag}: broken data JS errors {errs}")
    pg.close()

    # empty lists → helpful empty views
    d = json.loads(__import__("re").search(r'<script id="lp-data" type="application/json">(.*?)</script>',
                                           (HERE / "dashboard.html").read_text(), __import__("re").S).group(1))
    d.update(customers=[], savings=[], by_feature={}, by_model={}, by_day={})
    d["dpdp"]["questions"] = [dict(q, ok=True) for q in d["dpdp"]["questions"]]
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    _with_data(pg, base, json.dumps(d))
    pg.goto(base + "dashboard.html"); pg.wait_for_load_state("networkidle")
    for sel in ("#cust", "#ideas", "#feat", "#model", "#gaps", "#chart"):
        if not pg.locator(f"{sel} .empty").count():
            fails.append(f"{tag}: no empty state in {sel}")
    if errs: fails.append(f"{tag}: empty data JS errors {errs}")
    pg.close()
    return fails


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
                taps = pg.evaluate(TAPS)
                pg.screenshot(path=str(out / f"{name}-{scheme}.png"), full_page=True)
                tag = f"{name} {scheme}"
                if r["scrollW"] > r["vw"] or r["bad"]: fails.append(f"{tag}: sideways scroll {r['scrollW']}>{r['vw']} {r['bad']}")
                if r["hero"] != HERO[scheme]: fails.append(f"{tag}: --hero is {r['hero']!r}, not the Kalpavruksha token")
                if not r["rozha"]: fails.append(f"{tag}: Rozha One did not load from 00-hq/design/fonts")
                if r["empty"]: fails.append(f"{tag}: empty figures {r['empty']}")
                if r["small"]: fails.append(f"{tag}: touch targets under 44 px {r['small']}")
                if taps: fails.append(f"{tag}: tap sweep {taps[:4]}")
                if ext: fails.append(f"{tag}: external requests {ext[:3]}")
                if errs: fails.append(f"{tag}: JS errors {errs}")
                pg.close()
            fails += behaviour(ctx, base, scheme)
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

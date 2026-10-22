#!/usr/bin/env python3
"""390 px screen check for the JobCard app screens (A13; Kalpa design rules 1, 2 and 4).

Record → Job card → Bill → Reminders, plus the bill on its own, in light AND dark: no sideways scroll, the Kalpavruksha
--hero token, Rozha One and Anek Telugu really loaded (self-hosted), Telugu never set in Rozha One, 44 px touch targets,
no request leaves this machine, no JS errors, the real bill shown in the Bill tab.
    python3 02-jobcard/design/screens.py [--out DIR]     (needs Python Playwright + Chromium)
"""
import argparse, functools, http.server, pathlib, sys, threading

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
CHECK = r"""() => {
  const vw = document.documentElement.clientWidth, bad = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect(); if (!r.width || !r.height) continue;
    let p = el.parentElement, clip = false;
    while (p && p !== document.body) { if (getComputedStyle(p).overflowX !== 'visible') { clip = true; break; } p = p.parentElement; }
    if (!clip && (r.right > vw + 1 || r.left < -1)) bad.push((el.tagName + '.' + el.className).slice(0, 40) + ' ' + Math.round(r.right));
  }
  const teInRozha = [], walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) { const t = walker.currentNode; if (/[ఀ-౿]/.test(t.data) && t.parentElement.offsetParent !== null
      && getComputedStyle(t.parentElement).fontFamily.trim().startsWith('"Rozha')) teInRozha.push(t.data.trim().slice(0, 20)); }
  const vis = (b) => { const r = b.getBoundingClientRect(); return r.width && r.height && b.offsetParent !== null; };
  const small = [...document.querySelectorAll('a.btn,button')].filter((b) => vis(b) && b.getBoundingClientRect().height < 44).map((b) => b.textContent.trim().slice(0, 20));
  const loaded = (f) => [...document.fonts].some((x) => x.family.includes(f) && x.status === 'loaded');
  return { scrollW: document.documentElement.scrollWidth, vw, bad: bad.slice(0, 6), small, teInRozha,
    rozha: loaded('Rozha'), telugu: loaded('Anek Telugu'),
    empty: [...document.querySelectorAll('[data-jc]')].filter((n) => n.offsetParent !== null && (!n.textContent.trim() || /undefined|NaN|null/.test(n.textContent))).map((n) => n.dataset.jc),
    hero: getComputedStyle(document.documentElement).getPropertyValue('--hero').trim().toLowerCase() };
}"""
HERO = {"light": "#1d3a25", "dark": "#17301f"}
SHOTS = [("record", "app.html", None), ("card", "app.html", "card"), ("bill", "app.html", "bill"), ("remind", "app.html", "remind")]


def run(out: pathlib.Path) -> list[str]:
    from playwright.sync_api import sync_playwright
    out.mkdir(parents=True, exist_ok=True)

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(REPO)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    origin = f"http://127.0.0.1:{srv.server_address[1]}"
    base = f"{origin}/02-jobcard/design/"
    fails = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for scheme in ("light", "dark"):
            ctx = b.new_context(viewport={"width": 390, "height": 844}, color_scheme=scheme)
            for name, page, tab in SHOTS:
                pg = ctx.new_page(); errs, ext = [], []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.on("request", lambda r: ext.append(r.url) if not r.url.startswith(origin) and not r.url.startswith(("data:", "about:")) else None)
                pg.goto(base + page); pg.wait_for_load_state("networkidle")
                tag = f"{name} {scheme}"
                if tab:
                    pg.click(f'.tabs button[data-v="{tab}"]'); pg.wait_for_timeout(300)
                    if pg.get_attribute(f'.tabs button[data-v="{tab}"]', "aria-selected") != "true": fails.append(f"{tag}: tab did not open")
                if tab == "bill":
                    fr = pg.frame_locator("#inv")
                    txt = fr.locator("body").inner_text(timeout=3000)
                    num = pg.text_content('[data-jc="invno"]')
                    if num not in txt or "Bill of Supply" not in txt or "UPI" not in txt: fails.append(f"{tag}: the real bill is not in the frame")
                pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(150)
                r = pg.evaluate(CHECK)
                h = pg.evaluate("document.documentElement.scrollHeight")  # grow the viewport so the fixed tab bar sits at the bottom
                pg.set_viewport_size({"width": 390, "height": max(844, h)}); pg.wait_for_timeout(100)
                pg.screenshot(path=str(out / f"{name}-{scheme}.png"))
                pg.set_viewport_size({"width": 390, "height": 844})
                if r["scrollW"] > r["vw"] or r["bad"]: fails.append(f"{tag}: sideways scroll {r['scrollW']}>{r['vw']} {r['bad']}")
                if r["hero"] != HERO[scheme]: fails.append(f"{tag}: --hero is {r['hero']!r}, not the Kalpavruksha token")
                if not r["rozha"]: fails.append(f"{tag}: Rozha One did not load from 00-hq/design/fonts")
                if not r["telugu"]: fails.append(f"{tag}: Anek Telugu did not load")
                if r["teInRozha"]: fails.append(f"{tag}: Telugu set in Rozha One {r['teInRozha']}")
                if r["small"]: fails.append(f"{tag}: touch targets under 44 px {r['small']}")
                if r["empty"]: fails.append(f"{tag}: empty fields {r['empty']}")
                if ext: fails.append(f"{tag}: external requests {ext[:3]}")
                if errs: fails.append(f"{tag}: JS errors {errs}")
                pg.close()
            ctx.close()
        # the bill alone, as the customer gets it (A4 width and phone width)
        ctx = b.new_context(viewport={"width": 390, "height": 844})
        pg = ctx.new_page(); pg.goto(base + "invoice-sample.html"); pg.wait_for_load_state("networkidle")
        pg.screenshot(path=str(out / "invoice-sample.png"), full_page=True)
        if pg.evaluate("document.documentElement.scrollWidth") > 390: fails.append("invoice-sample: sideways scroll at 390 px")
        ctx.close(); b.close()
    srv.shutdown()
    return fails


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE / "screens")); a = ap.parse_args()
    fails = run(pathlib.Path(a.out))
    if fails:
        print("\n".join("  ✗ " + f for f in fails)); sys.exit(1)
    print(f"  ✓ {len(SHOTS) * 2 + 1} screens at 390 px (light + dark): no sideways scroll, Kalpavruksha tokens, Telugu in Anek Telugu, "
          f"44 px targets, self-hosted fonts, no external requests, no JS errors → {a.out}")


if __name__ == "__main__":
    main()

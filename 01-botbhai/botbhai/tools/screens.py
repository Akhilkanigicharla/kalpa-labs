#!/usr/bin/env python3
"""
Screen check for every BotBhai UI (Kalpa design rule 1 + 2): each page at 390 px wide, in light AND dark,
must have no sideways scroll, must use the Kalamkari tokens, and gets a full-page PNG for review.

  python3 tools/screens.py                 # builds demo + SEO site + cards, checks, PNGs → web/dist/screens/
  python3 tools/screens.py --out /tmp/x    # PNGs elsewhere

Needs Python Playwright with a Chromium (preinstalled in the cloud sandbox; skipped by test-all.sh if missing).
Nothing here touches the network except Google Fonts, which may fail offline; layout is checked with fallbacks too.
"""
import argparse, json, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
W = 390
KALAMKARI = {"light": "#1c2463", "dark": "#1b2266"}  # --hero in each theme: proves tokens.css is in use

OVERFLOW_JS = """() => {
  const vw = document.documentElement.clientWidth, bad = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect(); if (!r.width || !r.height) continue;
    // ignore children of an element that scrolls sideways on purpose (tables, tab rows, code)
    let p = el.parentElement, scrolls = false;
    while (p && p !== document.body) { const o = getComputedStyle(p).overflowX; if (o === 'auto' || o === 'scroll' || o === 'hidden') { scrolls = true; break; } p = p.parentElement; }
    if (!scrolls && (r.right > vw + 1 || r.left < -1)) bad.push((el.tagName + '.' + el.className).slice(0, 60) + ' ' + Math.round(r.left) + '→' + Math.round(r.right));
  }
  return { scrollW: document.documentElement.scrollWidth, vw, bad: bad.slice(0, 8),
           hero: getComputedStyle(document.documentElement).getPropertyValue('--hero').trim().toLowerCase(),
           display: getComputedStyle(document.documentElement).getPropertyValue('--f-display').trim() };
}"""

def pages(tmp):
    """(name, file url, wants Kalamkari --hero token, optional JS to run first)"""
    subprocess.check_call([sys.executable, str(ROOT / "build.py")], stdout=subprocess.DEVNULL)
    sys.path.insert(0, str(ROOT / "seo")); import seo_bot as S
    site = pathlib.Path(tmp) / "seo"; S.build("salon", S.load("salon", {"site_url": "https://glow.example", "areas": ["Ameerpet"]}), site)
    demo = (ROOT / "web" / "dist" / "index.html").as_uri()
    out = [("demo-leads", demo, True, None)]
    for tab in ["convo", "cards", "widget", "finder", "how"]:
        out.append((f"demo-{tab}", demo, True, f"document.querySelector('[data-tab={tab}]').click()"))
    out.append(("demo-voice", demo, True, "document.getElementById('m-voice').click()"))
    out.append(("demo-embed", demo + "?embed=1", True, None))
    inbox = (ROOT / "web" / "dist" / "inbox.html").as_uri()
    out.append(("invoice-sample", (ROOT / "web" / "dist" / "invoice-sample.html").as_uri(), True, None))
    billing = (ROOT / "web" / "dist" / "billing.html").as_uri()
    out.append(("billing-signin", billing, True, None))
    out.append(("billing-demo", billing + "?demo=1", True, None))
    out.append(("billing-paying", billing + "?demo=1", True, "document.querySelector('.inv .btn.ok').click()"))
    out.append(("inbox-signin", inbox, True, None))
    out.append(("inbox-list", inbox + "?demo=1", True, None))
    out.append(("inbox-chat", inbox + "?demo=1&open=919812345678", True, None))
    out.append(("inbox-notes", inbox + "?demo=1&open=919812345678", True, "document.querySelector('details.more').open = true"))
    out.append(("seo-home", (site / "site" / "index.html").as_uri(), True, None))
    first = sorted((site / "site").glob("*-in-*.html"))[0]
    out.append(("seo-service", first.as_uri(), True, None))
    return out

def run(out_dir):
    from playwright.sync_api import sync_playwright
    out_dir = pathlib.Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    fails, report = [], []
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        try: browser = pw.chromium.launch()
        except Exception: browser = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        for name, url, kal, js in pages(tmp):
            for theme in ["light", "dark"]:
                ctx = browser.new_context(viewport={"width": W, "height": 844}, device_scale_factor=1, color_scheme=theme)
                pg = ctx.new_page(); errors = []
                pg.on("pageerror", lambda e: errors.append(str(e)))
                pg.goto(url, wait_until="load", timeout=30000)
                if js: pg.evaluate(js)
                pg.wait_for_timeout(400)
                m = pg.evaluate(OVERFLOW_JS)
                shot = out_dir / f"{name}-{theme}.png"; pg.screenshot(path=str(shot), full_page=True)
                ok = m["scrollW"] <= W and not m["bad"] and not errors and (not kal or (m["hero"] == KALAMKARI[theme] and "Rozha One" in m["display"]))
                report.append({"page": name, "theme": theme, "scrollWidth": m["scrollW"], "ok": ok})
                if not ok: fails.append((name, theme, m, errors))
                ctx.close()
        browser.close()
    (out_dir / "report.json").write_text(json.dumps(report, indent=1))
    return fails, report

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(ROOT / "web" / "dist" / "screens"))
    a = ap.parse_args()
    fails, report = run(a.out)
    for f in fails: print("  ✗", f[0], f[1], json.dumps(f[2])[:400], f[3][:2])
    if fails: sys.exit(f"screen check failed: {len(fails)} of {len(report)}")
    print(f"  ✓ {len(report)} screens at {W} px (light + dark): no sideways scroll, Kalamkari tokens, no JS errors → {a.out}")

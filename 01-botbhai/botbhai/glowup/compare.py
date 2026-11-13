"""Before/after screenshots for a glow-up at 360, 768 and 1280 px (A199). Our own Playwright pipeline.

  python3 glowup/compare.py --owner <folder> --site <out>/site --out <out>/compare

"Before" is ONLY the owner's own old site (owner.json "old_site"), and only with signed permission; it is opened once
per width, read-only, no logins, no crawling of other pages. Writes before-<w>.png, after-<w>.png and compare.html.
"""
import argparse, functools, html, http.server, json, pathlib, sys, threading

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from glowup import GlowupError, check_permission  # noqa: E402

WIDTHS = (360, 768, 1280)


def serve(folder):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(folder)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/"


def run(owner, site, out):
    from playwright.sync_api import sync_playwright
    owner, out = pathlib.Path(owner), pathlib.Path(out)
    o = json.loads((owner / "owner.json").read_text(encoding="utf-8"))
    check_permission(o)
    before = str(o.get("old_site") or "")
    if not before.startswith(("https://", "http://127.0.0.1", "file://")):
        raise GlowupError("old_site must be the owner's own https address")
    out.mkdir(parents=True, exist_ok=True)
    srv, after = serve(site)
    shots = []
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            for w in WIDTHS:
                pg = b.new_page(viewport={"width": w, "height": 800})
                for name, url in (("before", before), ("after", after)):
                    pg.goto(url, wait_until="load", timeout=45000)
                    pg.wait_for_timeout(300)
                    pg.screenshot(path=str(out / f"{name}-{w}.png"), full_page=True)
                    shots.append(f"{name}-{w}.png")
                pg.close()
            b.close()
    finally:
        srv.shutdown()
    rows = "".join(f"<h2>{w} px</h2><div class=r><figure><figcaption>Before</figcaption><img src='before-{w}.png' alt='Old site at {w} px'></figure>"
                   f"<figure><figcaption>After</figcaption><img src='after-{w}.png' alt='New page at {w} px'></figure></div>" for w in WIDTHS)
    (out / "compare.html").write_text(
        "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><meta name=robots content=noindex>"
        f"<title>Glow-up: {html.escape(o.get('business', ''))}</title><style>body{{font:16px system-ui;margin:16px}}.r{{display:grid;"
        "grid-template-columns:1fr 1fr;gap:12px}img{max-width:100%;border:1px solid #ccc}</style>"
        f"<h1>Glow-up: {html.escape(o.get('business', ''))}</h1>{rows}", encoding="utf-8")
    return shots


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", required=True); ap.add_argument("--site", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    try:
        print(f"{len(run(a.owner, a.site, a.out))} screenshots → {a.out}/compare.html")
    except GlowupError as err:
        sys.exit(f"compare stopped: {err}")

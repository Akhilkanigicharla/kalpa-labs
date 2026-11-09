"""A189 check: Kingdom artifact (kingdom-control-room.html) at 390 px, light + dark.

1. Tap sweep on every tab (same rules as 00-hq/site/tests/test_tap_sweep.py: taps >= 44 px, nothing covered or off-screen).
2. UX 1: a quest status change shows at once, and goes back if the save fails.
The page gets the viewport meta the Artifact skeleton adds on publish. Run: python3 00-hq/design/test_kingdom_ux.py
"""
import functools, http.server, sys, tempfile, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "site" / "tests"))
import test_tap_sweep as T  # noqa: E402

HEAD = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>'
# a db whose every save fails, so the rollback path runs
FAILING_DB = """<script>window.claude={use:async k=>k==='db'?{collection:()=>({onSnapshot(){},doc:()=>({set:()=>Promise.reject(new Error('offline'))})})}:null};</script>"""


def main():
    tmp = Path(tempfile.mkdtemp())
    body = (HERE / "kingdom-control-room.html").read_text()
    (tmp / "k.html").write_text(HEAD + body + "</body></html>")
    (tmp / "fail.html").write_text(HEAD + FAILING_DB + body + "</body></html>")
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(tmp)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}/"
    bad = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for sc in ("light", "dark"):
            pg = b.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, color_scheme=sc)
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(base + "k.html"); pg.wait_for_timeout(300)
            tabs = pg.locator("nav.tabs button")
            for i in range(tabs.count()):
                tabs.nth(i).click(); pg.wait_for_timeout(250)
                name = tabs.nth(i).inner_text().strip()
                bad += [f"[{sc}/{name}] {x}" for x in T.sweep(pg)]
            # UX 1 rollback
            pg.goto(base + "fail.html"); pg.wait_for_timeout(400)
            pg.locator("nav.tabs button", has_text="Quests").click(); pg.wait_for_timeout(250)
            vis = '.seg button[data-set="doing"][aria-pressed="false"]:visible'
            pg.locator("details.task summary:visible").first.click(); pg.wait_for_timeout(200)  # open the first quest
            btn = pg.locator(vis).first
            qid = btn.get_attribute("data-id")
            btn.click(); pg.wait_for_timeout(300)
            now = pg.locator(f'.seg button[data-set="doing"][data-id="{qid}"]').first.get_attribute("aria-pressed")
            toast = pg.locator("#toast").inner_text()
            if now != "false":
                bad.append(f"[{sc}] failed save did not roll back {qid} (aria-pressed={now})")
            if "back as it was" not in toast:
                bad.append(f"[{sc}] failed save toast: {toast!r}")
            bad += [f"[{sc}] page error: {e}" for e in errs]
        b.close()
    srv.shutdown()
    for x in bad:
        print("FAIL", x)
    print("PASS kingdom UX (tap sweep every tab + rollback), 390 px light + dark" if not bad else f"{len(bad)} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

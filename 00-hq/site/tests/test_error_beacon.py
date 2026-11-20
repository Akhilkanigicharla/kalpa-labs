#!/usr/bin/env python3
"""Row 53 Error Tracking: a browser error on the site reaches /api/chat as a small client_error report.

    python3 00-hq/site/tests/test_error_beacon.py   # Python Playwright + Chromium
Checks: an uncaught error and an unhandled promise rejection each send one report with only
kind/msg/file/line/col (file without query string), and a page sends at most 3 reports.
"""
import functools, http.server, json, pathlib, threading
from playwright.sync_api import sync_playwright

SITE = pathlib.Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(SITE)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"
sent = []

def on_chat(route):
    body = json.loads(route.request.post_data or "{}")
    if body.get("type") == "client_error": sent.append(body)
    route.fulfill(status=204)

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 390, "height": 844})
    pg.route("**/api/chat", on_chat)
    pg.goto(base + "/index.html"); pg.wait_for_load_state("networkidle")
    assert sent == [], f"clean page load must send nothing, got {sent}"
    pg.add_script_tag(content="setTimeout(()=>{throw new Error('boom one')},0); Promise.reject(new Error('boom two'));")
    pg.wait_for_timeout(500)
    for i in range(5): pg.add_script_tag(content=f"setTimeout(()=>{{throw new Error('extra {i}')}},0)")
    pg.wait_for_timeout(800); b.close()
srv.shutdown()
kinds = sorted(s["kind"] for s in sent[:2])
assert kinds == ["error", "rejection"], sent
assert any("boom one" in s["msg"] for s in sent) and any("boom two" in s["msg"] for s in sent), sent
assert len(sent) == 3, f"cap is 3 reports per page, got {len(sent)}"
for s in sent:
    assert set(s) <= {"type", "kind", "msg", "file", "line", "col"}, s
    assert "?" not in s["file"], s
print(f"PASS error beacon: {len(sent)} reports, fields kind/msg/file/line/col only, cap 3")

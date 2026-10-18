#!/usr/bin/env python3
"""A50 website chat: when the server asks for a Turnstile check before saving a booking, the page shows the check, then
resends the same message with the token (no duplicate customer bubble). 390 px, light + dark, no sideways scroll.
Cloudflare and the chat function are faked, so no network. Run after build.py; needs Playwright."""
import http.server, json, os, pathlib, sys, threading
from playwright.sync_api import sync_playwright
dist = pathlib.Path(__file__).resolve().parent.parent / "web" / "dist"
shots = pathlib.Path(os.environ.get("SHOTS", dist / "screens")); shots.mkdir(parents=True, exist_ok=True)
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=str(dist), **k)
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{srv.server_port}/index.html?embed=1&client=11111111-2222-3333-4444-555555555555&niche=salon"
FAKE_TS = """window.turnstile = { render(el, o) {
  if (o.action !== 'booking' || !o.sitekey) throw new Error('bad options');
  const b = document.createElement('button'); b.textContent = 'Verify you are human (' + o.theme + ')'; b.className = 'fake-ts';
  b.style.cssText = 'width:100%;min-width:300px;height:65px'; b.onclick = () => o.callback('pass-token-1'); el.appendChild(b); } };"""
with sync_playwright() as p:
    b = p.chromium.launch()
    for scheme in ("light", "dark"):
        pg = b.new_page(viewport={"width": 390, "height": 844}, color_scheme=scheme); errs, posts = [], []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        def chat(route):
            body = json.loads(route.request.post_data); posts.append(body)
            if body.get("turnstile") == "pass-token-1": out = {"replies": [{"text": "✅ Booked! Facial, tomorrow 4:00 PM."}]}
            else: out = {"replies": [{"text": "One quick check so we know you're not a robot: tap the box below. Your slot is not booked yet."}], "check": {"sitekey": "1x00000000000000000000AA"}}
            route.fulfill(status=200, content_type="application/json", body=json.dumps(out))
        pg.route("**/.netlify/functions/chat", chat)
        pg.route("https://challenges.cloudflare.com/**", lambda r: r.fulfill(status=200, content_type="text/javascript", body=FAKE_TS))
        pg.goto(url); pg.fill("#text", "Kavya"); pg.press("#text", "Enter")
        pg.wait_for_selector(".ts .fake-ts", timeout=8000)
        assert f"({scheme})" in pg.inner_text(".fake-ts"), "widget theme follows the page"
        assert pg.evaluate("document.documentElement.scrollWidth <= 390"), "no sideways scroll with the check showing"
        pg.screenshot(path=str(shots / f"chat-turnstile-{scheme}-390.png"))
        pg.click(".fake-ts"); pg.wait_for_selector(".b.in >> text=Booked!", timeout=8000)
        assert [x.get("turnstile") for x in posts] == [None, "pass-token-1"], posts
        assert posts[0]["text"] == posts[1]["text"] == "Kavya"
        assert pg.locator(".b.out").count() == 1, "the resend does not repeat the customer's bubble"
        assert pg.locator(".ts").count() == 0 and not errs, errs
        pg.close()
    b.close(); srv.shutdown()
print("turnstile chat flow ok at 390 px, light + dark: check shown → token → same message resent → booked")

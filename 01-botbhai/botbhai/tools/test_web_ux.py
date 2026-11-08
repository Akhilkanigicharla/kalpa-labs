#!/usr/bin/env python3
"""A185 UX patterns on the built BotBhai web screens (web/dist) at 390 px:
optimistic reply (bubble shows at once, failed send keeps the text), two-tap "Mark done",
debounced lead search, and key fields checked when you leave them. Run after build.py; needs Playwright."""
import functools, http.server, json, pathlib, threading
from playwright.sync_api import sync_playwright

dist = pathlib.Path(__file__).resolve().parent.parent / "web" / "dist"
KEY = "11111111-2222-3333-4444-555555555555"
NOW = "2026-11-09T05:00:00Z"
convo = {"contact": "919800000001", "name": "Priya", "channel": "whatsapp", "status": "human", "opted_out": False,
         "window_open": True, "human_until": NOW, "updated_at": NOW,
         "last": {"direction": "in", "author": "customer", "body": "Slot at 4?", "created_at": NOW}}


def inbox_api(route):
    req = route.request
    if req.method == "GET" and "contact=" not in req.url:
        body = {"client": {"name": "Glow Studio"}, "conversations": [convo]}
    elif req.method == "GET":
        body = {"conversation": convo, "messages": [{"direction": "in", "author": "customer", "body": "Slot at 4?", "created_at": NOW}]}
    else:
        return route.fulfill(status=500, body=json.dumps({"message": "WhatsApp is down. Try again."}), content_type="application/json")
    route.fulfill(status=200, body=json.dumps(body), content_type="application/json")


# fetch() is blocked on file://, so serve dist over local http
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(dist)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{srv.server_address[1]}/"

with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    ctx = b.new_context(viewport={"width": 390, "height": 844})
    ctx.add_init_script(f"localStorage.setItem('botbhai.inbox.key','{KEY}')")
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))

    # 1 optimistic reply: the bubble is there before the server answers; a failed send keeps the words
    release = []
    def slow(route):
        if route.request.method == "POST": release.append(route); return
        inbox_api(route)
    pg.route("**/.netlify/functions/inbox**", slow)
    for page, lst in (("inbox.html", "#convos"), ("billing.html", "#invs")):  # skeleton rows before data arrives
        html = (dist / page).read_text(); i = html.index(lst.replace("#", 'id="'))
        assert "skeleton" in html[i:i + 400], f"{page}: no skeleton in {lst}"
    pg.goto(BASE + "inbox.html"); pg.wait_for_selector("#convos:not([aria-busy])"); pg.click(".convo:has-text(\"Priya\")")
    pg.fill("#reply", "See you at 4, Priya!"); pg.click(".send")
    pg.wait_for_selector(".b.staff.pending >> text=See you at 4")
    assert pg.input_value("#reply") == "", "draft should clear while sending"
    pg.wait_for_timeout(200); assert release, "reply POST not sent"
    inbox_api(release[0])
    pg.wait_for_selector(".b.staff.failed >> text=Not sent")
    assert pg.input_value("#reply") == "See you at 4, Priya!", "failed send must give the text back"
    assert pg.is_enabled(".send")

    # 2 Mark done needs a second tap
    pg.click("button:text-is(\"Mark done\")")
    pg.wait_for_selector("button:has-text(\"Tap again\")")

    # 3 key checked when you leave the field (inbox sign-in)
    pg2 = b.new_page(viewport={"width": 390, "height": 844}); pg2.on("pageerror", lambda e: errs.append(str(e)))
    for page in ("inbox.html", "dashboard.html", "billing.html"):
        pg2.goto(BASE + page)
        pg2.fill("#key", "abc"); pg2.press("#key", "Tab")
        assert pg2.get_attribute("#key", "aria-invalid") == "true", page
        assert pg2.text_content("#signin-err").strip(), page
        good = KEY if page != "billing.html" else "x" * 40
        pg2.fill("#key", good)
        assert pg2.get_attribute("#key", "aria-invalid") in (None, "false"), page
        assert not pg2.text_content("#signin-err").strip(), page

    # 4 lead search waits for a pause in typing
    pg3 = b.new_page(viewport={"width": 390, "height": 844}); pg3.on("pageerror", lambda e: errs.append(str(e)))
    pg3.goto(BASE + "dashboard.html" + "?demo=1")
    pg3.click(".tab[data-tab=leads]")
    pg3.evaluate("""() => { window.__renders = 0; const ul = document.querySelector('#leads, .leads');
        new MutationObserver(() => window.__renders++).observe(ul, { childList: true }); }""")
    pg3.type("#q", "Priya", delay=30)
    pg3.wait_for_timeout(500)
    n = pg3.evaluate("window.__renders")
    assert 1 <= n <= 2, f"search re-rendered {n} times for 5 letters"
    assert not errs, errs
    print("web UX ok: optimistic reply + retry text, two-tap Mark done, key checked on blur (3 screens), debounced search")
    b.close(); srv.shutdown()

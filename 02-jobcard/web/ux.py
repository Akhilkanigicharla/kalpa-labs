"""A186: JobCard PWA UX patterns at 390 px. Live mode is faked in the browser (config.js + Supabase answers are
intercepted), so nothing leaves this machine. Checks: skeleton before data, load error with a working Try again,
failed opt-in save rolls back and says so, sign out needs a second tap, phone number checked when you leave the field,
lead search waits for a pause in typing, empty search and empty bills say something.
Run: node 02-jobcard/web/build.mjs && python3 02-jobcard/web/ux.py"""
import functools, http.server, json, threading, time
from pathlib import Path
from playwright.sync_api import sync_playwright

web = Path(__file__).parent
class H(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".mjs": "text/javascript", ".webmanifest": "application/manifest+json"}
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(H, directory=str(web)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_port}"

assert "skeleton" in (web / "index.html").read_text(), "no skeleton in #main before data arrives"

LIVE = f"export default {json.dumps({'supabaseUrl': base + '/sb', 'anonKey': 'test', 'demo': False})};"
SESSION = json.dumps({"access": "a", "refresh": "r", "exp": int(time.time() * 1000) + 864e5, "user": "u"})
TABLES = {"technicians": [{"name": "Ravi", "business_name": "Ravi Cooling", "plan": "pilot", "language": "en"}],
          "customers": [{"id": "c1", "name": "Sita", "phone": "9000033333", "area": "Ameerpet", "opted_in_whatsapp": False}],
          "job_cards": [], "invoices": [], "amc_contracts": [], "usage_minutes": []}
state = {"fail_load": True}

def sb(route):
    r = route.request
    table = r.url.split("/rest/v1/")[-1].split("?")[0]
    if r.method == "PATCH": return route.fulfill(status=500, body="{}")
    if state["fail_load"]: return route.fulfill(status=500, body="{}")
    route.fulfill(status=200, content_type="application/json", body=json.dumps(TABLES.get(table, [])))

errs = []
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True, service_workers="block")
    ctx.route("**/config.js", lambda r: r.fulfill(status=200, content_type="text/javascript", body=LIVE))
    ctx.route("**/sb/**", sb)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))

    # sign-in: phone checked on blur, error clears once it is right
    pg.goto(base + "/?lang=en"); pg.wait_for_selector("#ph")
    pg.fill("#ph", "123"); pg.press("#ph", "Tab")
    assert pg.get_attribute("#ph", "aria-invalid") == "true" and pg.text_content("#err").strip(), "phone not checked on blur"
    pg.fill("#ph", "9000011111")
    assert pg.get_attribute("#ph", "aria-invalid") is None and not pg.text_content("#err").strip(), "phone error did not clear"

    # signed in, first load fails → Try again works
    pg.evaluate(f"localStorage.setItem('jobcard.session', {json.dumps(SESSION)})")
    pg.goto(base + "/?lang=en"); pg.wait_for_selector("#retry")
    state["fail_load"] = False; pg.click("#retry"); pg.wait_for_selector(".tabs:not([hidden])")

    # failed opt-in save rolls back and says so
    pg.click('.tabs button[data-tab="customers"]'); pg.check("[data-opt=c1]")
    pg.wait_for_selector("#toast:not([hidden])")
    assert not pg.is_checked("[data-opt=c1]"), "opt-in did not roll back after a failed save"

    # search: empty result says so; typing re-draws at most twice
    pg.evaluate("""() => { window.__n = 0; new MutationObserver(() => window.__n++).observe(document.querySelector('#main'), { childList: true }); }""")
    pg.type("#q", "zzzz", delay=30); pg.wait_for_timeout(400)
    n = pg.evaluate("window.__n"); assert 1 <= n <= 2, f"search re-drew {n} times for 4 letters"
    assert pg.is_visible(".empty"), "no empty state for a search with no match"
    assert pg.evaluate("document.activeElement.id") == "q", "search box lost focus"

    # bills tab with no bills says so
    pg.click('.tabs button[data-tab="bills"]'); assert pg.is_visible(".empty"), "no empty state for zero bills"

    # sign out needs a second tap
    pg.click("#signout"); assert pg.is_visible("#signout") and not pg.query_selector("#ph"), "signed out on the first tap"
    pg.click("#signout"); pg.wait_for_selector("#ph")
    assert not errs, errs
    b.close()
srv.shutdown()
print("ok: skeleton, Try again, opt-in rollback + toast, blur phone check, debounced search, empty states, two-tap sign out")

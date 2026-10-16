#!/usr/bin/env python3
"""Owner dashboard (A10) click-through on the built demo at 390 px: KPIs and today's timeline, tabs, lead filters and
search, Excel (CSV) download with Telugu-safe BOM and formula-injection guard, inbox link, sign-in errors; no JS errors."""
import pathlib, sys  # noqa: E401
ROOT = pathlib.Path(__file__).resolve().parent.parent
DASH = (ROOT / "web" / "dist" / "dashboard.html").as_uri()


def main():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844}, accept_downloads=True); pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(DASH + "?demo=1"); pg.wait_for_selector(".kpi b")
        kp = pg.locator("#kpis .kpi b").all_inner_texts()
        assert kp == ["6", "5", "2"], kp
        slots = pg.locator(".slot time").all_inner_texts()
        assert slots[0] == "10:00 AM" and slots[-1] == "7:00 PM" and len(slots) == 7, slots
        assert pg.locator(".slot .pill.cancelled").count() == 1 and pg.inner_text("#tomorrow") == "Tomorrow: 1"
        assert pg.get_attribute("#inbox-tab", "href") == "inbox.html?demo=1" and pg.inner_text("#waiting") == "2"
        print("  ✓ Today: 6 bookings / 5 confirmed / 2 need you; timeline in time order; cancelled marked; inbox badge 2")
        pg.click(".tab[data-tab=leads]"); assert pg.is_visible("#pane-leads") and not pg.is_visible("#pane-today")
        hot = pg.locator(".lead").count(); pg.click(".chip[data-f=all]"); alln = pg.locator(".lead").count()
        assert 0 < hot < alln == 10, (hot, alln)
        pg.fill("#q", "sravani"); assert pg.locator(".lead").count() == 1
        assert "booked" not in pg.inner_text("#leads").split("·")[-1] and "meta_ads" not in pg.inner_text("#leads")
        pg.fill("#q", "zzz"); assert "No lead matches" in pg.inner_text("#leads"); pg.fill("#q", "")
        print("  ✓ Leads: hot filter, all, search, owner-side words (no raw status codes)")
        pg.click(".tab[data-tab=report]"); assert pg.locator("#bars .bar").count() == 14 and pg.locator("#stats .kpi").count() == 4
        with pg.expect_download() as d:
            pg.click("#dl-bookings")
        raw = pathlib.Path(d.value.path()).read_bytes()
        assert raw.startswith(b"\xef\xbb\xbf") and b'"Date","Time","Name","Phone","Service","Status"' in raw
        print("  ✓ Report: 4 numbers, 14 daily bars, bookings download as Excel-ready CSV (BOM)")
        # live mode against a faked API (same JSON shape as functions/leads.js), with a hostile lead name
        import json
        api = {"client": {"name": "Live Salon", "niche": "salon"}, "today": "2026-10-16", "waiting": 0, "messages": [],
               "leads": [{"contact": "919848012345", "name": "=HYPERLINK(\"http://evil\")", "score": "hot", "status": "new", "details": {}, "source": "whatsapp", "updated_at": "2026-10-16T05:00:00Z"}],
               "bookings": [{"contact": "919848012345", "name": "Asha", "service": "Facial", "date_iso": "2026-10-16", "slot": "11:00 AM", "status": "confirmed", "confirmed_at": None}]}
        import functools, http.server, threading
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT / "web" / "dist")))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_address[1]}/dashboard.html"
        live = ctx.new_page(); live.on("pageerror", lambda e: errs.append(str(e)))
        seen = {}
        def handle(route):
            seen["auth"] = route.request.headers.get("authorization"); route.fulfill(status=200, content_type="application/json", body=json.dumps(api))
        live.route("**/.netlify/functions/leads", handle)
        key = "a" * 36
        live.goto(base + "#key=" + key); live.wait_for_selector(".slot")
        assert seen["auth"] == "Bearer " + key and "#key" not in live.url, (seen, live.url)
        assert live.inner_text("#biz").startswith("Live Salon") and live.locator(".slot").count() == 1
        live.click(".tab[data-tab=report]")
        with live.expect_download() as d2:
            live.click("#dl-leads")
        text = pathlib.Path(d2.value.path()).read_text(encoding="utf-8-sig")
        assert '"\'=HYPERLINK(""http://evil"")"' in text, text
        srv.shutdown()
        print("  ✓ live mode: #key= setup link read then wiped, Bearer header sent, a hostile =HYPERLINK name is neutralised in the Excel file")
        pg2 = ctx.new_page(); pg2.on("pageerror", lambda e: errs.append(str(e))); pg2.goto(DASH)
        pg2.fill("#key", "not-a-key"); pg2.click("#signin-form button"); assert "36 letters" in pg2.inner_text("#signin-err")
        assert pg2.evaluate("document.documentElement.scrollWidth") <= 390
        print("  ✓ sign-in rejects a malformed key with a plain message")
        assert not errs, errs
        b.close()
    print("dashboard UI tests passed")


if __name__ == "__main__":
    sys.exit(main())

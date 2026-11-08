"""Pilot form UX (UX-PATTERNS 6, 8, 9, 20) at 390 px, English + Telugu.

- smart validation: Indian mobile check on blur, inline message in the page language, focus to the first bad field
- autosave: name/phone/interest survive a reload; cleared after a successful send
- throttling: button shows "Sending…" and is disabled while sending
- graceful errors: offline → told before sending, details kept; server error → "details are safe" + Try again

Run: python3 00-hq/site/tests/test_form_ux.py [URL]   (default: serves 00-hq/site locally)
"""
import sys
from playwright.sync_api import sync_playwright
sys.path.insert(0, __import__("os").path.dirname(__file__))
from test_tap_sweep import serve  # noqa: E402


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else None
    srv = None
    if not url:
        srv, url = serve()
    fails = []

    def check(cond, what):
        if not cond:
            fails.append(what)

    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        pg = ctx.new_page()
        posts = []

        def route(r):
            if r.request.method == "POST" and r.request.url.rstrip("/") == url.rstrip("/"):
                posts.append(r.request.post_data)
                mode = pg.evaluate("window.__formMode || 'ok'")
                return r.fulfill(status=500 if mode == "fail" else 200, body="ok")
            return r.continue_()
        pg.route("**/*", route)
        pg.goto(url, wait_until="load")
        f = "form.signup"
        name, phone = pg.locator(f + " [name=name]"), pg.locator(f + " [name=phone]")

        # 9: bad phone -> inline message on blur, aria-invalid, no browser bubble needed
        name.fill("Ravi")
        phone.fill("12345")
        phone.blur()
        err = pg.locator("#phone-err")
        check(err.is_visible() and "10-digit" in err.inner_text(), "phone error shown on blur (English)")
        check(phone.get_attribute("aria-invalid") == "true", "phone aria-invalid")
        for good in ("98765 43210", "+91 98765 43210", "919876543210"):
            phone.fill(good)
            phone.blur()
            check(not err.is_visible(), f"valid phone accepted: {good}")

        # submit with missing consent -> inline message, focus moves there, no POST
        pg.locator(f + " button[type=submit]").click()
        check(pg.locator("#consent-err").is_visible(), "consent error shown")
        check(not posts, "nothing sent while invalid")

        # 6: autosave survives reload
        pg.wait_for_timeout(400)
        pg.reload(wait_until="load")
        check(name.input_value() == "Ravi", "name restored after reload")
        check(phone.input_value() == "919876543210", "phone restored after reload")

        # 20: offline -> told before sending, details kept
        ctx.set_offline(True)
        pg.locator(f + " [name=consent]").check()
        pg.locator(f + " button[type=submit]").click()
        msg = pg.locator("#formmsg")
        check("offline" in msg.inner_text().lower(), "offline message")
        check(name.input_value() == "Ravi" and not posts, "details kept, nothing sent offline")
        ctx.set_offline(False)

        # 20: server error -> details safe + Try again
        pg.evaluate("window.__formMode='fail'")
        pg.locator(f + " button[type=submit]").click()
        pg.wait_for_function("document.querySelector('#formmsg').textContent.includes('safe')")
        check(pg.locator("#formretry").is_visible(), "Try again button on failure")
        check(name.input_value() == "Ravi", "details kept after failure")

        # 8 + success: retry works, sending state, form cleared, draft cleared
        pg.evaluate("window.__formMode='ok'")
        pg.evaluate("""() => { window.__states = []; const b = document.querySelector('form.signup button[type=submit]');
            new MutationObserver(() => window.__states.push(b.disabled + '|' + b.textContent)).observe(b, {attributes:true, childList:true, subtree:true}); }""")
        pg.locator("#formretry").click()
        pg.wait_for_function("document.querySelector('#formmsg').textContent.includes('Thank you')")
        states = pg.evaluate("window.__states")
        check(any(s.startswith("true|Sending") for s in states), f"button showed Sending… while disabled ({states[:3]})")
        check(name.input_value() == "", "form cleared after success")
        check(pg.evaluate("localStorage.getItem('kalpa_pilot_draft')") is None, "draft cleared after success")
        check(len(posts) == 2, f"exactly 2 sends (fail + retry), got {len(posts)}")

        # Telugu: messages follow the page language
        pg.locator("button", has_text="తెలుగు").first.click()
        phone.fill("123")
        phone.blur()
        check(any("ఀ" <= ch <= "౿" for ch in err.inner_text()), "phone error in Telugu")
        b.close()
    if srv:
        srv.shutdown()
    for x in fails:
        print("FAIL", x)
    print("PASS form UX" if not fails else f"{len(fails)} problem(s)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()

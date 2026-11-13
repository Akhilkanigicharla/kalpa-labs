"""A203: free X-ray intake form on the landing page, tapped at 390 px in light + dark like a customer would."""
from __future__ import annotations

import functools
import http.server
import json
import sys
import threading
from pathlib import Path

import pytest

DESIGN = Path(__file__).resolve().parents[1] / "design"
REPO = DESIGN.parents[1]
CSV = b"timestamp,model,input_tokens,output_tokens,feature,customer_id_hash\n2026-10-12T05:00:00Z,gpt-4o,100,20,support,c_1\n"


def test_form_markup():
    html = (DESIGN / "landing.html").read_text()
    assert "coming soon" not in html and "disabled aria-disabled" not in html
    for name in ("company", "email", "file", "consent"):
        assert f'name="{name}"' in html and f'id="xf-{name}-err"' in html
    assert "14 days after the X-ray" in html and "withdraw consent" in html
    assert 'src="intake.js"' in html


@pytest.fixture(scope="module")
def site():
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(REPO)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    origin = f"http://127.0.0.1:{srv.server_address[1]}"
    with sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as e:  # only a missing browser skips; failing checks fail
            pytest.skip(f"Playwright browser not available: {e}")
        yield b, origin
        b.close()
    srv.shutdown()


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_form_like_a_customer(site, scheme):
    sys.path.insert(0, str(DESIGN))
    import screens
    b, origin = site
    ctx = b.new_context(viewport={"width": 390, "height": 844}, color_scheme=scheme)
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    reply = {"status": 503, "body": {"error": "x"}}
    pg.route(origin + "/api/xray-intake", lambda r: r.fulfill(status=reply["status"], content_type="application/json",
                                                                body=json.dumps(reply["body"])))
    pg.goto(origin + "/06-finops/design/landing.html#xray")
    pg.wait_for_load_state("networkidle")
    err = lambda n: pg.text_content(f"#xf-{n}-err").strip()

    # blur checks, one field at a time
    pg.click("#xf-company"); pg.click("#xf-email")
    assert "company name" in err("company")
    pg.fill("#xf-email", "ravi@gmail.com"); pg.click("#xf-company")
    assert "work email" in err("email")
    # send with gaps: every gap marked, focus on the first
    pg.fill("#xf-company", "చాయ్‌వాలా AI 🍵")
    pg.click("#xf-send")
    assert err("file") and err("consent")
    assert pg.evaluate("document.activeElement.id") == "xf-email"
    # touch targets: inputs and button 44 px+, nothing covered
    for sel in ("#xf-company", "#xf-email", "#xf-file", "#xf-send", ".consent"):
        assert pg.locator(sel).bounding_box()["height"] >= 44, sel
    assert pg.evaluate(screens.TAPS) == []
    assert pg.evaluate("document.documentElement.scrollWidth") <= 390

    # fix everything; server is down → failure with Retry
    pg.fill("#xf-email", "ops@chaiwala.ai")
    pg.set_input_files("#xf-file", files=[{"name": "usage.csv", "mimeType": "text/csv", "buffer": CSV}])
    pg.check("#xf-consent")
    assert not err("email") and not err("file") and not err("consent")
    pg.click("#xf-send")
    pg.wait_for_selector("#xf-status button")
    assert "Nothing was kept" in pg.text_content("#xf-status")
    # server says the file has prompts → shown on the file field
    reply.update(status=422, body={"errors": {"file": 'Your file has a "prompt" column.'}})
    pg.click("#xf-status button")
    pg.wait_for_function("document.getElementById('xf-file-err').textContent.includes('prompt')")
    # Retry works once the server is up
    reply.update(status=202, body={"ok": True, "id": "xr_1"})
    pg.click("#xf-send")
    pg.wait_for_selector("#xf-done")
    assert "ops@chaiwala.ai" in pg.text_content("#xf-done")
    assert errs == []
    ctx.close()


def test_offline_and_unreachable(site):
    b, origin = site
    ctx = b.new_context(viewport={"width": 390, "height": 844})
    pg = ctx.new_page()
    pg.route(origin + "/api/xray-intake", lambda r: r.abort())
    pg.goto(origin + "/06-finops/design/landing.html#xray")
    pg.fill("#xf-company", "Acme"); pg.fill("#xf-email", "a@acme.in")
    pg.set_input_files("#xf-file", files=[{"name": "u.json", "mimeType": "application/json", "buffer": b"[]1"}])
    pg.check("#xf-consent")
    pg.click("#xf-send")
    pg.wait_for_selector("#xf-status button")
    assert "couldn't reach" in pg.text_content("#xf-status")
    ctx.set_offline(True)
    pg.click("#xf-status button")
    pg.wait_for_function("document.getElementById('xf-status').textContent.includes('offline')")
    assert pg.is_enabled("#xf-send")
    ctx.close()

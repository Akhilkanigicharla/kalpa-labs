"""Phone check (bug 7 Nov 2026): tapping "Chat with our AI" must show the typing box above the
bottom bar and focus it. Run: python3 00-hq/site/tests/test_chat_button.py [url]"""
import pathlib, sys
from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else (pathlib.Path(__file__).resolve().parents[1] / "index.html").as_uri()
fails = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for scheme in ("light", "dark"):
        pg = b.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, color_scheme=scheme)
        pg.goto(url, wait_until="load")
        for sel in (".mbar a[href='#demo']", ".ctas a[href='#demo']"):
            pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(200)
            pg.locator(sel).first.tap(); pg.wait_for_timeout(1200)
            box = pg.locator("#askin").bounding_box()
            bar = pg.locator(".mbar").bounding_box()
            focused = pg.evaluate("document.activeElement && document.activeElement.id")
            if not box or box["y"] < 0 or box["y"] + box["height"] > bar["y"]:
                fails.append(f"{scheme} {sel}: typing box not visible above the bar ({box}, bar y={bar['y']})")
            if focused != "askin":
                fails.append(f"{scheme} {sel}: typing box not focused ({focused})")
        pg.close()
    b.close()
print("FAIL\n" + "\n".join(fails) if fails else "PASS: chat buttons open the typing box (390 px, light + dark)")
sys.exit(1 if fails else 0)

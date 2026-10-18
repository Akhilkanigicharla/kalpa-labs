"""A36: Record screen of the Expo app at 390 px, light + dark (web export of the real app).
Run: cd 02-jobcard/src && npx expo export --platform web --output-dir /tmp/jc-web && python3 ../design/app-shots.py /tmp/jc-web"""
import functools, http.server, json, sys, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

root = sys.argv[1]
out = Path(__file__).parent / "app"
out.mkdir(exist_ok=True)

class Spa(http.server.SimpleHTTPRequestHandler):
    def send_head(self):  # expo-router web export: unknown paths fall back to index.html
        if not Path(self.translate_path(self.path)).exists():
            self.path = "/index.html"
        return super().send_head()
    def log_message(self, *a): pass

srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Spa, directory=root))
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{srv.server_port}/"
tech = {"id": "t1", "name": "Ravi", "business_name": "Ravi Cooling Services", "phone": "9000022222", "gst_kind": "unregistered"}
note = "Split AC gas leak undi, gas refill 2500, capacitor, total 3000, customer Sita 9000033333 Ameerpet"
errors = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for theme in ("light", "dark"):
        pg = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2, color_scheme=theme)
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(url)
        pg.evaluate("""([tech, theme]) => { const k = 'mmkv.default\\\\';
          localStorage.setItem(k + 'IS_FIRST_TIME', 'false'); localStorage.setItem(k + 'token', JSON.stringify({ access: 'demo', refresh: 'demo' }));
          localStorage.setItem(k + 'technician', JSON.stringify(tech)); localStorage.setItem(k + 'SELECTED_THEME', theme);
          localStorage.setItem(k + 'local', 'te'); }""", [tech, theme])
        pg.goto(url)
        pg.get_by_test_id("mic").wait_for(timeout=20000)
        pg.get_by_test_id("note").fill(note)
        pg.get_by_test_id("total").wait_for()
        pg.wait_for_timeout(600)
        pg.screenshot(path=str(out / f"record-390-{theme}.png"), full_page=True)
        assert pg.evaluate("document.documentElement.scrollWidth") <= 390, "horizontal scroll at 390 px"
    b.close()
srv.shutdown()
print("errors:", errors[:3]) if errors else print("ok", sorted(x.name for x in out.iterdir()))

#!/usr/bin/env python3
"""A71 chat UI: business card first, real greeting with tap buttons (no "type hi"), one-line booking, typing dots,
voice mode with a language choice, and the free browser speech wired to the chosen language. 390 px, light + dark.
Speech is faked (no microphone in CI). Run after build.py; needs Playwright."""
import http.server, os, pathlib, threading
from playwright.sync_api import sync_playwright
dist = pathlib.Path(__file__).resolve().parent.parent / "web" / "dist"
shots = pathlib.Path(os.environ.get("SHOTS", dist / "screens")); shots.mkdir(parents=True, exist_ok=True)
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=str(dist), **k)
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{srv.server_port}/index.html?embed=1&niche=salon"
FAKE_SPEECH = """window.__heardLang = null; window.__said = [];
window.webkitSpeechRecognition = class { start() { window.__heardLang = this.lang; setTimeout(() => {
  const r = [{ transcript: 'beard trim tomorrow 7pm' }]; r.isFinal = true; this.onresult({ results: [r] }); this.onend(); }, 50); } };
window.SpeechRecognition = window.webkitSpeechRecognition;
window.SpeechSynthesisUtterance = class { constructor(t) { this.text = t; } };
Object.defineProperty(window, 'speechSynthesis', { value: { cancel() {}, getVoices() { return []; }, speak(u) { window.__said.push(u.text); } } });"""
with sync_playwright() as p:
    b = p.chromium.launch()
    for scheme in ("light", "dark"):
        pg = b.new_page(viewport={"width": 390, "height": 844}, color_scheme=scheme); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.add_init_script(FAKE_SPEECH)
        pg.goto(url); pg.wait_for_selector(".b.welcome"); pg.wait_for_selector("#quick button")
        assert "Glow Studio" in pg.inner_text(".b.welcome"), "business card first"
        first = pg.inner_text(".b.in:not(.welcome)")
        assert "Reply with a number" not in first and "*1.*" not in first, first
        labels = pg.locator("#quick button").all_inner_texts()
        assert labels[:2] == ["Book a service", "Price list"], labels
        assert pg.locator(".b.out").count() == 0, "no fake customer message on open"
        pg.fill("#text", "haircut men repu 7pm"); pg.press("#text", "Enter")
        pg.wait_for_selector(".typing"); pg.wait_for_selector(".b.in >> text=Your name", timeout=8000)
        assert pg.locator(".typing").count() == 0
        pg.screenshot(path=str(shots / f"chat-booking-{scheme}.png"))
        pg.click(".langs [data-lang=te-IN]")
        pg.click("#m-voice"); pg.wait_for_selector(".voice", state="visible")
        pg.click("#orb"); pg.wait_for_selector(".b.out >> text=beard trim tomorrow 7pm", timeout=5000)
        assert pg.evaluate("window.__heardLang") == "te-IN", "listens in the chosen language"
        pg.wait_for_function("window.__said.length > 1", timeout=8000)
        assert all("✨" not in t and "*" not in t for t in pg.evaluate("window.__said")), "no emoji or markdown read aloud"
        pg.screenshot(path=str(shots / f"chat-voice-{scheme}.png"))
        assert pg.evaluate("document.documentElement.scrollWidth") <= 390, "no sideways scroll"
        min_tap = pg.evaluate("Math.min(...[...document.querySelectorAll('#quick button, .round, .mode button')].filter(e => e.offsetParent).map(e => e.getBoundingClientRect().height))")
        assert min_tap >= 40, min_tap
        assert not errs, errs
    b.close()
print("chat UI ok at 390 px, light + dark: card first, tap buttons, one-line booking, typing dots, voice in the chosen language")

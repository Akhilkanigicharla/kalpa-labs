"""Turn X-ray data into one self-contained HTML file from the design template (design/xray.html).

Inlines the Kalpa tokens, the Ledger Peaks CSS (fonts as data: URLs) and the page script, so the
file opens offline, makes no external requests and prints as 2 A4 pages ("Save as PDF").
"""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DESIGN = ROOT / "06-finops" / "design"
TOKENS = ROOT / "00-hq" / "design" / "tokens.css"
FONTS = ROOT / "00-hq" / "design" / "fonts"
DATA_RE = re.compile(r'(<script id="lp-data" type="application/json">)(.*?)(</script>)', re.S)


def _css() -> str:
    css = (DESIGN / "lp.css").read_text(encoding="utf-8")

    def font(m):
        f = FONTS / Path(m.group(1)).name
        return "url(data:font/woff;base64," + base64.b64encode(f.read_bytes()).decode() + ")"
    return re.sub(r"url\((\.\./\.\./00-hq/design/fonts/[^)]+)\)", font, css)


def render(data: dict) -> str:
    html = (DESIGN / "xray.html").read_text(encoding="utf-8")
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = DATA_RE.sub(lambda m: m.group(1) + blob + m.group(3), html)
    tokens = TOKENS.read_text(encoding="utf-8")
    html = html.replace('<link rel="stylesheet" href="../../00-hq/design/tokens.css">', f"<style>{tokens}</style>")
    html = html.replace('<link rel="stylesheet" href="lp.css">', f"<style>{_css()}</style>")
    js = (DESIGN / "lp.js").read_text(encoding="utf-8")
    html = html.replace('<script src="lp.js"></script>', f"<script>{js}</script>")
    html = re.sub(r'<a class="btn btn-ghost" href="landing.html"[^>]*>.*?</a>', "", html)
    label = "LLM Bill X-ray · synthetic data" if data.get("synthetic") else "LLM Bill X-ray"
    html = html.replace("LLM Bill X-ray · sample · synthetic data", label)
    title = f"LLM Bill X-ray · {data['company']}".replace("&", "&amp;").replace("<", "&lt;")
    html = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", html, count=1)
    leftovers = re.findall(r'(?:href|src)="(?!data:)[^"#][^"]*"', html)
    if leftovers:
        raise RuntimeError(f"X-ray still links to external files: {leftovers}")
    return html


def to_pdf(html_path: Path, pdf_path: Path) -> int:
    """Print the HTML to A4 with headless Chromium (Playwright). Returns the page count."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto(Path(html_path).resolve().as_uri())
        pg.emulate_media(media="print")
        pg.pdf(path=str(pdf_path), format="A4", print_background=True,
               margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"})
        b.close()
    return len(re.findall(rb"/Type\s*/Page[^s]", Path(pdf_path).read_bytes()))

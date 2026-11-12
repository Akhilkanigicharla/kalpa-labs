"""A192: build the public Ledger Peaks site into 06-finops/site/_dist (20 SEO checks, 00-hq/design/SEO-CHECKS.md).

  python3 06-finops/site/build.py            # SITE_URL env overrides the host (default: the Netlify free subdomain)

Sources stay in 06-finops/design (landing.html, xray.html, lp.css, lp.js, intake.js); this script only
copies them, fixes the asset paths, and adds the SEO head, robots.txt, sitemap.xml, llms.txt and 404.html.
Not deployed here (rule 9): it goes live only on Akhil's "go".
"""
import html, json, os, re, shutil
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DESIGN = ROOT / "06-finops/design"
DIST = HERE / "_dist"
SITE = os.environ.get("SITE_URL", "https://ledger-peaks.netlify.app").rstrip("/")
FONTS = ["anek-latin-latin-600-normal.woff", "anek-latin-latin-700-normal.woff", "rozha-one-latin-400-normal.woff"]

# page in _dist -> (source, title 30-60, description 70-160)
PAGES = {
    "index.html": ("landing.html", "Ledger Peaks · AI bill in rupees per customer",
                   "Turn your OpenAI, Anthropic, Gemini or Langfuse usage logs into rupees per customer and feature, plus a DPDP "
                   "checklist. Free X-ray in 48 hours."),
    "sample-x-ray.html": ("xray.html", "Sample LLM Bill X-ray report · Ledger Peaks",
                          "A sample LLM Bill X-ray for a made-up Indian AI startup: cost per customer in rupees, margin, three "
                          "savings ideas and a DPDP score."),
}
ORG = {"@type": "Organization", "@id": f"{SITE}/#org", "name": "Kalpa Labs", "url": "https://kalpalabs.dpdns.org/",
       "address": {"@type": "PostalAddress", "addressLocality": "Hyderabad", "addressRegion": "Telangana", "addressCountry": "IN"}}


def url_of(name):
    return f"{SITE}/" if name == "index.html" else f"{SITE}/{name[:-5]}"


def seo_head(name, title, desc):
    url = url_of(name)
    if name == "index.html":
        graph = [ORG, {"@type": "WebSite", "@id": f"{SITE}/#site", "name": "Ledger Peaks", "url": f"{SITE}/",
                       "publisher": {"@id": f"{SITE}/#org"}},
                 {"@type": "Service", "name": "LLM Bill X-ray", "provider": {"@id": f"{SITE}/#org"}, "areaServed": "IN",
                  "description": desc, "offers": {"@type": "Offer", "price": "0", "priceCurrency": "INR",
                                                  "description": "Free 2-page X-ray of one usage export"}}]
    else:
        graph = [ORG, {"@type": "WebPage", "name": title, "url": url, "description": desc,
                       "isPartOf": {"@type": "WebSite", "url": f"{SITE}/"}}]
    e = lambda t: html.escape(t, quote=True)
    return (f'<meta name="description" content="{e(desc)}">\n<link rel="canonical" href="{url}">\n'
            '<meta property="og:type" content="website"><meta property="og:site_name" content="Ledger Peaks">\n'
            f'<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">\n'
            f'<meta property="og:url" content="{url}"><meta property="og:image" content="{SITE}/og.png">\n'
            '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">\n'
            '<meta property="og:image:alt" content="Ledger Peaks: which customer is your AI bill eating?">\n'
            f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{SITE}/og.png">\n'
            '<link rel="icon" href="data:,">\n'
            f'<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@graph": graph})}</script>\n')


def page(src, name, title, desc):
    t = (DESIGN / src).read_text()
    t = t.replace("../../00-hq/design/tokens.css", "vendor/tokens.css")
    t = t.replace('href="landing.html"', 'href="/"').replace('href="xray.html"', 'href="/sample-x-ray"')
    t = t.replace('class="logo" href="#"', 'class="logo" href="/"')
    t = re.sub(r"<title>.*?</title>", f"<title>{html.escape(title)}</title>", t, count=1, flags=re.S)
    t = re.sub(r'<meta name="description"[^>]*>\n?', "", t)
    t = t.replace("</title>\n", "</title>\n" + seo_head(name, title, desc), 1)
    # inline page scripts move to a file so the CSP can stay script-src 'self'
    js = name.replace(".html", ".page.js")
    inline = re.findall(r"<script>(.*?)</script>", t, flags=re.S)
    if 'onclick="print()"' in t:  # inline handlers are blocked by the CSP too
        t = t.replace('onclick="print()"', "data-print")
        inline.append("document.querySelectorAll('[data-print]').forEach((b) => b.addEventListener('click', () => print()));")
    if inline:
        (DIST / js).write_text("\n".join(inline))
        t = re.sub(r"<script>.*?</script>", "", t, flags=re.S)
        t = t.replace("</body>", f'<script src="{js}"></script>\n</body>', 1)
    return t


NOT_FOUND = """<!doctype html>
<html lang="en-IN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Page not found · Ledger Peaks</title><meta name="robots" content="noindex">
<link rel="stylesheet" href="/vendor/tokens.css"><link rel="stylesheet" href="/lp.css"></head>
<body><main class="wrap" style="padding:48px 0"><h1>This page is not here</h1>
<p>The link may be old. <a href="/" style="display:inline-flex;min-height:44px;align-items:center">Go to Ledger Peaks home</a></p></main></body></html>
"""

LLMS = """# Ledger Peaks

> Ledger Peaks, by Kalpa Labs (Hyderabad, India), turns an AI company's LLM usage export (OpenAI, Anthropic, Gemini, LiteLLM or Langfuse) into rupees per customer and per feature, with savings ideas and a DPDP checklist. It reads metadata only (model, tokens, customer id, feature), never prompts.

- [Home and free X-ray form]({site}/): send one usage export, get a 2-page X-ray in 48 hours, free.
- [Sample X-ray]({site}/sample-x-ray): what the report looks like, on synthetic data.

Prices for paid plans are not live yet. Uploaded files are deleted after 14 days.
"""


def build():
    shutil.rmtree(DIST, ignore_errors=True)
    (DIST / "vendor/fonts").mkdir(parents=True)
    shutil.copy(ROOT / "00-hq/design/tokens.css", DIST / "vendor/tokens.css")
    for f in FONTS:
        shutil.copy(ROOT / "00-hq/design/fonts" / f, DIST / "vendor/fonts" / f)
    css = (DESIGN / "lp.css").read_text().replace("../../00-hq/design/fonts/", "vendor/fonts/")
    (DIST / "lp.css").write_text(css)
    for f in ("lp.js", "intake.js"):
        shutil.copy(DESIGN / f, DIST / f)
    shutil.copy(HERE / "og.png", DIST / "og.png")
    for name, (src, title, desc) in PAGES.items():
        (DIST / name).write_text(page(src, name, title, desc))
    (DIST / "404.html").write_text(NOT_FOUND)
    today = date.today().isoformat()
    urls = "".join(f"<url><loc>{url_of(n)}</loc><lastmod>{today}</lastmod></url>" for n in PAGES)
    (DIST / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                                      f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nDisallow: /api/\n\nSitemap: {SITE}/sitemap.xml\n")
    (DIST / "llms.txt").write_text(LLMS.format(site=SITE))
    # Netlify: security headers (HSTS, CSP, no framing) + clean URLs; the API is not deployed until Akhil's go.
    (DIST / "_headers").write_text(
        "/*\n  Strict-Transport-Security: max-age=31536000; includeSubDomains\n  X-Frame-Options: DENY\n"
        "  X-Content-Type-Options: nosniff\n  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()\n  Referrer-Policy: strict-origin-when-cross-origin\n"
        "  Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'\n")
    return DIST


if __name__ == "__main__":
    print(build())

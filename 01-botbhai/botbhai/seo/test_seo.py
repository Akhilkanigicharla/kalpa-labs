# Run: python3 seo/test_seo.py  (offline)
import json, pathlib, re, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import seo_bot as S
for setup in ["salon", "gym", "realestate", "examkits"]:
    out = pathlib.Path(tempfile.mkdtemp())
    cfg = S.load(setup, {"site_url": "https://glow.example", "areas": ["Jubilee Hills", "Madhapur"]})
    urls = S.build(setup, cfg, out)
    assert len(urls) == 1 + len(cfg["catalog"]) * 2, (setup, len(urls))
    idx = (out / "site" / "index.html").read_text()
    blocks = [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', idx, re.S)]
    assert blocks[0]["@type"] == S.SCHEMA_TYPE[setup] and blocks[1]["@type"] == "FAQPage", setup
    assert "{" not in re.sub(r"<script.*?</script>|<style>.*?</style>", "", idx, flags=re.S), "unfilled placeholder in " + setup
    assert idx.count("https://wa.me/") == 1 and (out / "site" / "sitemap.xml").read_text().count("<loc>") == len(urls)
    assert sum(1 for _ in open(out / "gbp_posts.csv", encoding="utf-8-sig")) == 13
    print(f"  ✓ {setup}: {len(urls)} pages, schema {blocks[0]['@type']} + FAQPage, sitemap, 12 GBP posts, citations")
re_cfg = S.load("realestate", {}); offers = S.jsonld("realestate", re_cfg, "x")[0]["hasOfferCatalog"]["itemListElement"]
assert all("price" not in o for o in offers), "lakh/crore ranges must not become numeric prices"
sal = S.jsonld("salon", S.load("salon", {}), "x")[0]["hasOfferCatalog"]["itemListElement"]
assert sal[0]["price"] == "250" and all("price" not in o for o in sal if "from" in o["description"])
html_ = S.page("salon", S.load("salon", {"whatsapp": "919000000002"}), "t", "d", "", "u", "Haircut & styling (women)")
assert "text=Hi%2C%20I%27d%20like%20to%20book%20Haircut%20%26%20styling%20%28women%29" in html_.replace("&amp;", "&")
print("  ✓ prices: only plain ₹ amounts become schema prices; WhatsApp button text is fully encoded")
# Deep Scan v2: Lighthouse found white-on-#25d366 (1.98:1) and a missing favicon
def _lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
def _ratio(a, b):
    hi, lo = sorted([_lum(a), _lum(b)], reverse=True); return (hi + 0.05) / (lo + 0.05)
wa_bg = re.search(r"\.wa\{[^}]*background:(#[0-9a-f]{6});color:(#[0-9a-f]{3,6})", S.CSS)
fg = wa_bg.group(2) if len(wa_bg.group(2)) == 7 else "#ffffff"
assert _ratio(fg, wa_bg.group(1)) >= 4.5, ("WhatsApp button contrast", _ratio(fg, wa_bg.group(1)))
root = dict(re.findall(r"--(\w+):(#[0-9a-f]{6})", S.CSS))
assert _ratio(root["accent"], root["bg"]) >= 4.5 and _ratio(root["muted"], root["bg"]) >= 4.5 and _ratio("#ffffff", "#0e7c66") >= 4.5
with tempfile.TemporaryDirectory() as d:
    out = pathlib.Path(d); S.build("salon", S.load("salon", {}), out)
    ico = (out / "site" / "favicon.svg").read_text(); idx = (out / "site" / "index.html").read_text()
    assert ico.startswith("<svg") and ">G</text>" in ico and 'rel="icon" href="/favicon.svg"' in idx
print("  ✓ WCAG AA contrast on the WhatsApp button, links and muted text; favicon.svg linked")
print("seo bot tests passed")

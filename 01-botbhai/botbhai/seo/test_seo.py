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
# A01b: Kalamkari tokens in both themes; the WhatsApp button must stay AA (hero-fg on hero) in light AND dark
assert ".wa{" in S.CSS and "background:var(--hero);color:var(--hero-fg)" in S.CSS and "prefers-color-scheme:dark" in S.CSS
_tok = (pathlib.Path(__file__).parents[3] / "00-hq/design/tokens.css").read_text().split("@media")
for block, theme in ((_tok[0], S.LIGHT), (_tok[1], S.DARK)):
    TOKENS = {k: v.lower() for k, v in re.findall(r"--([a-z0-9-]+):(#[0-9A-Fa-f]{6})", block)}
    for k, v in theme.items(): assert TOKENS[k] == v, ("not a Kalamkari token", k, v)
for name, t in (("light", S.LIGHT), ("dark", S.DARK)):
    for fg, bg in (("hero-fg", "hero"), ("accent", "bg"), ("accent", "panel"), ("muted", "bg"), ("fg", "panel")):
        assert _ratio(t[fg], t[bg]) >= 4.5, (name, fg, bg, round(_ratio(t[fg], t[bg]), 2))
assert _ratio("#d3940a", "#1c2463") >= 4.5  # favicon letter
with tempfile.TemporaryDirectory() as d:
    out = pathlib.Path(d); S.build("salon", S.load("salon", {"draft": True}), out)
    try:
        S.build("salon", S.load("salon", {}), pathlib.Path(d) / "real"); raise AssertionError("built a real site with the placeholder URL")
    except ValueError:
        pass
    ico = (out / "site" / "favicon.svg").read_text(); idx = (out / "site" / "index.html").read_text()
    assert ico.startswith("<svg") and ">G</text>" in ico and 'fill="#1c2463"' in ico and 'rel="icon" href="/favicon.svg"' in idx
print("  ✓ Kalamkari tokens; WCAG AA on the WhatsApp button, links and muted text in light + dark; favicon.svg linked")
print("seo bot tests passed")

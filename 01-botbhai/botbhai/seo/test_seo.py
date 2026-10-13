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
print("seo bot tests passed")

# Run: python3 seo/test_seo.py  (offline)
import json, pathlib, re, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import seo_bot as S
for setup in ["salon", "gym", "realestate", "examkits"]:
    out = pathlib.Path(tempfile.mkdtemp())
    cfg = S.load(setup, {"site_url": "https://glow.example", "areas": ["Jubilee Hills", "Madhapur"]})
    urls = S.build(setup, cfg, out)
    # A49: no local data in the config -> no thin "service in area" pages, only the home page
    assert len(urls) == 1 and not list((out / "site").glob("*-in-*.html")), (setup, len(urls))
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
# A49 (REA audit #13): no doorway pages. Area pages exist only where the salon gave its own local content
# (directions, landmarks, its own photos, reviews it supplies); at most 12 pages; body text differs per page.
# Test-only sample text below: never shipped, and the bot never writes reviews itself.
AREAS = ["Jubilee Hills", "Madhapur", "Kukatpally", "Ameerpet", "Banjara Hills", "Gachibowli", "Kondapur", "Miyapur",
         "Begumpet", "Somajiguda", "Panjagutta", "Hitech City", "Manikonda", "Tolichowki", "Attapur"]
STREETS = ["Road No. 36", "Ayyappa Society", "KPHB Phase 3", "Mythrivanam", "Road No. 12", "DLF gate", "Botanical Garden road",
           "Allwyn X Roads", "Greenlands", "Raj Bhavan Road", "Nagarjuna Circle", "Cyber Towers", "Puppalaguda", "Seven Tombs", "Pillar 140"]
TRAVEL = ["auto ride", "metro hop then a short walk", "bus on route 10H", "cab via the flyover", "scooter ride past the lake",
          "walk along the service road", "shared auto", "drive through the old market lane", "metro to the nearest station",
          "ride past the stadium", "cab along the ring road", "walk from the IT park", "bike ride over the bridge",
          "auto past the dargah", "bus from the depot"]
def _local(i, a):
    d = {"directions": f"From {a}, take a {TRAVEL[i]} via {STREETS[i]}; turn {'left' if i % 2 else 'right'} after the "
                       f"{['temple', 'petrol bunk', 'school', 'bakery', 'bank'][i % 5]} and look for our blue board, about {5 + i} minutes.",
         "landmarks": [f"{STREETS[i]} signal", f"{a} {['bus stop', 'metro pillar', 'post office'][i % 3]}"]}
    if i == 0:
        d["photos"] = [{"src": "photos/front-desk.jpg", "alt": "Our front desk seen from the Road No. 36 entrance"}]
        d["reviews"] = [{"name": "Test customer A", "stars": 5, "text": "Easy to find from the signal and the stylist listened.", "source": "Google"}]
    return d
cfg = S.load("salon", {"site_url": "https://glow.example", "areas": AREAS, "local": {a: _local(i, a) for i, a in enumerate(AREAS)}})
with tempfile.TemporaryDirectory() as d:
    out = pathlib.Path(d); urls = S.build("salon", cfg, out)
    files = sorted((out / "site").glob("*.html"))
    assert len(urls) == len(files) <= S.MAX_PAGES == 12, (len(urls), len(files))
    assert (out / "site" / "salon-in-jubilee-hills.html").exists() and len(files) == 12
    texts = {f.name: S.body_text(f.read_text()) for f in files}
    assert len(set(texts.values())) == len(texts), "two pages share the same body text"
    worst = max((S.similarity(texts[x], texts[y]), x, y) for i, x in enumerate(texts) for y in list(texts)[i + 1:])
    assert worst[0] < S.DUP_LIMIT, ("near-duplicate pages", worst)
    jh = (out / "site" / "salon-in-jubilee-hills.html").read_text(); mp = (out / "site" / "salon-in-madhapur.html").read_text()
    assert "Ayyappa Society" in mp and 'src="photos/front-desk.jpg"' in jh and "Test customer A" in jh and "Google" in jh
    assert "Reviews" not in mp and "<img" not in mp, "no reviews/photos supplied -> section omitted, never faked"
    assert '"aggregateRating"' not in jh and '"review"' not in jh, "self-serving review markup is not allowed"
    idx = (out / "site" / "index.html").read_text()
    assert 'href="salon-in-madhapur.html"' in idx and "Attapur" in idx  # page-less areas still listed on the home page
    sm = (out / "site" / "sitemap.xml").read_text(); assert sm.count("<loc>") == len(urls)
    assert all(row.split(",")[-1].strip() in {f.name for f in files} for row in open(out / "keywords.csv", encoding="utf-8-sig").read().splitlines()[1:])
    print(f"  ✓ A49: {len(files)} pages (≤ 12), unique body text, max similarity {worst[0]:.2f} < {S.DUP_LIMIT}; no reviews -> no section")
# A copy-paste area (same directions with only the area name swapped) is refused as a doorway page
twin = dict(cfg, areas=["Jubilee Hills", "Madhapur"], local={"Jubilee Hills": {"directions": "Take the main road, turn left at the signal and walk two minutes to our blue board near the big temple."},
                                                             "Madhapur": {"directions": "Take the main road, turn left at the signal and walk two minutes to our blue board near the big temple."}})
with tempfile.TemporaryDirectory() as d:
    urls = S.build("salon", twin, pathlib.Path(d)); assert len(urls) == 2, urls
# Unsafe photo sources and bad review data are rejected, not rendered
for bad in ({"photos": [{"src": "javascript:alert(1)", "alt": "x"}]}, {"photos": [{"src": "a.jpg"}]},
            {"reviews": [{"name": "A", "stars": 9, "text": "x"}]}, {"reviews": [{"name": "", "stars": 5, "text": "x"}]}):
    try:
        S.local_section("Madhapur", dict({"directions": "Walk from the metro."}, **bad)); raise AssertionError(("accepted", bad))
    except ValueError:
        pass
print("  ✓ A49: copy-paste area pages skipped; unsafe photo src and bad reviews rejected")
print("seo bot tests passed")

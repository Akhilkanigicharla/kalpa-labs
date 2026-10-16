#!/usr/bin/env python3
"""
BotBhai SEO bot — makes a client easy to find on Google, Google Maps and AI search (ChatGPT, Gemini,
Perplexity) for "<service> near me" / "<service> in <area>" searches. No paid tools.

For one client it generates (into --out):
  site/index.html                 fast one-page site: name/address/phone (NAP), services + prices, hours,
                                  FAQs, WhatsApp booking button, schema.org JSON-LD (LocalBusiness + FAQPage)
  site/<service>-in-<area>.html   one honest page per service × nearby area ("Hair spa in Jubilee Hills")
  site/sitemap.xml, robots.txt, llms.txt   for Google and AI crawlers
  gbp_posts.csv                   12 weeks of Google Business Profile posts (offers, tips, festivals)
  citations.csv                   free listings to create, with the exact NAP to paste everywhere
  keywords.csv                    the search phrases each page targets
  review_replies.md               reply templates by star rating (owner approves; never auto-post fake reviews)

Usage: python seo/seo_bot.py --setup salon --config client.json --out build/glow-studio
       (client.json overrides the setup's bot.config.json: business, address, phone, whatsapp, areas, site_url)
"""
import argparse, csv, datetime as dt, html, json, pathlib, re, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA_TYPE = {"salon": "BeautySalon", "gym": "ExerciseGym", "realestate": "RealEstateAgent", "examkits": "EducationalOrganization"}
CITATIONS = {
    "common": [("Google Business Profile", "https://business.google.com", "Most important: Maps + 'near me' searches"),
               ("Bing Places", "https://www.bingplaces.com", "Import from Google in 2 minutes"),
               ("Apple Business Connect", "https://businessconnect.apple.com", "iPhone Maps users"),
               ("Facebook Page", "https://www.facebook.com/pages/create", "Needed for Meta ads anyway"),
               ("Instagram Business", "https://www.instagram.com", "Link the WhatsApp number in profile"),
               ("Justdial (free listing)", "https://www.justdial.com/Free-Listing", "Big in Indian local search; ignore paid upsell calls"),
               ("Sulekha", "https://www.sulekha.com", "Local services directory")],
    "salon": [("magicpin", "https://magicpin.in", "Salon discovery in Hyderabad")],
    "gym": [("Google Fit-friendly listing via GBP attributes", "https://business.google.com", "Add 'women-only batch', 'personal training'")],
    "realestate": [("TS-RERA agent page", "https://rera.telangana.gov.in", "Show RERA number on site and profiles"),
                   ("99acres / MagicBricks / Housing.com", "https://www.99acres.com", "Owner/agent listings; free tiers vary")],
    "examkits": [("UrbanPro", "https://www.urbanpro.com", "Tutors and coaching institutes"),
                 ("YouTube channel", "https://www.youtube.com", "Short solved questions rank well for exam searches")],
}
# Telangana holiday dates (lunar festivals move every year; source: cleartax.in Telangana 2026 holiday list). Add 2027 dates when announced.
FESTIVALS = [("2026-01-14", "Sankranti"), ("2026-03-04", "Holi"), ("2026-03-08", "Women's Day"), ("2026-03-20", "Ugadi"),
             ("2026-10-11", "Bathukamma"), ("2026-10-20", "Dussehra"), ("2026-11-08", "Diwali"), ("2026-12-25", "Christmas"),
             ("2027-01-14", "Sankranti"), ("2027-03-08", "Women's Day")]

def clean(t, cfg):
    return re.sub(r"\*", "", str(t).replace("{phone}", cfg.get("phone", "")).replace("{business}", cfg.get("business", "")).replace("{address}", cfg.get("address", "")))

def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

PLACEHOLDER_URL = "https://example.netlify.app"


def load(setup, overrides):
    cfg = json.loads((ROOT / "setups" / setup / "bot.config.json").read_text())
    cfg.update(overrides)
    cfg.setdefault("areas", ["Jubilee Hills", "Banjara Hills", "Madhapur", "Kukatpally", "Gachibowli"])
    cfg.setdefault("site_url", PLACEHOLDER_URL)
    cfg.setdefault("whatsapp", re.sub(r"\D", "", cfg.get("phone", "")))
    return cfg

def price_number(p):
    """Only a plain single price ("₹1,200") becomes a schema.org price; ranges, lakhs/crores and 'from' prices stay text."""
    m = re.fullmatch(r"\s*₹\s?([\d,]+)\s*", p); return m.group(1).replace(",", "") if m else None

def jsonld(setup, cfg, page_url, service=None, area=None):
    biz = {"@context": "https://schema.org", "@type": SCHEMA_TYPE[setup], "name": cfg["business"], "url": cfg["site_url"],
           "telephone": cfg["phone"], "address": {"@type": "PostalAddress", "streetAddress": cfg["address"], "addressLocality": "Hyderabad",
           "addressRegion": "Telangana", "addressCountry": "IN"}, "openingHours": cfg["hours"], "areaServed": cfg["areas"],
           "hasOfferCatalog": {"@type": "OfferCatalog", "name": cfg["catalogTitle"], "itemListElement": [
               {"@type": "Offer", "itemOffered": {"@type": "Service", "name": c["name"]}, "priceCurrency": "INR",
                **({"price": price_number(c["price"])} if price_number(c["price"]) else {}),
                "description": c["price"]} for c in cfg["catalog"]]}}
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": "What are your timings?", "acceptedAnswer": {"@type": "Answer", "text": cfg["hours"]}},
        {"@type": "Question", "name": f"How do I book at {cfg['business']}?", "acceptedAnswer": {"@type": "Answer", "text": f"Message us on WhatsApp at {cfg['phone']}; booking takes under a minute, any time of day."}},
    ] + [{"@type": "Question", "name": f"Do you offer {f['k'][0]}?", "acceptedAnswer": {"@type": "Answer", "text": clean(f["a"], cfg)}} for f in cfg["faqs"][:4]]}
    return [biz, faq]

# Kalpa "Kalamkari" design system (00-hq/design/tokens.css), trimmed to what a client site needs. Light + dark.
# The WhatsApp button is hero indigo with a turmeric ring: AA contrast in both themes (test_seo.py checks it).
LIGHT = {"bg": "#eeedf3", "panel": "#fbfbfd", "fg": "#191c33", "muted": "#5d6079", "rule": "#dcdbe7", "accent": "#2a3a8f",
         "hero": "#1c2463", "hero-fg": "#f6f2e8", "gold": "#d3940a", "madder": "#b23a2c"}
DARK = {"bg": "#0e1230", "panel": "#161b42", "fg": "#ecebf7", "muted": "#a3a7cc", "rule": "#2a3060", "accent": "#9aabff",
        "hero": "#1b2266", "hero-fg": "#f6f2e8", "gold": "#f2b840", "madder": "#f0745f"}
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Rozha+One&family=Anek+Latin:wght@400;600;700&family=Anek+Telugu:wght@400;600&display=swap">')
def _vars(d): return ";".join(f"--{k}:{v}" for k, v in d.items())
CSS = (":root{" + _vars(LIGHT) + ";--f-display:'Rozha One','Noto Serif',Georgia,serif;--f-body:'Anek Latin','Anek Telugu',system-ui,-apple-system,'Segoe UI',sans-serif;"
       "--temple:radial-gradient(circle at 7px 5px,var(--gold) 2.4px,transparent 2.8px) 0 0/14px 10px,linear-gradient(135deg,transparent 0 50%,var(--madder) 50%) 0 0/7px 10px}"
       "@media (prefers-color-scheme:dark){:root{" + _vars(DARK) + ";color-scheme:dark}}"
       "*{box-sizing:border-box}body{margin:0;font:17px/1.6 var(--f-body);color:var(--fg);background-color:var(--bg);"
       "background-image:radial-gradient(color-mix(in srgb,var(--accent) 12%,transparent) 1px,transparent 1.4px);background-size:18px 18px}"
       "body::before{content:'';display:block;height:10px;background:var(--temple)}"
       "main{max-width:760px;margin:0 auto;padding:24px 16px 104px}"
       "h1,h2{font-family:var(--f-display);font-weight:400;letter-spacing:.005em;text-wrap:balance}"
       "h1{font-size:clamp(30px,7vw,44px);line-height:1.1;margin:8px 0;color:var(--fg)}h2{font-size:24px;margin:36px 0 8px}h3{font-size:17px;margin:20px 0 4px}"
       ".muted{color:var(--muted)}table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--rule);border-radius:12px;overflow:hidden}"
       "td{padding:10px 12px;border-bottom:1px solid var(--rule);overflow-wrap:anywhere}td:last-child{text-align:right;font-weight:600;white-space:nowrap}"
       ".wa{position:fixed;left:16px;right:16px;bottom:16px;max-width:728px;margin:0 auto;display:flex;align-items:center;justify-content:center;min-height:52px;"
       "text-align:center;background:var(--hero);color:var(--hero-fg);font-weight:700;padding:14px;border-radius:999px;text-decoration:none;"
       "box-shadow:0 0 0 3px var(--gold),0 12px 28px -12px #1c2463}a{color:var(--accent)}a:focus-visible{outline:3px solid var(--gold);outline-offset:3px}")

def page(setup, cfg, title, desc, body, url, service=None, area=None):
    ld = "\n".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in jsonld(setup, cfg, url, service, area))
    wa = html.escape(f"https://wa.me/{cfg['whatsapp']}?text=" + urllib.parse.quote(("Hi, I'd like to book " + (service or "")).strip()))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="/favicon.svg" type="image/svg+xml">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}"><link rel="canonical" href="{url}">
<meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(desc)}"><meta property="og:type" content="website">
{FONTS}<style>{CSS}</style>{ld}</head><body><main>{body}</main><a class="wa" href="{wa}">Book on WhatsApp</a></body></html>"""

def favicon(cfg):
    """A small letter mark: turmeric on hero indigo (5.4:1 contrast), the Kalamkari pair."""
    letter = html.escape((cfg.get("business") or "B").strip()[:1].upper())
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#1c2463"/>'
            f'<text x="32" y="44" font-family="system-ui,sans-serif" font-size="36" font-weight="700" fill="#d3940a" text-anchor="middle">{letter}</text></svg>')

def services_table(cfg):
    return "<table>" + "".join(f"<tr><td>{html.escape(c['name'])}</td><td>{html.escape(c['price'])}</td></tr>" for c in cfg["catalog"]) + "</table>"

def build(setup, cfg, out):
    # A real client site needs its real address: canonical tags, sitemap and robots.txt would otherwise send
    # Google to example.netlify.app (REA audit, 16 Oct 2026). Drafts/tests pass draft=True.
    if cfg["site_url"].rstrip("/") == PLACEHOLDER_URL and not cfg.get("draft"):
        raise ValueError("site_url is missing: add the client's real site address to client.json (or use --draft for a preview)")
    site = out / "site"; site.mkdir(parents=True, exist_ok=True)
    urls, kw = [], []
    nap = f"<p class='muted'>{html.escape(cfg['address'])} · {html.escape(cfg['phone'])}<br>{html.escape(cfg['hours'])}</p>"
    faqs = "".join(f"<h3>{html.escape(f['k'][0].capitalize())}?</h3><p>{html.escape(clean(f['a'], cfg))}</p>" for f in cfg["faqs"])
    body = f"<h1>{html.escape(cfg['business'])}</h1>{nap}<p>{html.escape(clean(cfg['greeting'], cfg))}</p><h2>{html.escape(cfg['catalogTitle'])}</h2>{services_table(cfg)}<h2>Areas we serve</h2><p>{', '.join(html.escape(a) for a in cfg['areas'])}</p><h2>Questions</h2>{faqs}"
    (site / "index.html").write_text(page(setup, cfg, f"{cfg['business']} — {cfg['catalogTitle']}, Hyderabad", f"{cfg['business']} in Hyderabad. Prices, timings and instant WhatsApp booking.", body, cfg["site_url"] + "/"))
    urls.append(cfg["site_url"] + "/")
    for c in cfg["catalog"]:
        for a in cfg["areas"]:
            name = f"{slug(c['name'])}-in-{slug(a)}.html"; url = f"{cfg['site_url']}/{name}"
            title = f"{c['name']} in {a} — {cfg['business']}"
            b = (f"<p class='muted'><a href='/'>{html.escape(cfg['business'])}</a></p><h1>{html.escape(c['name'])} near {html.escape(a)}</h1>"
                 f"<p><strong>{html.escape(c['price'])}</strong> at {html.escape(cfg['business'])}, {html.escape(cfg['address'])}. "
                 f"Serving customers from {html.escape(a)} and nearby. Book on WhatsApp in under a minute; we confirm instantly and remind you before your visit.</p>"
                 f"{nap}<h2>All {html.escape(cfg['catalogTitle'].lower())}</h2>{services_table(cfg)}")
            (site / name).write_text(page(setup, cfg, title, f"{c['name']} near {a}: {c['price']}. Instant WhatsApp booking at {cfg['business']}.", b, url, c["name"], a))
            urls.append(url); kw.append((c["name"], a, f"{c['name'].lower()} in {a.lower()}", f"{c['name'].lower()} near me", name))
    today = dt.date.today().isoformat()
    (site / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{u}</loc><lastmod>{today}</lastmod></url>" for u in urls) + "</urlset>")
    (site / "favicon.svg").write_text(favicon(cfg))  # stops the /favicon 404 that Lighthouse logged as a console error
    (site / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {cfg['site_url']}/sitemap.xml\n")
    (site / "llms.txt").write_text(f"# {cfg['business']}\n\n> {cfg['address']}. {cfg['hours']}. Phone/WhatsApp {cfg['phone']}.\n\n## {cfg['catalogTitle']}\n" + "\n".join(f"- {c['name']}: {c['price']}" for c in cfg["catalog"]) + "\n")
    with open(out / "keywords.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(["service", "area", "primary phrase", "secondary phrase", "page"]); w.writerows(kw)
    # 12 weeks of Google Business Profile posts
    start = dt.date.today()
    with open(out / "gbp_posts.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(["week of", "post type", "text", "button", "photo idea"])
        for i in range(12):
            d = start + dt.timedelta(weeks=i); c = cfg["catalog"][i % len(cfg["catalog"])]
            fest = next((n for day, n in FESTIVALS if 0 <= (dt.date.fromisoformat(day) - d).days < 7), None)
            if fest: w.writerow([d, "Event", f"{fest} at {cfg['business']}! Book your slot early on WhatsApp — festive weeks fill fast.", "Book", "Team photo with festive decor"])
            elif i % 3 == 0: w.writerow([d, "Offer", f"This week: {c['name']} at {c['price']}. Message us on WhatsApp to book in 30 seconds.", "Book", f"Real photo of {c['name']}"])
            elif i % 3 == 1: w.writerow([d, "Update", f"Tip from our team: {clean(cfg['faqs'][i % len(cfg['faqs'])]['a'], cfg)[:220]}", "Learn more", "Behind-the-scenes photo"])
            else: w.writerow([d, "Update", f"Thank you, {cfg['areas'][i % len(cfg['areas'])]}! New customers from your area get a warm welcome at {cfg['business']}.", "Call", "Happy customer (with consent)"])
    with open(out / "citations.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(["site", "link", "why", "status", "NAP to paste exactly"])
        for name, link, why in CITATIONS["common"] + CITATIONS.get(setup, []):
            w.writerow([name, link, why, "todo", f"{cfg['business']} | {cfg['address']} | {cfg['phone']}"])
    (out / "review_replies.md").write_text(f"""# Review replies for {cfg['business']}
Reply to every review within 24 hours (Google ranks active profiles higher). Use the customer's first name and one specific detail.

**5 stars:** Thank you so much, {{name}}! So glad you loved your {{service}}. See you again soon at {cfg['business']} 💛
**4 stars:** Thanks a lot, {{name}}! We're happy you enjoyed it. Anything we could do to make it 5 stars next time? Just WhatsApp us on {cfg['phone']}.
**3 stars:** Thank you for the honest feedback, {{name}}. We'd love to do better. Could you WhatsApp us on {cfg['phone']} so we can make it right?
**1–2 stars:** We're sorry, {{name}}. This isn't the experience we want for anyone. Please WhatsApp us on {cfg['phone']}; the owner will personally look into it.

Never offer discounts in exchange for reviews, and never post reviews on the business's behalf: both break Google's policies and Indian consumer rules on fake reviews.
""")
    return urls

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--setup", required=True, choices=list(SCHEMA_TYPE)); ap.add_argument("--config", help="client JSON overrides"); ap.add_argument("--out", required=True)
    ap.add_argument("--draft", action="store_true", help="preview without a real site_url (placeholder links)")
    a = ap.parse_args()
    cfg = load(a.setup, json.loads(pathlib.Path(a.config).read_text()) if a.config else {})
    cfg["draft"] = cfg.get("draft") or a.draft
    urls = build(a.setup, cfg, pathlib.Path(a.out))
    print(f"{len(urls)} pages + sitemap, 12 GBP posts, citations and review replies → {a.out}")

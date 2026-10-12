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
import argparse, csv, datetime as dt, html, json, pathlib, re

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

def load(setup, overrides):
    cfg = json.loads((ROOT / "setups" / setup / "bot.config.json").read_text())
    cfg.update(overrides)
    cfg.setdefault("areas", ["Jubilee Hills", "Banjara Hills", "Madhapur", "Kukatpally", "Gachibowli"])
    cfg.setdefault("site_url", "https://example.netlify.app")
    cfg.setdefault("whatsapp", re.sub(r"\D", "", cfg.get("phone", "")))
    return cfg

def price_number(p):
    m = re.search(r"[\d,]+", p.replace("L", "")); return m.group(0).replace(",", "") if m else None

def jsonld(setup, cfg, page_url, service=None, area=None):
    biz = {"@context": "https://schema.org", "@type": SCHEMA_TYPE[setup], "name": cfg["business"], "url": cfg["site_url"],
           "telephone": cfg["phone"], "address": {"@type": "PostalAddress", "streetAddress": cfg["address"], "addressLocality": "Hyderabad",
           "addressRegion": "Telangana", "addressCountry": "IN"}, "openingHours": cfg["hours"], "areaServed": cfg["areas"],
           "hasOfferCatalog": {"@type": "OfferCatalog", "name": cfg["catalogTitle"], "itemListElement": [
               {"@type": "Offer", "itemOffered": {"@type": "Service", "name": c["name"]}, "priceCurrency": "INR",
                **({"price": price_number(c["price"])} if price_number(c["price"]) and "from" not in c["price"] else {}),
                "description": c["price"]} for c in cfg["catalog"]]}}
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": "What are your timings?", "acceptedAnswer": {"@type": "Answer", "text": cfg["hours"]}},
        {"@type": "Question", "name": f"How do I book at {cfg['business']}?", "acceptedAnswer": {"@type": "Answer", "text": f"Message us on WhatsApp at {cfg['phone']}; booking takes under a minute, any time of day."}},
    ] + [{"@type": "Question", "name": f"Do you offer {f['k'][0]}?", "acceptedAnswer": {"@type": "Answer", "text": clean(f["a"], cfg)}} for f in cfg["faqs"][:4]]}
    return [biz, faq]

CSS = """:root{--ink:#1d1d1f;--muted:#5f6368;--accent:#0e7c66;--bg:#fafaf7}*{box-sizing:border-box}body{margin:0;font:16px/1.6 system-ui,-apple-system,'Segoe UI',sans-serif;color:var(--ink);background:var(--bg)}main{max-width:760px;margin:0 auto;padding:24px 16px 80px}h1{font-size:clamp(28px,6vw,40px);line-height:1.15;margin:8px 0}h2{margin-top:32px}.muted{color:var(--muted)}table{width:100%;border-collapse:collapse}td{padding:8px 0;border-bottom:1px solid #e5e5e5}td:last-child{text-align:right;font-weight:600}.wa{position:fixed;left:16px;right:16px;bottom:16px;max-width:728px;margin:0 auto;display:block;text-align:center;background:#25d366;color:#fff;font-weight:700;padding:14px;border-radius:12px;text-decoration:none}a{color:var(--accent)}"""

def page(setup, cfg, title, desc, body, url, service=None, area=None):
    ld = "\n".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in jsonld(setup, cfg, url, service, area))
    wa = f"https://wa.me/{cfg['whatsapp']}?text=" + html.escape(("Hi, I'd like to book " + (service or "")).strip().replace(" ", "%20"))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}"><link rel="canonical" href="{url}">
<meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(desc)}"><meta property="og:type" content="website">
<style>{CSS}</style>{ld}</head><body><main>{body}</main><a class="wa" href="{wa}">Book on WhatsApp</a></body></html>"""

def services_table(cfg):
    return "<table>" + "".join(f"<tr><td>{html.escape(c['name'])}</td><td>{html.escape(c['price'])}</td></tr>" for c in cfg["catalog"]) + "</table>"

def build(setup, cfg, out):
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
    a = ap.parse_args()
    cfg = load(a.setup, json.loads(pathlib.Path(a.config).read_text()) if a.config else {})
    urls = build(a.setup, cfg, pathlib.Path(a.out))
    print(f"{len(urls)} pages + sitemap, 12 GBP posts, citations and review replies → {a.out}")

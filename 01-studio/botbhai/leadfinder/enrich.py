#!/usr/bin/env python3
"""
Lead enrichment — visits each prospect's own public website (only if robots.txt allows) and finds:
  business email · WhatsApp link · Instagram / Facebook pages · online booking already present?
Then re-scores the lead: a business with a website but NO WhatsApp booking is BotBhai's best prospect.

Sources we use, and why (all free and allowed):
  1. OpenStreetMap (leadfinder.py)  — open data, ODbL licence.
  2. The business's own website     — public business contact details, robots.txt respected, 1 request/sec.
  3. Google Places API (optional)   — only with your own API key; Google's free monthly caps per SKU apply.
Sources we do NOT scrape: Google Maps pages, Justdial, Instagram, Facebook, IndiaMART — their terms forbid it,
and accounts/IPs get banned. Consumers' personal numbers are never collected: BotBhai contacts businesses only,
and a client's customers come in through ads, SEO, Google Business Profile and referrals (opt-in).

Usage: python enrich.py leads.csv --out leads-enriched.csv [--max 300]
"""
import argparse, csv, re, sys, time, urllib.parse, urllib.request, urllib.robotparser

UA = "KalpaLabs-BotBhai-Enricher/1.0 (+https://github.com/Akhilkanigicharla)"
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
BOOKING = re.compile(r"fresha|booksy|setmore|calendly|zenoti|book (now|online|an appointment)|schedule (a|your) (visit|appointment)", re.I)
SKIP_EMAIL = re.compile(r"\.(png|jpg|jpeg|gif|webp|svg)$|example\.|sentry|wixpress|domain\.com", re.I)

def allowed(url, cache):
    p = urllib.parse.urlparse(url); base = f"{p.scheme}://{p.netloc}"
    if base not in cache:
        rp = urllib.robotparser.RobotFileParser(); rp.set_url(base + "/robots.txt")
        try: rp.read()
        except Exception: rp = None  # unreachable robots.txt → treat as allowed (standard behaviour)
        cache[base] = rp
    return cache[base] is None or cache[base].can_fetch(UA, url)

def fetch(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        if "html" not in r.headers.get("Content-Type", "html"): return ""
        return r.read(600_000).decode("utf-8", "ignore")

def extract(html):
    emails = sorted({e for e in EMAIL.findall(html) if not SKIP_EMAIL.search(e)})
    wa = re.findall(r"(?:wa\.me/|api\.whatsapp\.com/send\?phone=)(\d{10,13})", html)
    ig = re.findall(r"instagram\.com/([A-Za-z0-9_.]{2,30})", html)
    fb = re.findall(r"facebook\.com/([A-Za-z0-9.\-]{2,60})", html)
    ig = [h for h in ig if h not in ("p", "explore", "accounts", "reel")]
    return {"email": emails[0] if emails else "", "whatsapp_link": wa[0] if wa else "",
            "instagram": ig[0] if ig else "", "facebook": fb[0] if fb and fb[0] not in ("sharer", "tr", "plugins") else "",
            "online_booking": "yes" if BOOKING.search(html) else "no"}

def rescore(row):
    s = int(row.get("score") or 0)
    if row.get("website") and row.get("online_booking") == "no": s += 10   # has a site, no booking → easy upgrade pitch
    if row.get("website") and not row.get("whatsapp_link"): s += 5         # no WhatsApp button
    if row.get("email"): s += 5
    if row.get("instagram"): s += 5                                         # active on social → cares about marketing
    if row.get("online_booking") == "yes": s -= 15                         # already has a booking tool
    return max(0, min(100, s))

def enrich(rows, max_sites=300, delay=1.0, fetcher=fetch):
    cache, done = {}, 0
    for r in rows:
        for k in ("email", "whatsapp_link", "instagram", "facebook", "online_booking"): r.setdefault(k, r.get(k, ""))
        url = r.get("website", "").strip()
        if url and done < max_sites:
            if not url.startswith("http"): url = "http://" + url
            try:
                if allowed(url, cache):
                    info = extract(fetcher(url))
                    for k, v in info.items():
                        if v and not r.get(k): r[k] = v
                    r["enriched"] = "yes"
                else: r["enriched"] = "blocked by robots.txt"
            except Exception as e: r["enriched"] = f"error: {type(e).__name__}"
            done += 1; time.sleep(delay)
        r["score"] = rescore(r)
    rows.sort(key=lambda r: -int(r["score"]))
    return rows

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("csv"); ap.add_argument("--out", required=True); ap.add_argument("--max", type=int, default=300)
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.csv, encoding="utf-8-sig")))
    rows = enrich(rows, a.max)
    cols = list(rows[0].keys()) if rows else []
    with open(a.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print(f"enriched {sum(1 for r in rows if r.get('enriched') == 'yes')} sites; {sum(1 for r in rows if r.get('email'))} emails; → {a.out}", file=sys.stderr)

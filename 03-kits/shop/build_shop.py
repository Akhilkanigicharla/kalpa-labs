"""Kit shop pages (A212): one sales page per exam kit + a home page, built from the engine's exam files.

The pitch is what the mock-test subscriptions do not sell: one payment, no expiry; a planner, a tracker and exam-date
alerts; Telugu for Telangana exams; free mock tests elsewhere linked as a companion; a free mini-kit for a Telegram follow.
Static HTML, no JavaScript, strict CSP. Nothing goes online until Akhil says "go" (CLAUDE.md rule 9).

    python3 03-kits/shop/build_shop.py            # writes 03-kits/shop/dist/
"""
import base64, hashlib, importlib.util, json, pathlib, shutil, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DIST = HERE / "dist"
_spec = importlib.util.spec_from_file_location("kit_engine", HERE.parent / "engine" / "kit_engine.py")
E = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(E)
_h = E._h
CFG = json.loads((HERE / "shop.json").read_text(encoding="utf-8"))
UDYAM = "UDYAM-TS-02-0382711"

TE = {  # Telugu lines (draft from K090, free-model output; a Telugu speaker reads them before go: CEO task)
    "once": "ఒకే చెల్లింపు, గడువు ముగింపు లేదు.",
    "plan": "స్టడీ ప్లానర్: రోజుకు ఏ టాపిక్ చదవాలో, ఎప్పుడు రివిజన్ చేయాలో.",
    "track": "రోజువారీ ట్రాకర్: సిలబస్‌లో ఎంత పూర్తయిందో ఫోన్‌లోనే చూడండి.",
    "alert": "పరీక్ష తేదీ హెచ్చరికలు: అధికారిక తేదీ రాగానే మీకు తెలుస్తుంది.",
    "mock": "ఉచిత మాక్ టెస్ట్‌లతో ప్రాక్టీస్ చేయండి; మేము మాక్ టెస్ట్‌లు అమ్మము.",
    "mini": "టెలిగ్రామ్ ఛానెల్‌లో చేరండి, ఉచిత మినీ-కిట్ పొందండి.",
}

CSS = """
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 var(--f-body);overflow-wrap:anywhere}
a{color:var(--accent)}
.wrap{max-width:720px;margin:0 auto;padding:0 16px 40px}
.hero{background:var(--hero);color:var(--hero-fg);padding:22px 0 18px}
.hero .wrap{padding-bottom:0}
.hero h1{font:400 30px/1.12 var(--f-display);margin:0 0 8px}
.hero p{margin:4px 0;color:var(--hero-mute)}
.hero a{color:var(--hero-fg)}
.vine{height:10px;background:var(--vine)}
.crumb{font-size:14px;margin:12px 0 0}
.once{display:inline-block;background:var(--accent);color:var(--accent-fg);font-weight:700;border-radius:var(--r-s);padding:4px 10px;margin:8px 0}
h2{font:400 22px/1.2 var(--f-display);margin:28px 0 8px}
h3{font-size:17px;margin:0 0 4px}
.te{font-family:"Anek Telugu",var(--f-body);color:var(--muted);display:block;font-size:15px}
.card{background:var(--panel);border:1px solid var(--rule);border-radius:var(--r-m);padding:14px;margin:10px 0;box-shadow:var(--shadow)}
.grid{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}
.price{font:600 28px/1.1 var(--f-mono);color:var(--l3)}
.btn{display:flex;align-items:center;justify-content:center;min-height:48px;padding:10px 16px;border-radius:var(--r-s);background:var(--accent);color:var(--accent-fg);font-weight:700;text-decoration:none;margin-top:10px}
.btn.alt{background:var(--panel);color:var(--accent);border:1px solid var(--accent)}
.soon{display:block;margin-top:10px;padding:10px;border:1px dashed var(--rule);border-radius:var(--r-s);font-size:14px;color:var(--muted)}
ul.ticks{padding-left:20px}ul.ticks li{margin:8px 0}
table{width:100%;border-collapse:collapse;font-size:14px}
td{border-top:1px solid var(--rule);padding:8px;vertical-align:top}
.badge{display:inline-block;font:600 11px/1 var(--f-mono);padding:4px 6px;border-radius:var(--r-s);border:1px solid currentColor}
.CONFIRMED{color:var(--ok)}.EXPECTED{color:var(--warn)}.NOT_ANNOUNCED{color:var(--madder)}
.note{font-size:13px;color:var(--muted)}
footer{border-top:1px solid var(--rule);margin-top:32px;padding-top:12px}
"""


def exams():
    out = []
    for f in E.exam_files():
        d = E.load(f)
        errs = E.validate(d)
        if errs:
            raise ValueError(f"{f.name}: {'; '.join(errs)}")
        out.append(d)
    # Telangana (Telugu) kits first: the shop is narrow on purpose (competitors-2026-11-11.md, tweak 2)
    return sorted(out, key=lambda d: ("te" not in d["languages"], d["short"]))


def rupees(n):
    return f"₹{n}"


def pay(kind, label):
    url = CFG["pay_url"].get(kind, "")
    if url:
        return f'<a class="btn" href="{_h(url)}" rel="noopener">{_h(label)}</a>'
    return '<span class="soon">Payment page opens soon. Join the Telegram channel below to hear first.</span>'


def mini(te):
    url = CFG["telegram_url"]
    line = f'<span class="te" lang="te">{TE["mini"]}</span>' if te else ""
    act = (f'<a class="btn alt" href="{_h(url)}" rel="noopener">Join Telegram, get the free mini-kit</a>' if url else
           '<span class="soon">Telegram channel opens soon. The mini-kit is free: no payment, no sign-up form.</span>')
    return (f'<h2 id="free">Free mini-kit for a Telegram follow</h2><div class="card"><p>Follow the Kalpa exam channel and get the '
            f'free mini-kit: the full syllabus checklist and a countdown to the official date. One message a day at most, '
            f'leave any time.{line}</p>{act}</div>')


def page(path, title, desc, body, ld, base):
    url = base + "/" + path.removesuffix("index.html")
    style = "\n" + E.TOKENS.read_text(encoding="utf-8") + CSS
    sha = "'sha256-" + base64.b64encode(hashlib.sha256(style.encode("utf-8")).digest()).decode() + "'"
    csp = (f"default-src 'none'; style-src {sha}; img-src 'self'; base-uri 'none'; form-action 'none'; object-src 'none'")
    ldj = json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_h(title)}</title><meta name="description" content="{_h(desc)}">
<meta http-equiv="Content-Security-Policy" content="{csp}"><meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="color-scheme" content="light dark"><link rel="canonical" href="{url}">
<meta property="og:title" content="{_h(title)}"><meta property="og:description" content="{_h(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{base}/og.png"><meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{ldj}</script>
<style>{style}</style></head><body>
{body}
<footer class="wrap"><p class="note">Kalpa Labs, Hyderabad · Udyam {UDYAM}. Not an official product of any exam body; dates come only from official sites.
No pass or rank promises. Works-or-refund within 7 days: if the copy fails or a formula is wrong, we fix it within 48 h or refund in full.</p></footer>
</body></html>
"""


def offer(d, base, kind="kit"):
    return {"@type": "Offer", "price": str(CFG["prices"][kind]), "priceCurrency": "INR", "url": f"{base}/{d['id']}/",
            "availability": "https://schema.org/PreOrder"}


def kit_page(d, base):
    te = "te" in d["languages"]
    n, ex = len(E.topics(d)), E.exam_date(d)
    p = CFG["prices"]
    conf = sum(k["status"] == "CONFIRMED" for k in d["key_dates"])
    mock = CFG["mocks"].get(d["id"])
    t = lambda k: f'<span class="te" lang="te">{TE[k]}</span>' if te else ""
    rows = "".join(
        f'<tr><td>{_h(k["event"])}{(f"<span class=te lang=te>{_h(k["event_te"])}</span>") if te and k.get("event_te") else ""}</td>'
        f'<td>{_h(k["date"]) if k.get("date") else "—"}<br><span class="badge {k["status"]}">{k["status"].replace("_", " ")}</span></td></tr>'
        for k in d["key_dates"])
    mock_html = (f'<a class="btn alt" href="{_h(mock["url"])}" rel="noopener" target="_blank">{_h(mock["title"])}</a>' if mock else "")
    body = f"""<header class="hero"><div class="wrap"><p class="crumb"><a href="/">All Kalpa exam kits</a></p>
<h1>{_h(d['short'])} exam kit</h1><p>{_h(d['name'])}{(' · <span lang=te>' + _h(d['name_te']) + '</span>') if te and d.get('name_te') else ''}</p>
<p class="once">One payment, no expiry</p>{t('once')}</div></header><div class="vine" aria-hidden="true"></div>
<main class="wrap">
<p>Mock-test passes stop working when they expire. This kit is yours for good: a plan, a tracker and date alerts for {_h(d['short'])}, built from the official syllabus ({n} topics).</p>
<h2>What you get</h2><ul class="ticks">
<li><b>Study planner:</b> a daily plan of {d['plan']['topics_per_day']} topics, with revisions on days {', '.join(map(str, d['plan']['revision_days']))}, in your phone calendar.{t('plan')}</li>
<li><b>Tracker:</b> a Google Sheet copy plus a phone page; tick topics and see % done per subject.{t('track')}</li>
<li><b>Exam-date alerts:</b> alerts 7 days and 1 day before every official date ({f'{conf} confirmed today; ' if conf else 'no official date is out yet; '}we add each one the day {_h(d['body'])} announces it).{t('alert')}</li>
</ul>
<h2 id="buy">Price</h2><div class="grid">
<div class="card"><h3>This kit</h3><p class="price">{rupees(p['kit'])}</p><p class="note">One payment, no expiry. No subscription.</p>{pay('kit', f"Buy the {d['short']} kit")}</div>
<div class="card"><h3>All kits bundle</h3><p class="price">{rupees(p['bundle'])}</p><p class="note">Every kit in the shop, one payment.</p>{pay('bundle', 'Buy the bundle')}</div>
</div>
<h2>Mock tests: use the free ones</h2><div class="card"><p>We do not sell mock tests. Take free mocks wherever you like and log your scores in the kit's mock sheet.{t('mock')}</p>
{mock_html}<a class="btn alt" href="{_h(d['official_site'])}" rel="noopener" target="_blank">Previous papers: official site</a>
<p class="note">Syllabus PDF and previous papers come from {_h(d['body'])}. Kalpa is not linked to any mock-test company.</p></div>
{mini(te)}
<h2>Official dates in the kit</h2><div class="card"><table>{rows}</table></div>
<p class="note">Dates checked {_h(d['checked_on'])}. Only CONFIRMED dates come from the official site; the rest are shown as not announced until they are.</p>
<h2>For coaching institutes</h2><div class="card"><p>{rupees(p['institute'])} a copy, at least {p['institute_min']} copies, each with the student's name.</p>{pay('institute', 'Order for an institute')}</div>
</main>"""
    title = f"{d['short']} exam kit: one payment, no expiry"
    if len(title) > 60:
        title = f"{d['short']} kit: one payment, no expiry"
    desc = f"{d['short']} planner, tracker and exam-date alerts{' in Telugu and English' if te else ''}. {rupees(p['kit'])} once, no expiry. Free mock tests linked as a companion."
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Product", "name": f"{d['short']} exam kit", "description": desc, "brand": {"@type": "Brand", "name": "Kalpa Labs"},
         "image": f"{base}/og.png", "offers": offer(d, base)},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Kalpa exam kits", "item": base + "/"},
            {"@type": "ListItem", "position": 2, "name": d["short"], "item": f"{base}/{d['id']}/"}]}]}
    return title, desc, body, ld


def home_page(ds, base):
    p = CFG["prices"]
    cards = "".join(
        f'<div class="card"><h3>{_h(d["short"])}</h3><p class="note">{len(E.topics(d))} topics{" · Telugu + English" if "te" in d["languages"] else ""}</p>'
        f'<a class="btn alt" href="/{d["id"]}/">See the {_h(d["short"])} kit</a></div>' for d in ds)
    body = f"""<header class="hero"><div class="wrap"><h1>Kalpa exam kits</h1>
<p>Planner, tracker and exam-date alerts for Telangana and central government exams, Telugu first.</p>
<p class="once">One payment, no expiry</p><span class="te" lang="te">{TE['once']}</span></div></header><div class="vine" aria-hidden="true"></div>
<main class="wrap">
<p>Mock-test apps sell tests by the month. We sell the plan: what to study each day, what to revise, and a nudge when the official date is out. Pair it with any free mock test.</p>
<h2>Kits</h2><div class="grid">{cards}</div>
<h2 id="buy">Prices</h2><div class="grid">
<div class="card"><h3>One kit</h3><p class="price">{rupees(p['kit'])}</p><p class="note">One payment, no expiry.</p></div>
<div class="card"><h3>All kits bundle</h3><p class="price">{rupees(p['bundle'])}</p>{pay('bundle', 'Buy the bundle')}</div>
<div class="card"><h3>Institutes</h3><p class="price">{rupees(p['institute'])}</p><p class="note">a copy, at least {p['institute_min']} copies.</p>{pay('institute', 'Order for an institute')}</div>
</div>
{mini(True)}
</main>"""
    title = "Kalpa exam kits: one payment, no expiry"
    desc = f"Exam planners, trackers and date alerts for TGPSC, SSC, RRB and GATE, Telugu first. {rupees(p['kit'])} a kit, {rupees(p['bundle'])} for all, no expiry."
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Organization", "name": "Kalpa Labs", "url": base + "/", "logo": f"{base}/og.png"},
        {"@type": "WebSite", "name": "Kalpa exam kits", "url": base + "/"},
        {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{base}/{d['id']}/", "name": d["short"]}
                                                  for i, d in enumerate(ds)]}]}
    return title, desc, body, ld


NOT_FOUND = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Page not found · Kalpa exam kits</title></head>
<body style="font:16px/1.5 system-ui,sans-serif;max-width:600px;margin:40px auto;padding:0 16px">
<h1>Page not found</h1><p><a href="/" style="display:inline-block;min-height:44px;line-height:44px">See all Kalpa exam kits</a></p></body></html>
"""


def build(out=DIST, base=None):
    base = (base or CFG["base"]).rstrip("/")
    out = pathlib.Path(out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    ds = exams()
    pages = {"index.html": home_page(ds, base)} | {f"{d['id']}/index.html": kit_page(d, base) for d in ds}
    for path, (title, desc, body, ld) in pages.items():
        f = out / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(page(path, title, desc, body, ld, base), encoding="utf-8")
    (out / "404.html").write_text(NOT_FOUND, encoding="utf-8")
    shutil.copy(ROOT / "00-hq" / "site" / "og.png", out / "og.png")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n", encoding="utf-8")
    locs = "".join(f"<url><loc>{base}/{p.removesuffix('index.html')}</loc></url>" for p in pages)
    (out / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{locs}</urlset>\n', encoding="utf-8")
    (out / "llms.txt").write_text("# Kalpa exam kits\n\nOne-payment, no-expiry exam planners, trackers and date alerts by Kalpa Labs (Hyderabad).\n\n"
                                  + "".join(f"- [{d['short']} kit]({base}/{d['id']}/)\n" for d in ds), encoding="utf-8")
    (out / "_headers").write_text("/*\n  X-Frame-Options: DENY\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n"
                                  "  Permissions-Policy: camera=(), microphone=(), geolocation=()\n  Strict-Transport-Security: max-age=31536000\n", encoding="utf-8")
    return out, list(pages)


if __name__ == "__main__":
    o, ps = build(base=sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"built {len(ps)} pages in {o}")

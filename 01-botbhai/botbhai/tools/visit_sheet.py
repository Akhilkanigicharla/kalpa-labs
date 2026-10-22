#!/usr/bin/env python3
"""
A08 / P1-W1-06: a walk-in visit sheet for one salon cluster, made from a lead file (leadfinder.py --near …).

  python3 tools/visit_sheet.py <leads.csv> --start 17.4375,78.4482 --start-name "Ameerpet Metro" \
      --cluster "Cluster 1 · SR Nagar / Ameerpet" --stops 8 --out ../docs/sales/visit-cluster1.html

Picks independent salons (chains are not our customer) within the radius, prefers the ones BotBhai helps most
(no website, open late, ladies/bridal), then walks them in the truly shortest order (every order is tried; ≤ 9 stops).
Each stop gets Google Maps walking directions from the previous stop (one link per leg, because phone browsers
allow only 3 waypoints) and a pitch written for that salon. **No phone numbers are printed**: walk-ins only, no cold
calls (PLAN.md), and lead files stay out of git (DPDP). Data © OpenStreetMap contributors, ODbL.
"""
import argparse, csv, html as H, itertools, math, pathlib, re, sys
from urllib.parse import urlencode

CHAINS = re.compile(r"\b(naturals|green trends|lakm[eé]|toni\s*&?\s*guy|jawed habib|ylg|bounce|enrich|looks|b blunt|geetanjali|limelite|tress lounge|bodycraft|kaya|vlcc|o2 spa|page 3)\b", re.I)
WALK_M_PER_MIN = 75      # relaxed walking speed with a bag of cards
DETOUR = 1.3             # streets are not straight lines; typical urban detour factor


def load(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                r["lat"], r["lon"] = float(r["lat"]), float(r["lon"])
            except (TypeError, ValueError):
                continue
            if r.get("niche", "salon") == "salon":
                rows.append(r)
    return rows


def dist_m(a, b):
    """Great-circle distance in metres (haversine)."""
    R = 6371000.0
    (la1, lo1), (la2, lo2) = [(math.radians(x), math.radians(y)) for x, y in (a, b)]
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def closing_time(hours):
    ends = [b for a, b in re.findall(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", hours or "")]
    return max(ends) if ends else ""


def ampm(hhmm):
    h, m = map(int, hhmm.split(":")); return f"{(h - 1) % 12 + 1}:{m:02d} {'PM' if h >= 12 else 'AM'}"


def is_ladies(r):
    return (r.get("kind") or "").lower() in ("female", "ladies", "women", "beauty") or r.get("category") == "beauty" or re.search(r"ladies|beauty|bridal|parlou?r", r.get("name", ""), re.I)


def prospect_score(r):
    s = 0
    if not r.get("website"): s += 3            # we add a free mini-site
    close = closing_time(r.get("opening_hours"))
    if close and (close >= "21:00"): s += 3     # late WhatsApps
    if is_ladies(r): s += 2                     # bridal season (Nov–Feb)
    if (r.get("kind") or "").lower() == "unisex": s += 1
    if r.get("address"): s += 1                 # easier to find
    return s


def pick(leads, start, radius_km=1.2, stops=8):
    cand = [r for r in leads if r.get("name") and not CHAINS.search(r["name"]) and r.get("category") != "cosmetics"  # retail, no appointments
            and dist_m(start, (r["lat"], r["lon"])) <= radius_km * 1000]
    cand.sort(key=lambda r: (-prospect_score(r), dist_m(start, (r["lat"], r["lon"]))))
    chosen, reserve = cand[:stops], cand[stops:stops + 4]
    if len(chosen) > 9: raise SystemExit("at most 9 stops (every order is tried)")
    best = min(itertools.permutations(chosen), key=lambda p: sum(dist_m(a, b) for a, b in zip([start] + [(r["lat"], r["lon"]) for r in p], [(r["lat"], r["lon"]) for r in p])), default=())
    return list(best), reserve


def pitch(r):
    close = closing_time(r.get("opening_hours")); kind = (r.get("kind") or "").lower()
    en, te = [], []
    if close and close >= "21:00":
        en.append(f"You're open till {ampm(close)}: who answers WhatsApp after that? BotBhai does, in Telugu, and books the slot.")
        te.append(f"మీరు {ampm(close)} వరకు తెరిచి ఉంటారు; ఆ తర్వాత వచ్చే WhatsApp లకు BotBhai తెలుగులో జవాబిచ్చి బుక్ చేస్తుంది.")
    if is_ladies(r):
        en.append("Bridal season (Nov–Feb): bridal enquiries reach you with the date, events and budget, so none slip away.")
        te.append("పెళ్లిళ్ల సీజన్‌లో బ్రైడల్ ఎంక్వైరీలు తేదీ, బడ్జెట్‌తో సహా మీకే వస్తాయి.")
    elif kind in ("unisex", "barber", "male"):
        en.append("Saturday rush: customers book their own haircut slot, and two reminders cut no-shows.")
        te.append("శనివారం రద్దీలో కస్టమర్లే స్లాట్ బుక్ చేసుకుంటారు; రెండు రిమైండర్లతో రాని వాళ్లు తగ్గుతారు.")
    if not r.get("website"):
        en.append("No website listed: the Standard plan includes a free mini-site that books on WhatsApp.")
        te.append("మీకు వెబ్‌సైట్ లేదు: Standard ప్లాన్‌లో WhatsApp బుకింగ్‌తో చిన్న వెబ్‌సైట్ ఉచితం.")
    if not en:
        en.append("Calls during a facial go unanswered: BotBhai answers and books while you work.")
        te.append("ఫేషియల్ చేస్తున్నప్పుడు కాల్స్ మిస్ అవుతాయి; అప్పుడు BotBhai జవాబిచ్చి బుక్ చేస్తుంది.")
    return {"en": " ".join(en[:2]), "te": " ".join(te[:2])}


def render(picked, reserve, start, start_name, cluster="Cluster 1", date="", spotted=0):
    e = lambda s: H.escape(str(s or ""))
    origin = f"{start[0]},{start[1]}"
    legs, prev, total = [], start, 0.0
    for r in picked:
        here = (r["lat"], r["lon"]); m = dist_m(prev, here) * DETOUR; total += m
        link = "https://www.google.com/maps/dir/?" + urlencode({"api": 1, "origin": origin if prev == start else f"{prev[0]},{prev[1]}", "destination": f"{here[0]},{here[1]}", "travelmode": "walking"}, safe=",")
        legs.append((r, round(m / 10) * 10, max(1, round(m / WALK_M_PER_MIN)), link)); prev = here
    stops = "".join(f"""<article class="stop"><div class="num">{i}</div><div class="main">
<h2>{e(r['name'])}<span class="kind">{e(r.get('kind') or r.get('category') or '')}</span></h2>
<p class="meta">{e(r.get('address') or 'Address not listed: use the map link')}{' · open ' + e(r['opening_hours']) if r.get('opening_hours') else ''}</p>
<p class="walk"><a href="{e(link)}">Walk {m} m (~{mins} min) from {'the start' if i == 1 else 'stop ' + str(i - 1)}</a> · <a href="{e(r.get('maps_link') or '')}">OpenStreetMap</a></p>
<p class="pitch"><b>Say:</b> {e(pitch(r)['en'])}</p><p class="pitch te" lang="te">{e(pitch(r)['te'])}</p>
<div class="boxes"><span>☐ visited</span><span>☐ owner there</span><span>☐ demo shown</span><span>☐ card left</span></div>
<div class="answers"><span>After 9 PM / wk: ____</span><span>No-shows last Sat: ____</span><span>Phone in facial: ________</span><span>Follow-up: ____</span></div>
</div></article>""" for i, (r, m, mins, link) in enumerate(legs, 1))
    res = ", ".join(e(r["name"]) for r in reserve) or "none"
    # OpenStreetMap lists few salons in Indian neighbourhoods, so the sheet leaves rows for salons seen on the street
    spots = "".join(f"""<article class="stop spot"><div class="num">+</div><div class="main"><h2>Spotted on the way: ____________________________</h2>
<p class="meta">Street / landmark: ______________________ · ☐ ladies ☐ unisex ☐ gents</p>
<div class="boxes"><span>☐ owner there</span><span>☐ demo shown</span><span>☐ card left</span></div>
<div class="answers"><span>After 9 PM / wk: ____</span><span>No-shows last Sat: ____</span><span>Phone in facial: ________</span><span>Follow-up: ____</span></div>
</div></article>""" for _ in range(spotted))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Visit sheet: {e(cluster)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Rozha+One&family=Anek+Latin:wght@400;600;700&family=Anek+Telugu:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap">
<style>@page{{size:A4;margin:10mm}}
:root{{--fg:#1E2A1F;--muted:#5A6152;--rule:#DCD5C3;--accent:#2F6A3A;--madder:#8A4A28;--gold:#C38E12;--hero:#1D3A25;--hero-fg:#F4EEDC;--hero-mute:#BFCDAE;--l1:#8A4A28;
--f-display:"Rozha One",Georgia,serif;--f-body:"Anek Latin","Anek Telugu",system-ui,sans-serif;--f-te:"Anek Telugu",sans-serif;--f-mono:"JetBrains Mono",ui-monospace,monospace}}
*{{box-sizing:border-box}}html{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}body{{margin:0;color:var(--fg);font:9.6pt/1.4 var(--f-body)}}
header{{position:relative;background:var(--hero);color:var(--hero-fg);padding:12px 16px 12px;border-radius:10px}}
header::after{{content:"";position:absolute;left:0;right:0;bottom:0;height:8px;border-radius:0 0 10px 10px;background:radial-gradient(circle at 7px 4px,var(--gold) 2.2px,transparent 2.6px) 0 0/14px 8px,linear-gradient(135deg,transparent 0 50%,var(--madder) 50%) 0 0/7px 8px;transform:scaleY(-1)}}
.eyebrow{{font:600 7.5pt var(--f-mono);letter-spacing:.1em;text-transform:uppercase;color:var(--gold);margin:0}}
h1{{font:400 19pt/1.15 var(--f-display);margin:2px 0 4px}}header p{{margin:0;color:var(--hero-mute)}}
.plan{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:8px 0}}.plan div{{border:1px solid var(--rule);border-radius:8px;padding:6px 9px}}.plan b{{color:var(--accent)}}
.plan ol,.plan ul{{margin:2px 0 0;padding-left:16px}}
.spot{{border-left-color:var(--gold)}}.spot .num{{color:var(--gold)}}
.stop{{display:flex;gap:9px;border:1px solid var(--rule);border-left:4px solid var(--l1);border-radius:8px;padding:6px 9px;margin-bottom:6px;break-inside:avoid}}
.num{{font:400 20pt/1 var(--f-display);color:var(--l1);min-width:20px}}.main{{flex:1;min-width:0}}
h2{{font:700 11pt var(--f-body);margin:0}}.kind{{font:600 7pt var(--f-mono);text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-left:6px}}
.stop p{{margin:1px 0}}.meta{{color:var(--muted)}}.walk a{{color:var(--accent)}}.te{{font-family:var(--f-te);color:var(--accent)}}
.boxes,.answers{{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:8.6pt;margin-top:2px}}.answers{{color:var(--muted)}}
footer{{font-size:7.5pt;color:var(--muted);margin-top:6px}}</style></head><body>
<header><p class="eyebrow">BotBhai walk-in · {e(cluster)}</p><h1>{len(picked)} mapped salons{f' + {spotted} you spot' if spotted else ''}, about {round(total / 100) / 10} km on foot</h1>
<p>Start: {e(start_name)} · Best time 11:30 AM–1 PM, when salons are quiet · Date: {e(date) or '__________'}</p></header>
<section class="plan"><div><b>At each salon (10–12 min)</b><ol><li>Ask for the owner. If busy, leave the card and ask when to come back.</li>
<li>Ask: How many WhatsApps come in after 9 PM? How many no-shows last Saturday? Who answers the phone during a facial?</li>
<li>Demo on their phone: type "repu haircut kavali" and book.</li><li>Leave the A5 card; write their 3 answers on it.</li></ol></div>
<div><b>Rules</b><ul><li>Walk-in only: no cold calls, no WhatsApp to numbers they didn't give you.</li><li>Never promise a number of bookings; prices only from the card.</li>
<li>At most 3 follow-ups (days 2, 5, 10); stop on "no".</li><li>Two blocks of 4 if time is short. Reserve if one is closed: {res}.</li></ul></div></section>
{stops}{spots}
<footer>Walking distances are straight-line × {DETOUR}, about {WALK_M_PER_MIN} m a minute. Salon data © OpenStreetMap contributors, ODbL (openstreetmap.org/copyright): check it's still open. Made by tools/visit_sheet.py.</footer>
</body></html>"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("leads"); ap.add_argument("--start", default="17.4375,78.4482"); ap.add_argument("--start-name", default="Ameerpet Metro")
    ap.add_argument("--cluster", default="Cluster 1 · SR Nagar / Ameerpet"); ap.add_argument("--radius-km", type=float, default=1.3)
    ap.add_argument("--spotted", type=int, default=0, help="blank rows for salons seen on the street (OSM lists few)")
    ap.add_argument("--stops", type=int, default=8); ap.add_argument("--date", default=""); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    start = tuple(float(x) for x in a.start.split(","))
    picked, reserve = pick(load(a.leads), start, a.radius_km, a.stops)
    spotted = a.spotted or max(0, 6 - len(picked))
    if len(picked) < 6: print(f"note: only {len(picked)} mapped salons in range; adding {spotted} 'spotted on the way' rows", file=sys.stderr)
    pathlib.Path(a.out).write_text(render(picked, reserve, start, a.start_name, a.cluster, a.date, spotted), encoding="utf-8")
    print(f"{len(picked)} stops → {a.out}")


if __name__ == "__main__":
    main()

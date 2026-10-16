#!/usr/bin/env python3
"""A08 visit sheet checks on a synthetic lead file (made-up salons): chains and far-away salons are left out,
the walking order is the true shortest path (checked by brute force here), no phone number is ever printed,
each stop has a walking-directions link and a pitch that fits it, and the sheet prints on 1–2 A4 pages."""
import itertools, math, pathlib, re, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import visit_sheet as V

START = (17.4375, 78.4482)
leads = V.load(ROOT / "tools" / "fixtures" / "leads-ameerpet-sample.csv")
picked, reserve = V.pick(leads, START, radius_km=1.3, stops=6)
names = [r["name"] for r in picked]
assert len(picked) == 6, names
assert not any("Naturals" in n or "Green Trends" in n for n in names + [r["name"] for r in reserve]), "chains are not our customer"
assert "Cosmo Cosmetics Store" not in names + [r["name"] for r in reserve], "cosmetics shops take no appointments"
assert "Far Away Salon Kukatpally" not in names + [r["name"] for r in reserve] and all(r["name"] for r in picked)
print(f"  ✓ picked {len(picked)} independent salons within 1.3 km (+{len(reserve)} reserve); chains, far and unnamed left out")

def length(path):
    pts = [START] + [(r["lat"], r["lon"]) for r in path]
    return sum(V.dist_m(a, b) for a, b in zip(pts, pts[1:]))
best = min(length(p) for p in itertools.permutations(picked))
assert abs(length(picked) - best) < 1e-6, f"order is {length(picked):.0f} m, shortest is {best:.0f} m"
print(f"  ✓ walking order is the shortest of {math.factorial(len(picked))} orders: {length(picked):.0f} m straight-line")

html = V.render(picked, reserve, START, "Ameerpet Metro (Blue/Red line interchange)", cluster="Cluster 1 · SR Nagar / Ameerpet", spotted=3)
assert html.count('class="stop spot"') == 3 and "Spotted on the way" in html, "blank rows for salons seen on the street"
text = re.sub(r"<[^>]+>", " ", html)
assert not re.search(r"\d[\d\s]{8,}\d", text.replace("17.4", "").replace("78.4", "")), "a phone-like number is printed"
assert "98480" not in html and "tel:" not in html, "phone numbers must never be on the sheet"
assert html.count("travelmode=walking") == len(picked) and "origin=17.4375,78.4482" in html
assert "© OpenStreetMap contributors" in html and "ODbL" in html
for q in ["after 9 PM", "no-shows last Saturday", "during a facial"]:
    assert q in html, q
lotus = V.pitch(next(r for r in leads if r["name"].startswith("Lotus")))
assert "bridal" in lotus["en"].lower() and "9:30 PM" in lotus["en"], lotus
assert "website" in V.pitch(next(r for r in leads if r["name"] == "Hair Craft"))["en"].lower()
assert all(V.pitch(r)["te"] for r in picked)
print("  ✓ sheet: no phone numbers, a walking-directions link per stop, the 3 questions, ODbL credit, pitches fit each salon")

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("  (PDF check skipped: needs Playwright)")
else:
    out = ROOT / "web" / "dist" / "sales"; out.mkdir(parents=True, exist_ok=True)
    (out / "visit-sample.html").write_text(html)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto((out / "visit-sample.html").as_uri()); pg.wait_for_load_state("networkidle")
        bad = pg.evaluate("""() => [...document.querySelectorAll('body *')].filter((el) => [...el.childNodes].some((n) => n.nodeType === 3 && /[\\u0C00-\\u0C7F]/.test(n.textContent))
            && /JetBrains|Rozha/.test(getComputedStyle(el).fontFamily.split(',')[0])).length""")
        assert bad == 0, "Telugu in a font without Telugu letters"
        pg.pdf(path=str(out / "visit-sample.pdf"), prefer_css_page_size=True, print_background=True); b.close()
        assert not errs, errs
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.check_output(["pdfinfo", str(out / "visit-sample.pdf")], text=True)).group(1))
    assert 1 <= n <= 2, f"{n} pages"
    print(f"  ✓ prints on {n} A4 page{'s' if n > 1 else ''}")
print("visit sheet tests passed")

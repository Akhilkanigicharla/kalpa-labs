#!/usr/bin/env python3
"""Offline tests for Kalpa Leads (no network, no browser, no AI key). Run: python3 00-hq/leads/test_kalpa_leads.py"""
import csv, json, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); FX = os.path.join(HERE, "fixtures")
sys.path.insert(0, HERE); import kalpa_leads as K

ok = 0
def check(cond, msg):
    global ok
    if not cond: raise SystemExit(f"  ✗ {msg}")
    ok += 1; print(f"  ✓ {msg}")

# 1. every world is configured, with a template and a lawful source
check(sorted(K.WORLD_IDS) == ["b1", "b2", "b3", "b4", "b5", "b6", "b7", "hq"], "all 8 worlds configured (HQ + b1-b7)")
for w in K.WORLD_IDS:
    c = K.WORLDS[w]
    assert c["template"] and c["signals"] and c["looking_for"], w
    for t in c.get("osm", []): assert "google" not in t.lower()
check(K.WORLDS["b7"].get("research_only") is True and "never customers" in K.WORLDS["b7"]["looking_for"].lower(), "Trading Lab finds research sources only (SEBI: no customers)")

# 2. banned sources are never fetched
for u in ["https://maps.google.com/x", "https://www.justdial.com/a", "https://instagram.com/x", "https://m.facebook.com/x", "https://www.linkedin.com/company/x", "https://dir.indiamart.com/x"]:
    assert K.banned(u), u
check(not K.banned("https://glow-salon.test/") and not K.banned("https://googlefiber.example.in"), "Google Maps, Justdial, Instagram, Facebook, LinkedIn, IndiaMART blocked; normal sites allowed")

# 3. OSM source: dedupe, URL normalising, sites first
rows = K.from_osm("b1", "Hyderabad", os.path.join(FX, "osm.json"))
names = [r["name"] for r in rows]
check(names.count("Glow Salon") == 1 and len(rows) == 4, "OSM rows de-duplicated by name")
check(rows[0]["website"].startswith("https://") and "ODbL" in rows[0]["source"], "URLs normalised; ODbL source recorded")
check(K.from_osm("b4", "Hyderabad", os.path.join(FX, "osm.json")) == [], "worlds without OSM tags return nothing from OSM (need a seed list)")

# 4. full offline run for BotBhai: contacts, gaps, banned skip, scoring order
urls = sorted({r["website"] for r in rows if r["website"] and not K.banned(r["website"])})
pages = K.from_html_dir(urls, FX)
out = {r["name"]: r for r in K.run("b1", rows, pages)}
g, b, n, m = out["Glow Salon"], out["Booked Spa"], out["No Site Parlour"], out["Maps Copy"]
check(g["email"] == "hello@glow-salon.test" and g["instagram"] == "glow.salon.hyd" and g["fetched"] == "yes", "contacts read from the business's own site")
check(b["whatsapp_link"] == "919000022222" and b["online_booking"] == "yes", "WhatsApp link and booking tool detected")
check(int(g["score"]) > int(b["score"]), f"no-booking salon ranks above one with a booking tool ({g['score']} > {b['score']})")
check("gap: no online booking" in g["why"] and "walk-in" in g["signals_hit"], "reason explains signals and gaps")
check(m["fetched"] == "skipped: banned source" and m["website"] == "", "Google Maps link never fetched")
check(n["fetched"] == "no website" and int(n["score"]) == 25, "phone-only lead kept (reachable, no site)")

check(K.best_email('a@sh120.global.temp.domains x support@domaincatch.in info@lakme.in care@unilever.com', 'https://www.lakme.in/') == 'info@lakme.in'
      and K.best_email('support@domaincatch.in', 'https://x.in/') == ''
      and K.best_email('juliet@writerjuliet.com example@mysite.com', 'https://zapier.com/blog/') == ''
      and K.best_email('care.llpl@unilever.com', 'https://www.lakmesalon.in/') == 'care.llpl@unilever.com',
      "own-domain email preferred; placeholders and people's personal off-domain addresses dropped")

# 5. seed-list worlds (b6) + unreachable site
seeds = K.from_urls("b6", os.path.join(FX, "b6-seeds.txt"))
check([s["name"] for s in seeds] == ["NeuroAI", "gone.test"], "seed list parsed (Name|URL and bare URL, comments skipped)")
res = {r["name"]: r for r in K.run("b6", seeds, K.from_html_dir([s["website"] for s in seeds], FX))}
check({"llm", "generative ai", "dpdp", "seed"} <= set(res["NeuroAI"]["signals_hit"].split(", ")), "FinOps signals found (LLM, GenAI, DPDP, seed)")
check(res["gone.test"]["fetched"].startswith("error") and int(res["NeuroAI"]["score"]) > int(res["gone.test"]["score"]), "dead site recorded, ranked last")

# 6. AI step: pluggable, capped, failure-safe, JSON parsing
class Fake:
    calls = 0
    def extract(self, world, md):
        Fake.calls += 1
        if "Booked" in md: raise TimeoutError()
        return {"what_they_do": "Unisex salon", "takes_appointments": "yes"}
rows2 = K.from_osm("b1", "Hyderabad", os.path.join(FX, "osm.json"))
o2 = {r["name"]: r for r in K.run("b1", rows2, pages, Fake(), max_ai=5)}
check(o2["Glow Salon"]["ai_summary"] == "Unisex salon" and o2["Booked Spa"]["ai_fields"] == "error: TimeoutError", "AI fields saved; an AI failure never stops the run")
Fake.calls = 0; K.run("b1", K.from_osm("b1", "Hyderabad", os.path.join(FX, "osm.json")), pages, Fake(), max_ai=1)
check(Fake.calls == 1, "AI calls capped by --max-ai (protects free limits)")
check(K.parse_json('<think>x</think>```json\n{"a": 1}\n```') == {"a": 1} and K.parse_json("nope") == {}, "AI JSON parsed from fenced/thinking output")
os.environ.pop("OPENROUTER_API_KEY", None)
try: K.OpenRouter(); check(False, "OpenRouter must refuse without a key")
except SystemExit as e: check("never paste" in str(e), "OpenRouter needs the secret from the environment, never from chat")

# 7. CLI end to end: all worlds, files + summary, no network
with tempfile.TemporaryDirectory() as d:
    summ = K.main(["--world", "b1", "--from-osm-json", os.path.join(FX, "osm.json"), "--html-dir", FX, "--out", d, "--delay", "0"])
    summ += K.main(["--world", "b6", "--urls", os.path.join(FX, "b6-seeds.txt"), "--html-dir", FX, "--out", os.path.join(d, "b6"), "--delay", "0"])
    data = list(csv.DictReader(open(os.path.join(d, "b1-leads.csv"), encoding="utf-8-sig")))
    check(len(data) == 4 and list(data[0].keys()) == K.COLS, "CSV written with fixed columns")
    check("ODbL" in open(os.path.join(d, "SUMMARY.md")).read(), "summary carries the OpenStreetMap attribution")
    check(summ[0][:4] == ("b1", 4, 2, 3), f"summary counts right {summ[0]}")
print(f"\nAll {ok} Kalpa Leads checks passed")

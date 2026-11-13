import sys, json; import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import leadfinder as lf
fake = {"elements": [
 {"type":"node","id":1,"lat":17.49,"lon":78.39,"tags":{"shop":"hairdresser","name":"Test Clinic A","phone":"+91 98480 00000","addr:street":"KPHB Road"}},
 {"type":"way","id":2,"center":{"lat":17.44,"lon":78.35},"tags":{"amenity":"dentist","name":"Smile Dental","website":"https://x.in","opening_hours":"Mo-Sa 10:00-20:00"}},
 {"type":"node","id":3,"lat":17.49,"lon":78.39,"tags":{"shop":"hairdresser","name":"Test Clinic A","phone":"+91 98480 00000"}},
 {"type":"node","id":4,"lat":17.4,"lon":78.4,"tags":{"amenity":"clinic"}}]}
lf.overpass = lambda q: fake
q = lf.build_query("Hyderabad", lf.NICHE_TAGS["salon"]); assert 'area["name"="Hyderabad"]' in q
rows = lf.collect("Hyderabad", "salon")
assert len(rows) == 2 and rows[0]["name"] == "Test Clinic A" and rows[0]["score"] == 55, rows
import tempfile; out = os.path.join(tempfile.mkdtemp(), "lf_test")
lf.write_csv(out+".csv", rows); lf.write_xlsx(out+".xlsx", {"salon": rows}, "Hyderabad")
from openpyxl import load_workbook; wb = load_workbook(out+".xlsx"); print(wb.sheetnames, wb["Summary"]["B5"].value, [c.value for c in wb["salon"][2]][:4])
print("leadfinder offline test passed")
# --- A08: one walking cluster (Overpass "around" filter), salon type kept for the pitch
q2 = lf.build_query("Hyderabad", lf.NICHE_TAGS["salon"], near=(17.4375, 78.4482), radius=1200)
assert 'nwr(around:1200,17.4375,78.4482)[shop~"^(hairdresser|beauty)$"];' in q2 and "area" not in q2, q2
fake["elements"].append({"type":"node","id":5,"lat":17.438,"lon":78.449,"tags":{"shop":"hairdresser","hairdresser":"unisex","name":"Style Unisex","opening_hours":"Mo-Su 10:00-22:00"}})
rows2 = lf.collect("Hyderabad", "salon", near=(17.4375, 78.4482), radius=1200)
r5 = next(r for r in rows2 if r["name"] == "Style Unisex"); assert r5["kind"] == "unisex" and r5["late"] is True, r5
assert next(r for r in rows2 if r["name"] == "Test Clinic A")["late"] is False
for bad in ["17.4,78.4", "abc", "95,78", "17.4,78.4,1"]:
    try: lf.parse_near(bad) if bad != "17.4,78.4" else None
    except SystemExit: continue
    assert bad == "17.4,78.4", bad
assert lf.parse_near("17.4375, 78.4482") == (17.4375, 78.4482)
print("leadfinder cluster test passed")
assert lf.COLS[0] == "score" and lf.COLS[3] == "phone" and lf.COLS[5] == "website" and lf.COLS[10] == "status", "xlsx formulas use fixed column letters"
assert not any("cosmetics" in t for t in lf.NICHE_TAGS["salon"]), "cosmetics shops are retail, not appointment salons"
assert 'shop~"^(hairdresser|beauty)$"' in lf.NICHE_TAGS["salon"][0]
# --- A208: source column + zero personal mobile numbers
import phones
assert phones.classify("+91 98480 00000") == ("mobile", "+919848000000")
assert phones.classify("040-2345 6789")[0] == "landline" and phones.classify("09848000000")[0] == "mobile"
assert phones.classify("1800 425 1234")[0] == "tollfree" and phones.classify("12345")[0] == "unknown"
assert phones.business_phone("+91 98480 00000; 040 2345 6789") == ("+914023456789", 1)
assert phones.business_phone("", "+91 70000 12345") == ("", 1)
fake["elements"].append({"type":"node","id":6,"lat":17.43,"lon":78.44,"tags":{"shop":"beauty","name":"Lakme Salon","phone":"+91 40 2345 6789","contact:mobile":"+91 99999 11111"}})
rows3 = lf.collect("Hyderabad", "salon")
a = next(r for r in rows3 if r["name"] == "Test Clinic A"); b = next(r for r in rows3 if r["name"] == "Lakme Salon")
assert a["phone"] == "" and a["phone_withheld"] == 1 and a["score"] == 55, a
assert b["phone"] == "+914023456789", b
assert all(r["source"].startswith("OpenStreetMap (ODbL) https://www.openstreetmap.org/") for r in rows3)
assert lf.COLS[-2:] == ["source", "phone_withheld"]
for r in rows3:
    for v in r.values(): assert phones.classify(str(v))[0] != "mobile" or v == "", (r["name"], v)
print("leadfinder A208 mobile-filter test passed")
import check_leads
lf.write_csv(out+"-a208.csv", rows3)
assert check_leads.check([out+"-a208.csv"], need=2) and not check_leads.check([out+"-a208.csv"], need=50)
print("leadfinder A208 check script test passed")

"""A208 check, run in GitHub Actions after the lead finder: 50+ salon/gym leads, source column filled,
zero mobile numbers in any cell. Prints counts only (lead lists are personal data and never printed)."""
import csv, glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phones import classify, has_mobile
IDS = {"osm_id", "maps_link", "source", "lat", "lon", "website", "score", "phone_withheld"}  # long OSM ids are not phones

def check(paths, need=50):
    rows = [r for p in paths for r in csv.DictReader(open(p, encoding="utf-8-sig")) if r.get("niche") in ("salon", "gym")]
    no_src = sum(1 for r in rows if not r.get("source"))
    def mobile(k, v):  # phone column: the whole cell is one number; free text: look for a 10-digit mobile run
        v = str(v or ""); return classify(v)[0] == "mobile" if k == "phone" else has_mobile(v)
    mobiles = sum(1 for r in rows for k, v in r.items() if k not in IDS and mobile(k, v))
    print(f"A208 check: {len(rows)} salon/gym leads in {len(paths)} files, {no_src} without source, {mobiles} mobile numbers")
    return len(rows) >= need and no_src == 0 and mobiles == 0

if __name__ == "__main__":
    sys.exit(0 if check(sys.argv[1:] or glob.glob("01-botbhai/botbhai/leads/*-enriched.csv")) else 1)

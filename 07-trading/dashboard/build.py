"""A339: build the single self-contained dashboard page (Kalpa tokens + chart library + data inlined).

Run from anywhere:  python3 07-trading/dashboard/build.py   ->  07-trading/dashboard/trade-dashboard.html
Needs data.json from export_data.py. Private page: noindex, no network calls except Google Fonts.
"""
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
TOKENS = HERE.parents[1] / "00-hq" / "design" / "tokens.css"
LIB = HERE / "vendor" / "lightweight-charts" / "lightweight-charts.standalone.production.js"
OUT = HERE / "trade-dashboard.html"


def main():
    data = json.loads((HERE / "data.json").read_text())
    for k in ("meta", "strategies", "exits", "trades", "months", "stats", "candles", "demo"):
        if k not in data:
            sys.exit(f"STOP: data.json has no '{k}' (re-run export_data.py)")
    page = (HERE / "template.html").read_text()
    for mark in ("/*TOKENS*/", "/*LIB*/", "__DATA__"):
        if page.count(mark) != 1:
            sys.exit(f"STOP: template must contain {mark} exactly once")
    blob = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")   # can't close the <script> early
    lib = LIB.read_text()
    if "</script" in lib.lower():
        sys.exit("STOP: chart library contains a closing script tag")
    # the library goes in last, so no later replace can touch text inside it
    page = page.replace("/*TOKENS*/", TOKENS.read_text()).replace("__DATA__", blob).replace("/*LIB*/", lib)
    OUT.write_text(page)
    print(f"wrote {OUT.name}: {OUT.stat().st_size // 1024} KB, {len(data['trades'])} trades, {len(data['demo'])} demo trades")


if __name__ == "__main__":
    main()

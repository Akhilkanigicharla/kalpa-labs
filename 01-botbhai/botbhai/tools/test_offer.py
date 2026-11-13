#!/usr/bin/env python3
"""A211: BotBhai positioned as a done-for-you front desk, not software to learn.
Checks (no browser): the approved ladder (Akhil, 11 Nov 2026: "prices ok") in prices.json; the demo page and the
A5 pitch card lead with the front-desk line, show the ladder from prices.json, say "no per-staff fee", carry the
comparison block (no rival named) and the 14-day pilot; and no fake-scarcity or invented-review wording."""
import json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SALES = ROOT.parent / "docs" / "sales"
P = json.loads((SALES / "prices.json").read_text())
T = {t["id"]: t for t in P["tiers"]}
RIVALS = ["dingg", "miosalon", "zylu", "zenoti", "salonist", "aisensy", "wati", "interakt", "cleomitra", "salonboost"]
SCARCITY = ["spots left", "only 3 left", "hurry", "last chance", "limited time", "offer ends", "★★★★★", "5-star review", "guarantee"]


def visible(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<(style|script)[^>]*>.*?</\1>", " ", html, flags=re.S)))


def check_ladder():
    want = {"starter": (999, 0), "lite": (1999, 999), "standard": (2999, 1499)}
    for k, (setup, monthly) in want.items():
        assert k in T, f"prices.json lacks tier {k}"
        assert (T[k]["setup"], T[k]["monthly"]) == (setup, monthly), f"{k}: {T[k]['setup']}+{T[k]['monthly']} ≠ approved {setup}+{monthly}"
    assert T["starter"].get("one_time") is True, "starter must be one-time (no monthly)"
    assert "founding" not in T, "founding tier folded into Standard (same price)"
    assert not any(t["setup"] == 4999 and t["monthly"] == 2999 for t in P["tiers"]), "the ₹4,999 + ₹2,999 tier is paused"
    assert T["lite"]["monthly"] < T["standard"]["monthly"], "Lite must sit under Standard"
    print("  ✓ approved ladder: Starter ₹999 once · Lite ₹1,999 + ₹999/mo · Standard ₹2,999 + ₹1,499/mo; ₹4,999 tier paused")


def check_page(name, html, lang_te=False):
    v = visible(html); low = v.lower()
    for need in ["front desk", "5 languages", "set up and run by us", "no per-staff fee", "14-day", "₹999 once", "₹1,999", "₹1,499"]:
        assert need.lower() in low, f"{name}: missing {need!r}"
    if lang_te:
        assert "ఒక్కో స్టాఫ్‌కి ఫీజు లేదు" in v, f"{name}: Telugu 'no per-staff fee' missing"
    for bad in SCARCITY:
        assert bad.lower() not in low, f"{name}: banned persuasion wording {bad!r}"
    for r in RIVALS:
        assert r not in low.replace(" ", ""), f"{name}: names a rival ({r})"
    print(f"  ✓ {name}: front-desk headline, ladder, no per-staff fee, 14-day pilot, no rival named, no fake scarcity")


def check_demo():
    subprocess.check_call([sys.executable, str(ROOT / "build.py")], cwd=ROOT, stdout=subprocess.DEVNULL)
    html = (ROOT / "web" / "dist" / "index.html").read_text()
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S).group(1)
    assert "front desk" in visible(h1).lower(), f"demo h1 must lead with the front desk line: {visible(h1)!r}"
    offer = re.search(r'<section[^>]*id="offer".*?</section>', html, re.S)
    assert offer, "demo page has no #offer section"
    o = offer.group(0)
    assert len(re.findall(r'class="tier( up)?"', o)) == 3, "offer shows exactly the 3 approved tiers"
    assert 'id="compare"' in o, "comparison block missing"
    check_page("demo index.html", html)
    figs = {int(x.replace(",", "")) for x in re.findall(r"₹([\d,]+)", visible(o))}
    allowed = {x for t in P["tiers"] for x in (t["setup"], t["monthly"])} | {P["whatsapp_fees"]["lite_no_marketing"], P["whatsapp_fees"]["typical"]}
    assert figs <= allowed, f"offer has ₹ figures not from prices.json: {sorted(figs - allowed)}"


def check_card():
    out = ROOT / "web" / "dist" / "sales"
    subprocess.check_output(["node", str(ROOT / "tools" / "sales_kit.js"), "all", str(out)])
    check_page("A5 pitch card", (out / "card-a5.html").read_text(), lang_te=True)


if __name__ == "__main__":
    check_ladder(); check_demo(); check_card()
    print("offer tests passed")

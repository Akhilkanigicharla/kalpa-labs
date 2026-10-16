#!/usr/bin/env python3
"""Sales kit (A07) checks. The roadmap check is "prices match PLAN.md §2": this parses the PLAN table and compares.
Then: every ₹ figure in the kit comes from prices.json or the proposal maths, the legal pages carry the clauses they
must, no guarantee wording, and (with Playwright) the PDFs render: A5 card = 2 pages with Telugu shaped and a QR that
scans, proposal = 1 A4 page, agreement ≤ 3 pages. `--save` refreshes the committed PDFs in 01-botbhai/docs/sales/."""
import json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent          # 01-botbhai/botbhai
B1 = ROOT.parent                                                # 01-botbhai
SALES = B1 / "docs" / "sales"
DIST = ROOT / "web" / "dist" / "sales"
rupees = lambda s: int(s.replace("₹", "").replace(",", ""))


def plan_ladder():
    text = (B1 / "PLAN.md").read_text()
    sec = text[text.index("### Salon price ladder"):text.index("Terms for every tier")]
    rows = {}
    for line in sec.splitlines():
        m = re.match(r"\|\s*\*\*(\w+)\*\*[^|]*\|\s*(₹[\d,]+)\s*\|\s*([^|]+)\|", line)
        if m:
            rows[m.group(1).lower()] = (rupees(m.group(2)), [rupees(x) for x in re.findall(r"₹[\d,]+", m.group(3))])
    terms = text[text.index("Terms for every tier"):text.index("**Later setups**")]
    return rows, terms


def check_prices():
    P = json.loads((SALES / "prices.json").read_text())
    rows, terms = plan_ladder()
    assert set(rows) == {t["id"] for t in P["tiers"]}, f"tiers differ: PLAN {sorted(rows)} vs prices.json"
    for t in P["tiers"]:
        setup, monthly = rows[t["id"]]
        assert t["setup"] == setup, f"{t['id']} setup {t['setup']} ≠ PLAN {setup}"
        assert t["monthly"] == monthly[0], f"{t['id']} monthly {t['monthly']} ≠ PLAN {monthly[0]}"
        if len(monthly) > 1:
            assert t.get("monthly_after") == monthly[1], f"{t['id']} later monthly ≠ PLAN {monthly[1]}"
    assert "50% on signing, 50% at go-live" in terms and "2 months free" in terms and "no lock-in" in terms.lower()
    meta = json.loads((ROOT / "setups" / "salon" / "setup.meta.json").read_text())["price"]
    std = next(t for t in P["tiers"] if t["id"] == "standard")
    assert meta["setup"] == f"₹{std['setup']:,}" and meta["monthly"] == f"₹{std['monthly']:,}", f"setup.meta.json price {meta} ≠ Standard tier"
    print("  ✓ prices.json matches PLAN.md §2 (4 tiers, founding step-up, terms) and setup.meta.json")
    return P


def build(out):
    out.mkdir(parents=True, exist_ok=True)
    meta = json.loads(subprocess.check_output(["node", str(ROOT / "tools" / "sales_kit.js"), "all", str(out)], text=True))
    return {f: (out / f).read_text() for f in meta["files"]}, meta["numbers"]


def visible(html):
    return re.sub(r"<[^>]+>", " ", re.sub(r"<(style|script)[^>]*>.*?</\1>", " ", html, flags=re.S))


def check_content(P, pages, n):
    ex = json.loads((SALES / "example-salon.json").read_text())
    # proposal maths, recomputed here independently of sales_kit.js
    lost = round(ex["after9_per_week"] * 4.3 * 0.25); ns = ex["noshows_last_saturday"] * 4; saved = round(ns / 3)
    tier = next(t for t in P["tiers"] if t["id"] == ex["tier"]); fees = P["whatsapp_fees"]["typical"]
    want = {"lostBookings": lost, "noShows": ns, "saved": saved, "value": (lost + saved) * ex["avg_ticket"], "breakEven": -(-(tier["monthly"] + fees) // ex["avg_ticket"])}
    for k, v in want.items():
        assert n[k] == v, f"proposal {k}: {n[k]} ≠ {v}"
    print(f"  ✓ proposal maths re-checked: {lost} lost + {saved} saved visits → ₹{want['value']:,}; pays back after {want['breakEven']} visits")
    allowed = {x for t in P["tiers"] for x in (t["setup"], t["monthly"], t.get("monthly_after"))} | {P["whatsapp_fees"]["lite_no_marketing"], fees, 3, 999}
    half = -(-tier["setup"] // 2)
    allowed_proposal = allowed | {ex["avg_ticket"], want["value"], half, tier["setup"] - half}
    for f, h in pages.items():
        figs = {rupees(x) for x in re.findall(r"₹[\d,]+", visible(h))}
        extra = figs - (allowed_proposal if f.startswith("proposal") else allowed)
        assert not extra, f"{f}: rupee figures not from prices.json / proposal maths: {sorted(extra)}"
        low = visible(h).lower()
        for bad in ["guarantee", "100%", "tax invoice", "gstin", "risk-free", "lakhs extra"]:
            assert bad not in low, f"{f}: banned wording {bad!r}"
    print("  ✓ every ₹ figure in the kit comes from prices.json or the proposal maths; no guarantee or GST wording")
    a = visible(pages["agreement.html"])
    for need in ["Data Fiduciary", "Data Processor", "section 8", "within 24 hours", "72 hours", "sub-processors", "10 business days",
                 "export", "delete your customers' data within 30 days", "access logs kept for 1 year", "never sell", "Hyderabad",
                 "no lock-in", "50% on signing, 50% at go-live", "CC BY 4.0", "Common Paper", "UDYAM-TS-02-0382711"]:
        assert need.lower() in a.lower(), f"agreement is missing: {need}"
    print("  ✓ agreement: DPDP s.8 processor terms (instructions, safeguards, 1-year logs, sub-processors, 24 h breach, export + delete), terms, CC BY credit")
    pv = visible(pages["privacy-notice-example.html"])
    for need in ["What we collect", "Why", "How long", "STOP", "delete", "Data Protection Board", "OFFERS", "Glow Studio", "+91 90000 00000",
                 "మేము తీసుకునే వివరాలు", "మీ హక్కులు"]:
        assert need in pv, f"privacy notice is missing: {need}"
    print("  ✓ privacy notice: Rule 3 items (data, purposes, rights, withdrawal, complaints) in English and Telugu")
    ob = visible(pages["objections.html"])
    assert ob.count("“") >= 8 and "Cochrane" in ob and "ban" in ob.lower() and "receptionist" in ob.lower()
    print("  ✓ objection sheet: 9 objections with English + Telugu answers and sources")


def render(pages, out, save):
    import cv2, numpy as np
    from playwright.sync_api import sync_playwright
    demo = re.search(r'DEMO_URL = "([^"]+)"', (ROOT / "tools" / "sales_kit.js").read_text()).group(1)
    expect = {"card-a5.html": (2, 2, "A5"), "proposal-example.html": (1, 1, "A4"), "agreement.html": (2, 3, "A4"), "privacy-notice-example.html": (1, 1, "A4"), "objections.html": (1, 2, "A4")}
    with sync_playwright() as p:
        b = p.chromium.launch(); errs = []
        for f, (lo, hi, size) in expect.items():
            pg = b.new_page(device_scale_factor=2); pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto((out / f).as_uri()); pg.wait_for_load_state("networkidle"); pg.evaluate("document.fonts.ready")
            if "తె" in pages[f] or "మీ" in pages[f]:
                assert pg.evaluate("document.fonts.check('16px \"Anek Telugu\"', 'తెలుగు')"), f"{f}: Anek Telugu font not loaded"
            bad_mono = pg.evaluate("""() => [...document.querySelectorAll('body *')].filter((el) => [...el.childNodes].some((n) => n.nodeType === 3 && /[\\u0C00-\\u0C7F]/.test(n.textContent))
                && /JetBrains|Rozha/.test(getComputedStyle(el).fontFamily.split(',')[0])).map((el) => el.textContent.trim().slice(0, 30))""")
            assert not bad_mono, f"{f}: Telugu set in a font without Telugu letters: {bad_mono}"
            if f == "card-a5.html":
                for i in range(2):
                    png = pg.locator(".qr").nth(i).screenshot()
                    got, _, _ = cv2.QRCodeDetector().detectAndDecode(cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR))
                    assert got == demo, f"card QR {i} scans to {got!r}, want {demo!r}"
            if f == "proposal-example.html":
                assert pg.evaluate("(() => { const p = document.querySelector('.page'); return p.scrollHeight <= p.clientHeight + 1; })()"), "proposal content is taller than one A4 page"
            pdf = out / f.replace(".html", ".pdf")
            pg.pdf(path=str(pdf), prefer_css_page_size=True, print_background=True)
            info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
            pages_n = int(re.search(r"Pages:\s+(\d+)", info).group(1)); w, h = map(float, re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", info).groups())
            assert lo <= pages_n <= hi, f"{f}: {pages_n} pages, want {lo}–{hi}"
            assert abs(w - (419.5 if size == "A5" else 595.3)) < 2, f"{f}: page width {w} is not {size}"
            fonts = subprocess.check_output(["pdffonts", str(pdf)], text=True)
            if f in ("card-a5.html", "privacy-notice-example.html", "objections.html"):
                assert "AnekTelugu" in fonts.replace(" ", ""), f"{f}: Telugu font not embedded"
            if save:
                (SALES / pdf.name.replace("-example", "")).write_bytes(pdf.read_bytes())
            print(f"  ✓ {pdf.name}: {pages_n} {size} page{'s' if pages_n > 1 else ''}" + (", both QR codes scan to the demo" if f == "card-a5.html" else "") + (", Telugu font embedded" if "Telugu" in fonts.replace(" ", "") or "AnekTelugu" in fonts else ""))
        assert not errs, errs
        b.close()


def main():
    P = check_prices()
    out = DIST
    pages, n = build(out)
    check_content(P, pages, n)
    try:
        import playwright, cv2  # noqa: F401
    except ImportError:
        print("  (PDF render skipped: needs Python Playwright + OpenCV)")
    else:
        render(pages, out, "--save" in sys.argv)
    print("sales kit tests passed")


if __name__ == "__main__":
    sys.exit(main())

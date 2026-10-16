#!/usr/bin/env python3
"""Billing (A05) checks in a real browser. Run after build.py; needs Playwright + Chromium, OpenCV and poppler-utils.

1. The sample invoice's QR, rendered by Chromium, is scanned with OpenCV and must equal the UPI link exactly.
2. The invoice prints to a one-page A4 PDF whose text (pdftotext) has every required field and no GST wording.
   `--save` refreshes the committed copy in 01-botbhai/docs/billing/sample-invoice.pdf for Akhil to look at.
3. billing.html (demo mode) at 390 px: quick-fill, create, mark paid with a UPI ref, two-tap void; no JS errors.
"""
import pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "web" / "dist"
DOCS = ROOT.parent / "docs" / "billing"


def main():
    import cv2
    import numpy as np
    from playwright.sync_api import sync_playwright

    link = subprocess.check_output(["node", str(ROOT / "tools" / "sample_invoice.js"), str(DIST / "invoice-sample.html"), "--link"], text=True).strip()
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto((DIST / "invoice-sample.html").as_uri())
        png = pg.locator(".qr").screenshot()
        img = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR)
        got, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
        assert got == link, f"QR scan mismatch:\n  got  {got!r}\n  want {link!r}"
        print("  ✓ QR on the rendered invoice scans (OpenCV) to the exact UPI link")
        assert pg.evaluate("document.documentElement.scrollWidth") <= 390, "invoice scrolls sideways at 390 px"
        box = pg.locator(".total .n").bounding_box(); wrap = pg.locator(".tablewrap").bounding_box()
        assert box["x"] + box["width"] <= wrap["x"] + wrap["width"] + 1, f"total is hidden off to the right at 390 px: {box} vs {wrap}"
        assert pg.evaluate("(() => { const w = document.querySelector('.tablewrap'); return w.scrollWidth <= w.clientWidth; })()"), "invoice table scrolls sideways on a phone"
        print("  ✓ invoice page fits 390 px")

        pdf = DIST / "sample-invoice.pdf"  # build output (ignored by git); the committed copy is refreshed only with --save
        pg.emulate_media(media="print")
        pg.pdf(path=str(pdf), format="A4", print_background=True, prefer_css_page_size=True)
        pages = int([l for l in subprocess.check_output(["pdfinfo", str(pdf)], text=True).splitlines() if l.startswith("Pages:")][0].split()[1])
        text = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], text=True)
        need = ["Invoice", "KL/26-27/001", "UDYAM-TS-02-0382711", "Supplier not registered under GST; no GST charged.", "Glow Studio",
                "Rupees Four Thousand Four Hundred Ninety Eight only", "4,498.00", "kalpalabs@example", "Sample only: do not pay"]
        miss = [n for n in need if n.lower() not in text.lower()]  # stamps are upper-cased by CSS
        assert not miss, f"PDF is missing {miss}"
        for bad in ["Tax Invoice", "GSTIN", "CGST", "SGST", "IGST", "Save as PDF"]:
            assert bad not in text, f"PDF must not contain {bad!r}"
        assert pages == 1, f"sample invoice should be 1 page, got {pages}"
        if "--save" in sys.argv or not (DOCS / "sample-invoice.pdf").exists():
            DOCS.mkdir(parents=True, exist_ok=True); (DOCS / "sample-invoice.pdf").write_bytes(pdf.read_bytes())
        print("  ✓ sample PDF renders: 1 A4 page, all fields, no GST words, no screen buttons")

        pg = b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto((DIST / "billing.html").as_uri())
        pg.click("summary"); pg.click("#makekey"); k1 = pg.input_value("#newkey"); pg.click("#makekey"); k2 = pg.input_value("#newkey")
        assert len(k1) == 48 and all(c in "0123456789abcdef" for c in k1) and k1 != k2, (k1, k2)
        print("  ✓ sign-in makes a fresh 192-bit key on the phone (never typed into a chat)")
        pg.goto((DIST / "billing.html").as_uri() + "?demo=1")
        pg.select_option("#client", "c3")
        pg.click("#presets button:text-is('Monthly plan')")
        assert pg.input_value("#amount") == "1499" and "monthly plan" in pg.input_value("#desc").lower()
        assert pg.inner_text("#preview").strip() == "₹1,499"
        pg.click("#create"); pg.wait_for_selector(".inv .num:has-text('KL/26-27/004')")
        print("  ✓ billing page: quick-fill + create → KL/26-27/004 listed")
        card = pg.locator(".inv", has_text="KL/26-27/004")
        card.locator("button:text-is('Mark paid')").click()
        pg.fill("#ref", "6298 1234 5678"); pg.click("button:text-is('Save as paid')")
        pg.click(".chips .chip[data-f=paid]")
        pg.wait_for_selector(".inv.paid:has-text('KL/26-27/004'):has-text('UPI ref 629812345678')")
        print("  ✓ mark paid with a UPI ref (spaces removed) → shows under Paid")
        pg.click(".chips .chip[data-f=open]")
        v = pg.locator(".inv", has_text="KL/26-27/003").locator("button.danger")
        v.click(); assert v.inner_text() == "Tap again to void"; v.click()
        pg.click(".chips .chip[data-f=all]"); pg.wait_for_selector(".inv.void:has-text('KL/26-27/003')")
        print("  ✓ void needs two taps (no pop-up dialogs)")
        assert pg.evaluate("document.documentElement.scrollWidth") <= 390, "billing page scrolls sideways"
        assert not errs, errs
        b.close()
    print("billing UI tests passed")


if __name__ == "__main__":
    sys.exit(main())

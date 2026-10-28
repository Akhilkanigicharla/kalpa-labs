"""A121: the receipt page at 390 px, light + dark: no sideways scroll, total visible. Run: python3 tools/test_receipt_ui.py"""
import json, pathlib, subprocess, sys
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
JS = """const R=require('./core/receipt.js');process.stdout.write(R.receiptHtml(R.makeReceipt(
{business:'Glow Studio Unisex Salon',address:'Road No. 36, Jubilee Hills, Hyderabad',gst:{mode:'regular',gstin:'36ABCDE1234F1Z5',sac:'999721',rate:18,state:'Telangana'}},
{customer:'Sravani Reddy',items:[{name:'Hair spa with long name to test wrapping on small phones',price:'₹1,200'},{name:'Facial',price:'₹1,500'}],discount:100},
{n:12,date:new Date('2026-10-25T10:00:00Z')})))"""
html = subprocess.run(["node", "-e", JS], cwd=ROOT, capture_output=True, text=True, check=True).stdout
bad = 0
with sync_playwright() as p:
    b = p.chromium.launch()
    for scheme in ("light", "dark"):
        pg = b.new_page(viewport={"width": 390, "height": 844}, color_scheme=scheme)
        pg.set_content(html)
        w = pg.evaluate("document.documentElement.scrollWidth")
        total = pg.inner_text(".total .n")
        ok = w <= 390 and total == "₹2,600.00"
        print(f"  {'✓' if ok else '✗'} receipt {scheme}: width {w}, total {total}")
        bad += not ok
    b.close()
if bad:
    sys.exit(1)
print("receipt UI ok at 390 px, light + dark")

// A121: the receipt page at 390 px, light + dark: no sideways scroll, total visible. Run: node tools/receipt_preview.test.js
const { chromium } = require("playwright");
const R = require("../core/receipt.js");
(async () => {
  const r = R.makeReceipt({ business: "Glow Studio Unisex Salon", address: "Road No. 36, Jubilee Hills, Hyderabad", gst: { mode: "regular", gstin: "36ABCDE1234F1Z5", sac: "999721", rate: 18, state: "Telangana" } },
    { customer: "Sravani Reddy", items: [{ name: "Hair spa with long name to test wrapping on small phones", price: "₹1,200" }, { name: "Facial", price: "₹1,500" }], discount: 100 }, { n: 12, date: new Date("2026-10-25T10:00:00Z") });
  const b = await chromium.launch(); let bad = 0;
  for (const scheme of ["light", "dark"]) {
    const p = await b.newPage({ viewport: { width: 390, height: 844 }, colorScheme: scheme });
    await p.setContent(R.receiptHtml(r));
    const w = await p.evaluate(() => document.documentElement.scrollWidth);
    const total = await p.locator(".total .n").innerText();
    const bg = await p.evaluate(() => getComputedStyle(document.body).backgroundColor);
    const okk = w <= 390 && total === "₹2,600.00";
    console.log(`  ${okk ? "✓" : "✗"} receipt ${scheme}: width ${w}, total ${total}, background ${bg}`);
    if (!okk) bad++;
    if (process.env.SHOT) await p.screenshot({ path: `${process.env.SHOT}-${scheme}.png`, fullPage: true });
  }
  await b.close(); if (bad) process.exit(1); console.log("receipt preview ok at 390 px, light + dark");
})();

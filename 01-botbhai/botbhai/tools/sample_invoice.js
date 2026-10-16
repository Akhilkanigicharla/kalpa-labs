// Writes a sample invoice page (A05) for the demo site, the 390 px screen check and the PDF test.
// Usage: node tools/sample_invoice.js <out.html> [--paid]
// The UPI ID uses the reserved "example" handle, so nobody can pay a stranger by scanning it.
const fs = require("fs");
const B = require("../core/billing.js");
const out = process.argv[2]; if (!out) { console.error("usage: node tools/sample_invoice.js <out.html> [--paid]"); process.exit(1); }
const paid = process.argv.includes("--paid");
const SELLER = { name: "Kalpa Labs", address: "Hyderabad, Telangana", phone: "+91 90000 00000", udyam: "UDYAM-TS-02-0382711", vpa: "kalpalabs@example" };
const INV = { number: "KL/26-27/001", issued_on: "2026-10-16", due_on: "2026-10-23", period: "Oct 2026", status: paid ? "paid" : "due",
  paid_on: paid ? "2026-10-18" : null, paid_ref: paid ? "629812345678" : null,
  bill_to: { name: "Glow Studio", address: "Ameerpet, Hyderabad", phone: "919000000000" },
  lines: [{ desc: "BotBhai setup (Founding)", qty: 1, rate_paise: 299900 }, { desc: "BotBhai monthly plan · Oct 2026", qty: 1, rate_paise: 149900 }], total_paise: 449800 };
fs.writeFileSync(out, B.invoiceHTML(INV, SELLER, { now: new Date("2026-10-16T06:00:00Z"), sample: !paid }));
if (require.main === module && process.argv.includes("--link")) console.log(B.upiLink({ vpa: SELLER.vpa, name: SELLER.name, amountPaise: INV.total_paise, number: INV.number }));
module.exports = { SELLER, INV };

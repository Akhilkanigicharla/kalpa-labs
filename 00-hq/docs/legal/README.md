# Kalpa Labs legal drafts (A41 · Q-HQ-05 + Q-HQ-06)

**All of these are careful templates, not legal advice.** Get them read by a lawyer, or the CA at Q-HQ-15, before the first paying customer (CEO items C23 and C24).

| Document | Who it's for | Where (single source) | Status |
|---|---|---|---|
| Invoice (Kalpa → salon) | BotBhai clients | `01-botbhai/botbhai/core/billing.js` → sample `01-botbhai/docs/billing/sample-invoice.pdf` | Built (A05). "Invoice", no GST (CGST s.32), Udyam, KL/26-27/001 |
| BotBhai service agreement + DPDP processor terms | Salons | `01-botbhai/botbhai/tools/sales_kit.js` → `01-botbhai/docs/sales/agreement.pdf` | Draft (A07), review in C23 |
| Salon's privacy notice to its customers (EN + TE) | Salon customers | same tool → `01-botbhai/docs/sales/privacy-notice.pdf` | Draft (A07) |
| Kit terms, privacy, refunds, delivery, contact, about | Kit buyers | `05-deals/site/src/lib/kits.ts` → `/legal/*` on the calculator site | Draft (A11), review in C24 |
| **Kalpa Labs website privacy notice** | Visitors to our own sites (BotBhai demo/website chat, calculators) | [privacy-kalpa-labs.md](privacy-kalpa-labs.md) | Draft (this item) |
| **Kalpa Labs website terms of use** | Same | [terms-kalpa-labs.md](terms-kalpa-labs.md) | Draft (this item) |

Every document is written from one source file, so a price or address changes in one place. Tests check prices against the PLANs, and check that required clauses are present (`01-botbhai/botbhai/tools/test_sales_kit.py`, `05-deals/site/src/lib/kits.test.ts`).

Laws these follow (checked 16 Oct 2026; sources in `01-botbhai/research/sales-kit-scan.md` and `03-kits/design/BRIEF.md`):
- DPDP Act 2023 + Rules 2025 (most duties apply from about 13 May 2027)
- CGST Act s.32 (no GST collected while unregistered)
- Consumer Protection (E-Commerce) Rules 2020
- CCPA Dark Patterns Guidelines 2023
- Meta's WhatsApp opt-in rules

# Salary Tax-Regime + SIP Goal Planner 2026-27 (A20 · K-08)

The product file is `03-kits/products/Kalpa-Tax-SIP-Planner-2026-27.xlsx`, built by `build_kit.py`. Never edit it by hand: change the builder and rebuild.

**Tabs:**
- **Start:** how to use, in English and Telugu.
- **Tax:** old vs new regime, with 80C, 80D, HRA, home-loan interest and NPS caps applied.
- **HRA**
- **SIP goal:** step-up and inflation; the return is the buyer's own assumption.
- **Loan:** EMI and how much an extra monthly payment saves.
- **Self-check:** the official examples, all PASS.
- **Rules:** the 2026-27 slabs, with sources.

**Proof:** `python3 03-kits/tax-sip/test_kit.py` recalculates the real file in LibreOffice and compares it with the calculator site's engine (`05-deals/site/src/lib/fin.ts`):
- 157 salary cases: exact match
- HRA, SIP and EMI: match
- the in-sheet fixtures: PASS

It runs in CI (Kalpa quality → kits).

**Limits, stated in the sheet:** income above ₹50 lakh shows a "surcharge not included" warning. The sheet names no funds and promises no returns (SEBI). It's a calculator, not advice.

## Akhil: make it sellable (10 min, after C24)
1. Upload the .xlsx to Google Drive → open it with Google Sheets → File → Save as Google Sheets.
2. Open the Self-check tab: every row must say PASS.
3. Share → "Anyone with the link" → Viewer. Copy the link and change `/edit…` at the end to `/copy`. That's the delivery link buyers get after paying (A21 sends it).
4. Send Claude the Razorpay Payment Page link for ₹199. It goes into `buyUrl` in `05-deals/site/src/lib/kits.ts`.

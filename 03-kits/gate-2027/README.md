# GATE 2027 Final-120-Days Tracker · CS (A19 · K-02)

The product files in `03-kits/products/` are built by `build_kit.py`:
- `Kalpa-GATE-2027-CS-Lite.xlsx`: free, share view-only
- `…-Kit.xlsx`: ₹199
- `…-Pro.xlsx`: ₹299

Proof: `python3 03-kits/gate-2027/test_kit.py` (also in CI). The 25-item QA checklist is in `03-kits/docs/qa.md`; the ☐ items are yours.

**v1 covers the CS paper**, the biggest market we can serve well. Other papers (DA, EC, ME…) use the same builder with their own syllabus lists.

## Akhil: make it sellable (15 min, after C24)
1. Do the ☐ items in `03-kits/docs/qa.md` (Google Sheets import, `/copy` link test, a Telugu read).
2. Upload Lite → Save as Google Sheets → Share "Anyone with the link: Viewer". Send Claude the link (it goes into the Lite button on the kit page).
3. Upload Kit and Pro → make a `/copy` link for each (Share → Viewer, then change `/edit` to `/copy`). Make two Razorpay Payment Pages (₹199, ₹299) and send Claude both payment links. Keep the copy links private: A21 puts them on the success page.

# Billing scan (A05): invoices, UPI QR, GST wording · 16 Oct 2026

Goal: the "manual billing" item in the BotBhai plan (S8 / P1-W2-06). Kalpa Labs bills each salon: one "Invoice" (no GST), a UPI QR and a paid flag. Everything here was checked on 16 Oct 2026.

## Answer first
- **QR: vendor `uqr` 0.1.3 unmodified** (unjs, MIT, © Project Nayuki + Anthony Fu, zero dependencies, 23 M npm downloads/month). It round-tripped **300/300 random UPI links** through an independent decoder (jsQR). It ships a CommonJS build, so BotBhai's Netlify Functions stay free of npm packages.
- **Invoice maths: reuse our JobCard code** (`02-jobcard/lib/invoice.mjs`: paise maths, Indian amount-in-words, FY series), ported to CommonJS. A test runs both copies side by side so they can't drift apart.
- **PDF: print the Kalamkari HTML invoice from the browser** (any phone: Share → Print → Save as PDF). The test renders it to PDF with Chromium and reads it back with `pdftotext`. We need no PDF library on the server, and Telugu shapes correctly (Deep Scan v2 found pdf-lib can't shape Telugu).
- **Wording: "Invoice"**, never "Tax Invoice". Add the line "Supplier not registered under GST; no GST charged." Show no GST anywhere. CGST Act s.32(1) bars an unregistered person from collecting any amount as tax.
- **Hosted invoice link** (the Stripe/Razorpay pattern): each invoice gets a random 128-bit view key. The salon opens `/.netlify/functions/billing?v=<key>` with no login, and the key is useless for anything else.

## GitHub, ranked by stars (topic pages, 16 Oct 2026)
| Repo | ★ | Licence | Verdict |
|---|---|---|---|
| [nayuki/QR-Code-generator](https://github.com/nayuki/QR-Code-generator) | 6.8k | MIT | LEARN: the reference encoder that uqr is derived from |
| [Shane32/QRCoder](https://github.com/Shane32/QRCoder) | 5.2k | MIT | C#, not our stack |
| [cozmo/jsQR](https://github.com/cozmo/jsQR) | 4.0k | Apache-2.0 | ADOPT **in tests only** (independent decoder) |
| [zxing-js/library](https://github.com/zxing-js/library) | 2.9k | Apache-2.0 | Alternative decoder; not needed |
| [unjs/uqr](https://github.com/unjs/uqr) | 765 | MIT | **ADOPT (vendored)**: SVG output, CJS + ESM, 0 deps |
| [kazuhikoarase/qrcode-generator](https://www.npmjs.com/package/qrcode-generator) | (npm 16 M/mo) | MIT | Also passed; SVG 43 % larger than uqr's |
| [PatilShreyas/EasyUpiPayment-Android](https://github.com/PatilShreyas/EasyUpiPayment-Android) | 378 | Apache-2.0 | Android-only; LEARN its parameter checks |
| [PtPrashantTripathi/linkpe](https://github.com/PtPrashantTripathi/linkpe) | 101 | (check) | Shareable UPI pages: same idea as our hosted link |
| [tuhinpal/Upier](https://github.com/tuhinpal/Upier) | 51 | MIT | LEARN (UPI link pages) |
| [knit-pay/upi-qr-code-payment-for-woocommerce](https://github.com/knit-pay/upi-qr-code-payment-for-woocommerce) | 39 | GPL | AVOID (GPL) |
| [bhar4t/upiqr](https://github.com/bhar4t/upiqr) | 31 | MIT | PNG only, 2.1k downloads/mo; we write the 6-field link ourselves |

The invoice apps were mapped in `02-jobcard/research/deep-scan-v2.md`: only InvoicePlane (MIT) and Invio (Unlicense) are safe to borrow from. Invoice Ninja (Elastic), Akaunting (BSL) and IDURAR/Crater/InvoiceShelf/easy-invoice-pdf (AGPL) are **AVOID**.

## UPI link rules (NPCI UPI Linking Specs v1.6)
- `pa` (UPI ID) and `pn` (payee name) are mandatory. `am` is a decimal ("2999.00"). If `am` is present and `mam` is absent, **the payer can't edit the amount**, which is what an invoice needs. `cu` is INR only. `tr` (reference) is mandatory for merchant/dynamic links, so we send the invoice number without slashes. `tn` is a short note. Spaces are written as `%20`.
- Show the **UPI ID in text under the QR** (NPCI guidance repeated in the deep-link-abuse write-up), so the payer can check who they're paying.
- Reports in 2026 say payment apps reject malformed links with a misleading "limit exceeded" error (missing `am` key, integer amounts, reused `tr`, `intent://` wrapping). We use a URL builder, 2-decimal amounts, one unique `tr` per invoice and a plain `upi://pay`. A **QR on a second phone always works**, so the page shows the QR first and a "Pay with UPI app" button second.
- Plan: Akhil opens a free **business** UPI QR (PLAN Q-HQ-04). A business ID is a merchant ID, which is more reliable for pre-filled links than a personal one.

## GST wording
- [CGST Act s.32(1)](https://www.knowyourgst.com/gstlaw/cgst-act/32-prohibition-of-unauthorised-collection-of-tax-32/): "A person who is not a registered person shall not collect in respect of any supply … any amount by way of tax." So: no GST line, no GSTIN, no "Tax Invoice".
- The Rule 46/49 formats apply only to registered persons ([knowyourgst Q&A](https://www.knowyourgst.com/qa/unragisterd-dealer-invoice-formate/704/)). We still follow their good habits: one series per financial year (`KL/26-27/001`, ≤ 16 characters), date, supplier name and address, customer, description, amount, and amount in words.
- The Udyam number goes on every invoice (company PLAN). **The CA consult (Q-HQ-15) should confirm this wording.**

## Built from this
A05: `invoices` table + atomic `next_invoice_no()`, `core/billing.js`, `core/functions/billing.js` (hosted invoice + admin actions), `web/billing.html` (Akhil's phone page), sample PDF in `01-botbhai/docs/billing/`.

Sources: [github.com/topics/qrcode](https://github.com/topics/qrcode?o=desc&s=stars) · [github.com/topics/upi](https://github.com/topics/upi?o=desc&s=stars) · [unjs/uqr](https://github.com/unjs/uqr) · [bhar4t/upiqr](https://github.com/bhar4t/upiqr) · [NPCI Linking Specs v1.6 (copy)](https://www.labnol.org/files/linking.pdf) · [UPI deep-link abuse](https://medium.com/@aryan.dcgpt/upi-qr-deep-link-abuse-how-attackers-exploit-payment-intents-and-how-to-stop-them-362e1e07c8f9) · [UPI "limit exceeded" causes](https://www.technetexperts.com/fix-upi-limit-exceeded-error/) · [Google Pay India intent params](https://developers.google.com/pay/india/api/android/in-app-payments) · npm registry API (versions, licences, downloads).

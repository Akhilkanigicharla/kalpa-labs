# Billing salons (A05): how Akhil uses it

**What it is:** Kalpa Labs invoices each salon from a phone page. The salon gets a WhatsApp message with a link, sees the invoice with a UPI QR, and pays. Akhil marks it paid. No GST (Kalpa Labs isn't GST-registered). Numbers run KL/26-27/001, 002… and restart on 1 April.

Sample: [sample-invoice.pdf](sample-invoice.pdf) (made by the tests; the UPI ID on it is fake on purpose).

## One-time setup (about 15 min, after the business UPI QR, Q-HQ-04)
1. Open `https://<botbhai site>/billing.html` → **First time? Make a billing key** → **Make**. It copies a random key.
2. In Netlify → Site configuration → Environment variables, add:
   - `BILLING_ADMIN_KEY` = the key you just copied
   - `BILLING_UPI_ID` = your **business** UPI ID (e.g. `kalpalabs@ybl`)
   - optional: `BILLING_PHONE`, `BILLING_ADDRESS`, `BILLING_EMAIL`
3. Supabase → SQL Editor: paste `botbhai/supabase/schema.sql` once (safe to re-run).
4. Redeploy, open `billing.html`, paste the key. Never send the key in any chat.

## Every month (2 min per salon)
1. **New invoice** → pick the salon → tap **Monthly plan** → **Create invoice**.
2. **Send on WhatsApp**. Overdue ones show **Send reminder** (days 3 and 7, per PLAN).
3. When the money arrives, tap **Mark paid** and paste the 12-digit UPI reference from your UPI app.
4. Made a mistake? **Void** it (tap twice). The number stays in the series. Never delete invoices.

## Rules built in
- The page says "Invoice", never "Tax Invoice". It shows no GST and carries the Udyam number. Sources: `01-botbhai/research/billing-scan.md`. The CA consult (Q-HQ-15) should confirm the wording.
- The salon's link carries a 128-bit random key. It is rate-limited, never indexed or cached, and is useless for anything except viewing that one invoice.

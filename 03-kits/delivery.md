# Kit delivery (A21 · K-06)

**Flow:** buyer pays on a Razorpay Payment Page → Razorpay calls `POST /api/razorpay-webhook` → we verify the signature and log the order in Cloudflare KV → the buyer is sent to `/kits/thanks/?razorpay_payment_id=…` → that page shows the "Make a copy" link and a guide PDF stamped with the buyer's email and payment ID.

**Code:** `05-deals/site/src/lib/delivery.ts` (logic) and `05-deals/site/functions/api/*` (Cloudflare Pages Functions).

**Tests:** `npm test` in `05-deals/site` (30 tests, fake payloads only). They cover:
- forged, wrong and tampered signatures
- duplicate events
- a ₹1 payment for a ₹199 kit going to review, not delivery
- product found from notes or from the page title
- status and copy link only for paid orders
- the stamp on every page of the guide

**Rules followed (Razorpay docs):**
- verify the raw body with HMAC-SHA256;
- de-duplicate with `x-razorpay-event-id`;
- deliver only on `payment.captured` / `order.paid`;
- the amount must equal the page price.

## Akhil: switch it on (20 min, after Razorpay KYC and C10 Cloudflare Pages)
1. Cloudflare → Workers & Pages → KV → create a namespace `kits`. In the Pages project → Settings → Functions → KV bindings, add `KITS_KV` = `kits`.
2. Razorpay → each kit's Payment Page:
   - add a hidden note, or put the kit name in the page title, exactly as on the site (for example "GATE 2027 Final-120-Days Tracker (Kit Pro)");
   - set **Redirect after payment** to `https://<your site>/kits/thanks/`.
3. Razorpay → Settings → Webhooks → add `https://<your site>/api/razorpay-webhook`, events `payment.captured` and `order.paid`, and make a secret there.
4. Cloudflare Pages → Settings → Environment variables (encrypted):
   - `RAZORPAY_WEBHOOK_SECRET` = that secret;
   - `KIT_COPY_URLS` = `{"gate-2027:kit":"…/copy","gate-2027:pro":"…/copy","tax-sip-2026-27:kit":"…/copy"}`.
   - Never paste these into a chat.
5. Test in Razorpay **Test mode** with a test card: the thank-you page should show the kit within seconds.

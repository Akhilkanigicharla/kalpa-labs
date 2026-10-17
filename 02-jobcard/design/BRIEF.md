# JobCard screens: design brief (A13)

**Who:** an AC / fridge technician in Hyderabad. He thinks in Telugu, speaks Tenglish, and uses a ₹8–15k Android phone, often on a terrace with weak signal and wet hands. He opens the app right after a job, has about 1 minute, and wants the customer to get a proper bill.

**Flow (one screen each, bottom tabs, phone first, Kalamkari tokens from `00-hq/design/`, world colour `--l2`):**

| Tab | What it does | What it must never do |
|---|---|---|
| **Record · రికార్డ్** | Hold the big gold mic and speak (2-min cap keeps speech-to-text cost down, PLAN §3). The note shows as text with every number highlighted. Chips show what was heard: customer, phone, machine, problem, parts + price, next service | Hide a gap. A chip turns gold with "?" when something wasn't heard |
| **Job card · కార్డ్** | Customer, tap-to-call phone, machine, problem tags, parts with ₹, total. A check line compares the parts with the total he said | Invent a value: unknown prices show "₹ ?" (the parser never guesses) |
| **Bill · బిల్లు** | The real bill (from `lib/invoice.mjs`) the customer gets, with a UPI QR. A green "Send on WhatsApp" button, Save PDF, and how it was paid | Show GST on a Bill of Supply. Unregistered technicians charge none, and the screen says why in one line |
| **Reminders · రిమైండర్** | Customers whose 6-month service is due within 30 days, latest first, and what they paid last time. Call or WhatsApp, with a ready Telugu message | Bulk-send. Messages go one at a time from his own WhatsApp, only to customers who gave their number for that job (Meta / TRAI rules) |

## Where the numbers come from
`sample.mjs` runs the **real core** on made-up notes:
- `parseTranscript` makes the card and the reminders. Each note is parsed with the date the job was done.
- `computeInvoice`, `invoiceNo`, `upiLink` and `invoiceHTML` make the bill and its QR.

It writes the result into `app.html` (`<script id="jc-data">`) and `invoice-sample.html`. Every phone number is a made-up 90000 xxxxx number. After changing the core, run `node 02-jobcard/design/sample.mjs`. `test/design.test.mjs` fails if the page is stale.

Building these screens found a parser bug: "Customer Anjali, …" lost the name because speech-to-text capitalises "Customer". It is fixed, with a test in `test/core.test.mjs`.

## Research applied
- **a4 + Deep Scan v2:**
  - expo-speech-recognition (te-IN / hi-IN / en-IN, works offline once the language pack is on the phone) → "No signal? It still records."
  - expo-print and the browser shape Telugu correctly → the bill is HTML.
  - UPI `upi://pay` QR on the bill.
- **Microsoft Research "UIs for low-literate users" and Patel et al. (CHI 2009, spoken web):**
  - voice plus pictures beats text and deep menus;
  - one task per screen, a 4-item flat tab bar, icon + Telugu + English on every tab;
  - first-time use must work without training.
- **PLAN.md §2:** prices (Free 10 cards; Pro ₹149/month or ₹1,490/year; Team ₹299). §4: the pitch is repeat jobs, so Reminders leads with the rupees those customers paid last time.

## Rules for these screens
1. One big action per screen, at least 44 px targets (the mic is 104 px), and a bottom tab bar.
2. **Telugu always in the body font** (Anek Telugu, self-hosted). Rozha One is for English headings only. `screens.py` fails if any Telugu text renders in Rozha.
3. Money in mono with `tabular-nums`. The spoken numbers are highlighted, because they become the bill.
4. No external requests: fonts come from `00-hq/design/fonts`. The only outside links are `tel:` and `wa.me` taps.
5. Light + dark at 390 px. `python3 02-jobcard/design/screens.py` checks 9 screens and saves PNGs to `design/screens/` (not in git).

## Next (not in this item)
- **b2.q19:** scaffold the Expo app (create-expo-stack, NativeWind with these tokens) and port these screens one to one.
- The reminder message template is checked by C17 (the Telugu read-through) before it goes to real customers.

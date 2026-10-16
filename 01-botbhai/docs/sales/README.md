# BotBhai sales kit (A07)

| File | When | Notes |
|---|---|---|
| [card-a5.pdf](card-a5.pdf) | Leave behind after every walk-in | Front Telugu, back English. Print double-sided on A5. Write your number and the owner's 3 answers by hand |
| [proposal.pdf](proposal.pdf) | Visit 2 | Example for a made-up salon. Make a real one from the owner's answers (below) |
| [agreement.pdf](agreement.pdf) | Visit 2, with the proposal | Includes the DPDP processor clause. **Get it checked by a lawyer before the first signature (C23)** |
| [privacy-notice.pdf](privacy-notice.pdf) | At go-live | The salon's notice to its customers, in English and Telugu. Make one per salon (below) |
| [objections.pdf](objections.pdf) | Read before each walk-in | 9 answers with Telugu one-liners |

**Prices** live in [prices.json](prices.json) and must match PLAN.md §2. Change both together; the test fails if they differ.

## Make a proposal or privacy notice for a real salon
1. Copy `example-salon.json` to `<salon>.json` and fill in the walk-in answers: after-9 PM WhatsApps per week, no-shows last Saturday, who answers during a facial, average bill, tier.
2. Ask Claude: "make the BotBhai proposal for `<salon>.json`". It runs `node botbhai/tools/sales_kit.js proposal <salon>.json <out.html>`, prints it to PDF and sends it to you.

The proposal shows its maths on the page: 1 in 4 late enquiries would have booked, 4 Saturdays a month, and reminders save about 1 in 3 no-shows (Cochrane review). Everything is an estimate; never promise a number of bookings.

## Checks
`python3 botbhai/tools/test_sales_kit.py` (part of test-all) checks:
- The prices match PLAN.md, and every ₹ figure in the kit comes from prices.json or the proposal maths.
- The proposal maths is right, and the legal clauses are present.
- Telugu renders in a Telugu font, and the QR codes scan.
- Each page count is right.

`--save` refreshes the PDFs in this folder. Research and sources: `01-botbhai/research/sales-kit-scan.md`.

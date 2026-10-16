# BotBhai sales kit (A07)

| File | When | Notes |
|---|---|---|
| [card-a5.pdf](card-a5.pdf) | Leave behind after every walk-in | Front Telugu, back English. Print double-sided on A5. Write your number and the owner's 3 answers by hand |
| [proposal.pdf](proposal.pdf) | Visit 2 | Example for a made-up salon. Make a real one from the owner's answers (below) |
| [agreement.pdf](agreement.pdf) | Visit 2, with the proposal | Includes the DPDP processor clause. **Get it checked by a lawyer before the first signature (C23)** |
| [privacy-notice.pdf](privacy-notice.pdf) | At go-live | The salon's notice to its customers, in English and Telugu. Make one per salon (below) |
| [objections.pdf](objections.pdf) | Read before each walk-in | 9 answers with Telugu one-liners |
| [visit-cluster1.pdf](visit-cluster1.pdf) | Walk-in day, Cluster 1 (SR Nagar / Ameerpet) | 3 mapped salons in the shortest walking order from Ameerpet Metro, a pitch for each, and 5 rows for salons you spot on the way. No phone numbers: walk-ins only |

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

## Make the next cluster's visit sheet
1. GitHub → Actions → **BotBhai lead finder** → Run workflow, with `niches` = `salon`, `near` = the cluster centre (for example KPHB `17.4934,78.3996`) and `radius` = `1300`. The result is a private download, kept for 7 days.
2. Ask Claude: "make the visit sheet for cluster 2". It runs `python3 botbhai/tools/visit_sheet.py <leads.csv> --start <lat,lon> --cluster "Cluster 2 · KPHB" --spotted 4 --out docs/sales/visit-cluster2.html` and prints it.

OpenStreetMap lists few salons in Hyderabad: only 3 near Ameerpet on 16 Oct 2026, so the sheet adds rows for salons you see on the street. Optional: after a visit, add the salon to OpenStreetMap with the free StreetComplete or Every Door app (2 min). Each one you add helps the next sheet.

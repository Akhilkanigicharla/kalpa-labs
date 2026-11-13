# Lead lists (not stored in git)

Lead files contain business phone numbers; some are owners' personal mobiles, which is personal data under India's DPDP Act 2023. So they are **not committed** (see `.gitignore`).

Make a fresh list (OpenStreetMap data, ODbL: credit "© OpenStreetMap contributors"):

```bash
cd 01-botbhai/botbhai/leadfinder
python leadfinder.py --city Hyderabad --niche salon gym realestate examkits --out ../leads
```

Keep working copies in a private Google Sheet. Old versions (12–16 Oct 2026) remain in git history; remove them from history before the repo is ever made public (CEO task C20).

## A208 (13 Nov 2026): lawful sources only, no mobile numbers
- Every lead has a `source` column: the OpenStreetMap object link (ODbL, attribution kept) and, after enrichment, `own website <url>`.
- Mobile numbers (10 digits starting 6–9) are withheld from every source, because they can be a person's own phone; `phone_withheld` counts them. Only landlines and toll-free numbers stay. WhatsApp buttons are kept as a yes/no flag, never the number.
- Not used: Google Maps pages, Justdial, LinkedIn, Instagram (their terms forbid scraping). Google Places API and government open data are not wired in yet (no free, no-card source verified for salon/gym lists).
- `leadfinder/check_leads.py` runs in the workflow after each run and fails it unless there are 50+ salon/gym leads, every row has a source and no cell holds a mobile number. It prints counts only.

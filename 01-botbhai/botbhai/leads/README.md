# Lead lists (not stored in git)

Lead files contain business phone numbers; some are owners' personal mobiles, which is personal data under India's DPDP Act 2023. So they are **not committed** (see `.gitignore`).

Make a fresh list (OpenStreetMap data, ODbL: credit "© OpenStreetMap contributors"):

```bash
cd 01-botbhai/botbhai/leadfinder
python leadfinder.py --city Hyderabad --niche salon gym realestate examkits --out ../leads
```

Keep working copies in a private Google Sheet. Old versions (12–16 Oct 2026) remain in git history; remove them from history before the repo is ever made public (CEO task C20).

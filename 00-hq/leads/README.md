# Kalpa Leads: one lead finder for all 8 worlds

**What it does:** finds organisations each world can sell to (or partner with). It reads only their own public websites and scores each one with a reason.
**Tools (free, open source):** Crawl4AI (Apache-2.0) reads the sites. NuExtract3 4B (Apache-2.0, Hugging Face) is an optional free AI that runs in the cloud with no key. Why these: [bake-off](../research/lead-scraper-bakeoff-2026-10-19.md).

| World | Looks for | Source |
|---|---|---|
| HQ | Offices/companies needing an AI website chat or the workshop | OpenStreetMap |
| b1 BotBhai | Salons, gyms, clinics, real-estate offices taking bookings by phone | OpenStreetMap |
| b2 JobCard | AC / appliance / electrical repair businesses | OpenStreetMap |
| b3 Kits | Coaching institutes and colleges (partners, never students) | OpenStreetMap |
| b4 Tab Lifeboat | Tool directories and blogs that list extensions | `seeds/b4.txt` |
| b5 Deals | Public affiliate programmes | `seeds/b5.txt` |
| b6 Ledger Peaks | Indian AI startups (LLM spend, DPDP) | OpenStreetMap + `seeds/b6.txt` |
| b7 Trading Lab | Research data sources only, never customers (SEBI) | `seeds/b7.txt` |

## Run it (GitHub, free, nothing on your PC)
GitHub → Actions → **Kalpa Leads** → Run workflow → choose a world → download the `kalpa-leads` file when it finishes.
- `llm = none`: about 5 minutes. Gives contacts plus a score.
- `llm = nuextract`: about 1 minute per site. Adds an AI summary of each organisation (free).
- `llm = openrouter`: only works after you add the `OPENROUTER_API_KEY` secret yourself.

## Rules (built into the code and tested)
- Only organisations' own websites; robots.txt is respected.
- Never Google Maps, Justdial, Instagram, Facebook, LinkedIn or IndiaMART.
- Lists stay private: a 7-day Actions download, never committed.
- Nobody is messaged automatically (TRAI and WhatsApp opt-in rules). Akhil decides who to contact.

Tests: `python3 00-hq/leads/test_kalpa_leads.py` (offline, 23 checks).

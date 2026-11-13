# Kalpa Labs connectors: what is connected, what works, what each world uses it for

Checked live on 14 Nov 2026 (00:50–01:30 IST) from a Claude cloud session, read-only calls only.
Re-check this list when Akhil adds or reconnects a connector. Secrets are never stored here.

## Working now

| Connector | Live check (14 Nov) | Used for | Rule |
|---|---|---|---|
| **Netlify** | 2 sites: `kalpa-labs` → https://kalpalabs.dpdns.org (deployed 12 Nov, HTTP 200), `kalpa-botbhai` → https://kalpa-botbhai.netlify.app (HTTP 200). Last 24 h on the HQ site: 31 home-page views, 1 visit from Google, **153 404s, almost all bots probing for `.env`, `secrets.txt`, `.claude/.credentials.json`, `gcp-key.json`** (all 404, nothing leaked); 6 real 404s for `/favicon.ico` | Deploy status, traffic and error logs for every Kalpa site; spotting attack probes | Read freely. Deploys follow the standing go (depth check green) |
| **Hugging Face** | Signed in as `kalpalabs5145` (free, no Pro); scopes include `inference-api`, `jobs` | Model/dataset search (Telugu TTS, Kronos weights), Spaces | Free tier only |
| **Firecrawl** | Search + page scrape working (used for the 13 Nov trading and reel research) | Web research for every world, competitor prices | Cite sources; no logged-in pages |
| **PostHog** | Project "Default project" (id 309944, EU host), **0 events ingested**: no site sends analytics yet | Product analytics once a site is wired (A270) | Cookieless only + privacy note (DPDP) before any tracking |
| **Supabase** | Org "Akhilkanigicharla's Org", **0 projects visible** to this login | BotBhai/Kalpa QR databases | The self-hosted n8n Postgres (`kalpa-n8n`) is not in this org: it is on another login, or was removed (C84) |
| **TEXT TO QUANT** | Free plan: **5 backtests for life**, crypto only (Binance), 1h–1w, 3 years | Second-opinion backtests for Track B (crypto) | Spend only on a strategy that already passed our own gate |
| **Cloudflare Developer Platform** | Signed in; 0 Workers | Planned Workers timer (C65 keys) | — |
| **Gmail, Google Calendar, Docs, Sheets, Slides** | Connected | Kalpa Ledger sheet, daily brief, docs | Never send mail or messages to customers (Akhil's call) |
| **Zapier** | Connected, **no actions enabled** | Only if a free n8n route does not exist | Prefer n8n (free) |
| **Floot** | Connected, no projects | Not needed: Kalpa builds on GitHub + Netlify | Do not move code there |
| **PaperOffice** | Connected | Not needed now (no invoices yet) | — |
| **SlickTrip** | Connected | Not a Kalpa tool (travel) | — |

## Not working: Akhil reconnects on the PC (C84)

| Connector | State | Why it matters |
|---|---|---|
| **n8n** (self-hosted, https://kalpa-n8n.onrender.com) | Connector returns 404; the server did not answer a health check within 90 s (Render free sleeps or is down) | The 22-agent team runs here |
| **Render** | Sign-in expired | Hosts the self-hosted n8n |
| **Google Drive** | Sign-in expired | Files for kits and the ledger |
| **Coinversa Pulse** | Sign-in expired | Optional crypto market data |
| **Ryze AI (ads/SEO)** | Setup never finished | Optional |

## Fixes made from this check
- `/favicon.ico` 404 → added `favicon.ico`, `favicon.svg` (the Kalpavruksha mark) and `apple-touch-icon.png` to `00-hq/site`, linked from `index.html` and `404.html`. Goes live with the next HQ site deploy.

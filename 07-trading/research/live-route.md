# Live route: where a real order may be sent from (A224)

_Lane A, 28 Nov 2026. Own money only, through a registered broker. Not advice to anyone._

**Answer:** GitHub Actions can never send a real order (no fixed IP). Keep **L1 manual orders** (₹0, no static IP). If an API bot is ever approved, the first route is **Dhan Cloud** (no static IP, already built in `deploy/dhan-cloud/`); a free Oracle VM is a backup that needs Akhil's card and his yes. The code now refuses any other route (tested).

## 1. The rules (in force for every broker since 1 Apr 2026)

| Rule | What it means for us | Sources (read 28 Nov 2026) |
|---|---|---|
| Framework + date | SEBI circular SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013 (4 Feb 2025); extension circular SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/132 (30 Sep 2025): "W.e.f. April 01, 2026" for all brokers | [SEBI 30 Sep 2025 PDF](https://www.sebi.gov.in/sebi_data/attachdocs/sep-2025/1759232056254.pdf), [NSE FAQ 3 Nov 2025](https://nsearchives.nseindia.com/web/sites/default/files/inline-files/FAQ_Retail_Algo_03112025_NSE.pdf) |
| Static IP for API orders | Order APIs accept orders only from the client's whitelisted IP. Zerodha: up to 2 IPs, **one change per calendar week**, used only by you or immediate family. Data, websocket, orderbook, positions are not IP-locked | [Zerodha static IP](https://support.zerodha.com/category/trading-and-markets/general-kite/kite-api/articles/static-ip), [Fyers](https://support.fyers.in/portal/en/kb/articles/what-are-the-new-sebi-rules-for-retail-algo-trading-from-april-01-2026), [Upstox](https://community.upstox.com/t/important-update-regulatory-changes-for-api-and-algo-trading-are-now-live/14874) |
| 10 orders/second | Above 10 OPS a strategy needs exchange registration (Algo ID); our bot sends a few orders a day, so no registration | Upstox, Fyers (above), NSE FAQ 8 |
| Every API order is an algo order | Tagged by the broker; **market orders are not allowed for algo orders** (NSE FAQ 11); Upstox blocks them, Fyers converts them to price-protected orders | NSE FAQ, Upstox, Fyers |
| Daily 2FA | Log in with 2FA once every trading day; no endless refresh-token sessions | Fyers (above); Dhan Cloud syncs its own token (see `deploy/dhan-cloud/README.md`) |

## 2. Routes compared

| Route | Fixed IP? | Cost | Verdict |
|---|---|---|---|
| GitHub Actions (free runners) | No. Static IPs exist only on paid "larger runners" for Team/Enterprise orgs ([GitHub docs](https://docs.github.com/en/actions/concepts/runners/larger-runners)) | Paid | **Never.** Code refuses (`GITHUB_ACTIONS=true`) |
| L1 manual: bot writes a signal card, Akhil taps the order in the broker app | Not needed (not an API order) | ₹0 | **Use now** (`PLAN.md` L1) |
| Dhan Cloud (strategy runs on Dhan's servers) | Not needed: "Dhan Cloud deployments are not subject to the Static IP requirement" ([Dhan FAQ](https://dhan.co/support/platforms/dhanhq-api/is-a-static-ip-required-for-dhan-cloud/)) | Pay-per-use, no free allowance listed ([Dhan charges FAQ](https://dhan.co/support/platforms/dhanhq-api/what-are-the-charges-for-deploying-my-algo-on-dhan-cloud/)); exact ₹ **unverified** (Estimator needs a login) | **First API route.** Provider page only (no second source found today) |
| Oracle Cloud Always Free VM + its public IP | Yes (one public IP per micro VM) | Always Free compute + 10 TB/month out ([Oracle docs](https://docs.oracle.com/en-us/iaas/Content/FreeTier/resourceref.htm)); **needs a credit/debit card** for sign-up verification ([Oracle FAQ](https://www.oracle.com/in/cloud/free/faq/)), so not "free" by our rule 8 | Backup only, with Akhil's yes. Risk: Oracle reclaims "idle" VMs (CPU p95 < 20% over 7 days); a bot that runs 1 min a day looks idle, and a lost VM = lost IP = a week before a new IP can be whitelisted |
| Paid Indian VPS / ISP static IP | Yes | ₹300–800/month in `PLAN.md` L2: **unverified** today | Not at ₹5–10k capital |

## 3. Tested plan (what the code does now)

`src/livetrade/broker.py` `route_blockers()` runs inside every live adapter before keys are read:

1. `GITHUB_ACTIONS=true` → refused, for every broker (Indian and crypto).
2. Indian brokers (Fyers, Dhan) → refused unless `LIVE_STATIC_IP` is set **and** equals this machine's egress IP (read from api.ipify.org; unreadable = refused, fail closed).
3. Only Dhan may skip step 2, and only with `KALPA_ROUTE=dhan-cloud` (set by `deploy/dhan-cloud/main.py`).

Tests (`tests/test_livetrade.py`): wrong IP, unknown IP, unset IP, Actions env, Fyers trying the Dhan Cloud skip → all refused; whitelisted IP and Dhan Cloud → start. 07-trading pytest: 336 passed (also with `GITHUB_ACTIONS=true` for the live suites).

## 4. Found while checking

- Our Dhan adapter sends `MARKET` orders. NSE FAQ 11 says market orders are not allowed for algo orders, so live API orders would be rejected or converted. New item **A359**: send marketable LIMIT orders with a price cap instead.
- K155 (free-model draft) had every rule "unverified"; replaced by this page.

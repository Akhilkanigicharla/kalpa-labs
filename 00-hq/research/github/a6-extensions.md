# a6: b4 Extensions (freemium MV3 Chrome extension), GitHub research

Agent 6 of 8 · 2026-10-13 · checked with shallow clones and the npm registry. The GitHub API was blocked, so star counts are approximate and come from public pages or general knowledge.

## Summary
WXT (MIT, last commit 2026-10-11, about 2.86M npm downloads a month) is the clear framework choice. We scaffolded it non-interactively, built it in about 1 s to a 68 KB MV3 bundle, and loaded it in headless Chromium through Playwright, where a working freemium gate (5 free uses a day, then PRO) passed every check. For payments, ExtensionPay is the easiest option, but it depends on Stripe, which has accepted new Indian accounts by invite only since May 2024. Its licence is also unclear (the LICENSE file says LGPL-3.0, package.json says AGPL-3.0-or-later). The India-friendly path is a merchant of record: Dodo Payments has public licence-key activate/validate endpoints, so no secret key ships in the extension, and its SDK is Apache-2.0. Lemon Squeezy is the fallback, with payouts to India through PayPal. Test with Playwright `launchPersistentContext` and `--load-extension`, and publish with `chrome-webstore-upload-cli` from GitHub Actions. All of this runs on free tiers.

## Shortlist

| # | Repo / package | What | Stars (approx) / npm per month | Last commit | Licence | Fit 1–5 | Verdict | Why |
|---|---|---|---|---|---|---|---|---|
| 1 | [wxt-dev/wxt](https://github.com/wxt-dev/wxt) `wxt@0.21.4` | MV3 framework (Vite, file-based entrypoints, storage API, zip, Firefox) | ~9k / 2.86M | 2026-10-11 | MIT | 5 | **ADOPT** | Most active project. Init and build are fast and run without prompts. Typed `storage.defineItem` makes a freemium gate easy. |
| 2 | [dodopayments/dodopayments-typescript](https://github.com/dodopayments/dodopayments-typescript) `dodopayments@2.54.2` | MoR SDK with licence keys, subscriptions and checkout | small / 453k | 2026-10-10 | Apache-2.0 | 5 | **ADOPT** | India-oriented MoR. Licence `activate/validate/deactivate` are public endpoints that can be called from the extension. Fees reported at about 4% + $0.40, plus surcharges for international cards (third-party review; check the pricing page). |
| 3 | [microsoft/playwright](https://github.com/microsoft/playwright) `playwright@1.64.0` | E2E testing, loads unpacked extensions | ~80k / 303M (@playwright/test) | active | Apache-2.0 | 5 | **ADOPT** | Verified: service worker detected, popup tested, storage changed from the SW in headless mode. |
| 4 | [fregante/chrome-webstore-upload-cli](https://github.com/fregante/chrome-webstore-upload-cli) `4.0.2` | Uploads and publishes to the Chrome Web Store from CI | ~400 / 529k | 2026-10-05 | MIT | 4 | **ADOPT** | Lets GitHub Actions ship releases without the Akhil PC. |
| 5 | [aklinker1/webext-core](https://github.com/aklinker1/webext-core) `@webext-core/messaging@4.0.0` | Typed messaging and storage helpers (same author as WXT) | ~300 / 444k | 2026-08-08 | MIT | 4 | **ADOPT** (when needed) | Type-safe messages between popup and background and content scripts. |
| 6 | [crxjs/chrome-extension-tools](https://github.com/crxjs/chrome-extension-tools) `@crxjs/vite-plugin@3.0.0` | Vite plugin that takes manifest.json as the source | ~3.5k / 1.78M | 2026-10-06 | MIT (packages/vite-plugin/LICENSE) | 3 | LEARN | Works (built and loaded below), but you assemble more yourself than with WXT. Good if a plain Vite app is ever wanted. |
| 7 | [Glench/ExtPay](https://github.com/Glench/ExtPay) `extpay@3.1.2` | ExtensionPay client (Stripe-based payments for extensions) | ~600 / 3k | 2026-10-06 | **Unclear**: LICENSE says LGPL-3.0, package.json says AGPL-3.0-or-later | 2 | LEARN / AVOID for now | Best payments API and UX to copy (`getUser().paid`, trials, login page). It needs a Stripe account, which is invite-only in India, and the AGPL tag is a red flag under our licence rule. |
| 8 | [lmsqueezy/lemonsqueezy.js](https://github.com/lmsqueezy/lemonsqueezy.js) `4.0.0` | MoR SDK with licence-key API | ~700 / 560k | 2024-11-05 | MIT | 3 | LEARN (fallback MoR) | Indian sellers without Stripe get payouts through PayPal only (LS docs). The SDK looks unmaintained since 2024. Fee 5% + 50c. |
| 9 | [PlasmoHQ/plasmo](https://github.com/PlasmoHQ/plasmo) `plasmo@0.90.5` | React-first extension framework | ~12k / 2.70M | **2025-05-17** | MIT | 2 | AVOID | Repo has had no commits for about 17 months. `create-plasmo` blocked on an interactive prompt even with CI=1. |
| 10 | [Jonghakseo/chrome-extension-boilerplate-react-vite](https://github.com/Jonghakseo/chrome-extension-boilerplate-react-vite) | React + Vite + Turborepo MV3 boilerplate | ~4k / n/a | 2025-09-10 | MIT | 2 | LEARN | Heavy monorepo, too much for a low-RAM, 1-hour-a-day setup. Useful for i18n and HMR patterns. |
| 11 | [aklinker1/vite-plugin-web-extension](https://github.com/aklinker1/vite-plugin-web-extension) `4.5.1` | Older Vite plugin from the WXT author | ~700 / 145k | 2026-04-06 | MIT | 1 | AVOID | Superseded by WXT. |
| 12 | [extension-js/extension.js](https://github.com/extension-js/extension.js) | Zero-config extension CLI | ~4k / small | 2026-10-10 | MIT | 2 | LEARN | Active, but the npm package `extension.js` shows almost no downloads (the CLI is published under another name). Less proven. |

Other candidates screened (more than 25 in total): webextension-polyfill (MPL-2.0, 8.3M/mo; WXT already provides `browser`), web-ext (MPL-2.0, used by WXT for Firefox), @plasmohq/storage, @paddle/paddle-js (Paddle MoR, Apache-2.0, heavier KYC), refined-github, darkreader and uBlock Origin (UX references only; Dark Reader and uBO are GPL, so **learn from them, don't copy**), fregante/Awesome-WebExtensions (discovery list), the "Plasmo vs CRXJS vs WXT 2026" comparisons on dev.to and merginit, and Stripe India docs.
**Review mining:** no allowed open-source scraper was adopted. Chrome Web Store reviews have no official API and its ToS forbids scraping. The allowed approach is to read the 1–3★ reviews of 20–30 target extensions by hand (about 15 min/day), paste them into a Google Sheet, and cluster them with Claude.
**Privacy policy:** no maintained OSS generator worth adopting. Write a 1-page policy by hand (what goes in `chrome.storage`, no data sale, contact email) and host it free on Netlify or GitHub Pages. The CWS "Limited Use" disclosure has to match the policy.

## Tried it (real commands and results)
Environment: Node 22.22.0, npm 10.9.4, Chromium build 1194 at `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`.

1. **WXT scaffold (no prompts):**
   `CI=1 npx -y wxt@0.21.4 init wxt-demo -t vanilla --pm npm` created the project in 26 s.
   `npm install` added 428 packages in 30 s. `npm run build` reported "Built extension in 536 ms", giving `.output/chrome-mv3` at 68 KB with a valid MV3 manifest (`service_worker: background.js`, popup, content script).
2. **Freemium gate:** replaced the popup with `storage.defineItem('local:usage')` and `storage.defineItem('local:isPro')`, allowing 5 free uses a day, and added `permissions:['storage']` in `wxt.config.ts`. Rebuild took 814 ms and `tsc --noEmit` passed.
3. **Playwright, headless:** `npm i playwright@1.64.0` with `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1`, then `chromium.launchPersistentContext('', {executablePath, headless:true, args:['--disable-extensions-except=<dir>','--load-extension=<dir>']})`. Output:
   ```
   service worker: chrome-extension://pbiacg.../background.js
   initial: Free uses left today: 5
   after 6 clicks: Limit reached - upgrade
   after setting isPro: PRO: unlimited      (set via sw.evaluate(() => chrome.storage.local.set({isPro:true})))
   ```
4. **CRXJS v3:** a hand-made project with `vite@7` and `@crxjs/vite-plugin@3.0.0` (44 packages, `defineManifest`) built in 195 ms. Playwright loaded it: `sw: .../service-worker-loader.js`, `popup: CRX popup ok, n=0`.
5. **Plasmo:** `CI=1 npx create-plasmo@latest plasmo-demo --with-src` stopped at the interactive "Extension description" prompt. We did not build it, given the stale repo.
6. **Licence and last-commit check:** shallow clones of the 11 repos above, then `git log -1 --format=%cs` and a read of LICENSE and package.json. This is where the ExtPay LGPL vs AGPL mismatch showed up. All clones and trial projects have been deleted.

## Recommended stack (versions checked 2026-10-13)
- **Framework:** `wxt@0.21.4` (vanilla TS template; add Preact or React only if the UI needs it), `typescript@^5.9`, `vite@^8` (from the template).
- **Storage and messaging:** WXT built-in `storage`, plus `@webext-core/messaging@4.0.0` when needed.
- **Payments and licensing:** Dodo Payments MoR with licence keys. The extension calls public `/licenses/activate` and `/licenses/validate` (no API key), caches `isPro` in `chrome.storage.local`, and revalidates every 24–72 h. Use the `dodopayments@2.54.2` SDK only server-side, for example in a Supabase edge function webhook. Fallback: Lemon Squeezy with PayPal payouts. Avoid Stripe and ExtensionPay unless a Stripe India invite exists.
- **Testing:** `playwright@1.64.0` using the pre-installed Chromium through `executablePath`. Run it in GitHub Actions.
- **Release:** `wxt zip`, then `chrome-webstore-upload-cli@4.0.2` in GitHub Actions. The CWS one-time $5 developer fee is the only cost.
- **Hosting (policy and landing page):** Netlify or GitHub Pages (free).

## Concrete next quests for b4 (at most 6)
1. **Idea mining (3 days, 15 min/day):** read the 1–3★ reviews of 25 popular extensions in one niche, log them in a Sheet, and pick the top 3 recurring pains. Read by hand only; no scraping.
2. **Scaffold the real extension in Codespaces** with `npx wxt@0.21.4 init` and port the 5-a-day freemium gate tested above.
3. **Sign up for Dodo Payments** (check India KYC and payouts on the pricing and onboarding pages), create a test-mode product with licence keys (3 activations), and wire up the activate and validate calls.
4. **Add the Playwright smoke test** (free limit, then upgrade, then PRO) and a GitHub Actions workflow: build, test, zip.
5. **Write the privacy policy and a single-purpose description**, host them on Netlify, and pay the $5 CWS developer registration.
6. **Automate publishing** with `chrome-webstore-upload-cli` behind a manual-approval GitHub Actions job, then submit v0.1.

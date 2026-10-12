# P4 · b4 Extensions — plan

Planning agent P4 · 2026-10-13 · follows `00-hq/plans/PLANNING-BRIEF.md`, uses research `00-hq/research/github/a6-extensions.md`. Code will live in `04-extensions/src/`, decisions in `04-extensions/docs/`.

**Pick: "Tab Lifeboat" (working name)**: a tab and session saver that keeps backing up your tabs, so they can't be lost the way OneTab and Session Buddy users keep losing theirs. Free covers saving and restoring. Pro adds automatic backups and history.

---

## 1. Verdict

We make money from a one-time Pro licence ($12 a year or $29 lifetime; ₹499 / ₹1,199 by UPI), sold through Dodo Payments as merchant of record. The extension checks the key against Dodo's public licence endpoints, so there are **no servers to run and the cost to serve is ₹0**. The only spend is the $5 Chrome Web Store fee. Demand is proven: OneTab has 2M users and Session Buddy 1M, and both have users who lost all their saved tabs. Revenue comes slowly because store search has to bring installs first.

| ₹ per month (₹88 = $1 assumed) | Low | Likely | High |
|---|---|---|---|
| Month 1 (build + review) | 0 | 0 | 1,000 |
| Month 3 | 0 | 2,500 | 8,000 |
| Month 6 | 2,000 | 10,000 | 30,000 |
| Month 12 | 5,000 | 25,000 | 80,000 |

Basis: new installs grow from 300 a month to about 2,000 a month by month 12, and 1–2% of new installs buy, at about $15 net per sale. **The biggest risk is discovery.** OneTab now has its own encrypted cloud sync, and if store search never surfaces a new tab manager, nobody buys. The kill dates in §7 catch this early.

## 2. Customer & offer

### How the idea was picked: 5 candidates, each from real complaints

Each candidate is scored 1–5, where 5 is best. For competition and policy risk, 5 means little competition and low risk. **Any score of 1 vetoes the idea.**

| # | Idea | Evidence (real complaints and requests) | Demand | Competition | Build time | Payment willingness | Policy risk | Total |
|---|---|---|---|---|---|---|---|---|
| A | **Tab saver with automatic backup** | OneTab: 2M users, 986 one-star ratings. One review: "One Tab consistently loses the links of the previous tabs used" (Jul 2024). OneTab's own help page says "Do not uninstall and reinstall OneTab unless you are happy to wipe all of your OneTab data." Session Buddy, 1M users: "After auto updating to v4, all [Unnamed sessions] were gone" (Google Group). Another reviewer had "needing it to take backups and it simply not doing it" (1★, Sep 2026). A Chrome Help thread asks how to recover lost OneTab data. | 5 | 2 | 4 | 3 | 4 | **18** |
| B | Local-first text expander | Text Blaze has 800K users at 4.9★ with a "Limited snippets" free plan, and Pro costs $2.99–3.49 a month. Rivals write "Magical alternatives" posts after Magical's changes. | 4 | 2 | 3 | 4 | 3 (needs all-sites access; ExtScope rates Text Blaze HIGH) | 16 |
| C | Google Meet attendance for teachers | Attendance for Google Meet (30–40K users): "It does not work at all today" (Apr 2024), "suddenly stopped taking the attendance of my class" (Oct 2022), "I am not able to export the attendance anymore". | 3 | 3 | 2 (reads Meet's page layout, which keeps changing; that is why it breaks) | 3 | 3 (student names) | 14 |
| D | ChatGPT/Claude chat exporter | ChatGPT Exporter has 200K users at 4.9★, plus dozens of free clones and "how to export" guides. | 4 | 1 | 3 | 2 | 3 | 13 (veto) |
| E | WhatsApp Web bulk sender (big Indian demand) | Socket found 131 copy-paste "spamware" extensions that evade WhatsApp's anti-spam limits, and those limits can get users banned. | 5 | 2 | 3 | 5 | **1** | veto |

**Why A wins:** it uses only official Chrome APIs (`tabs`, `tabGroups`, `storage`, `alarms`), so it doesn't break when a website changes. C's fatal problem is that it does. The pain behind A is data loss, which people pay to avoid; Workona already sells "90-day session backups" in its Pro plan. A also sells worldwide in dollars, with no WhatsApp or Meta risk.

### The offer

**Promise:** "Your tabs, backed up automatically. Restore any day, on any device. We never see them."

| | Free (forever) | Pro |
|---|---|---|
| Save all tabs / window / tab group in 1 click, named sessions, search | ✅ unlimited | ✅ |
| Restore with **tab group names and colours** (a gap reviewers point to in Session Buddy) | ✅ | ✅ |
| **Import from OneTab and Session Buddy** (the way switchers move in) | ✅ | ✅ |
| Crash-safety auto-snapshots | Last 3 | Every 5 min, **90-day history**, restore any point |
| Automatic backup file | Manual export | Daily to **your own Google Drive** (`drive.file` scope) or Downloads folder |
| Restore on a new PC / after a reinstall | From a manual file | 1 click from Drive |
| Duplicate and stale-tab cleanup, "where did this tab go" timeline | — | ✅ |

**Price ladder:**

| Plan | Price | Notes |
|---|---|---|
| Free | $0 | No account, nothing leaves the device |
| Founding Lifetime (first 50 buyers only, count shown honestly) | $19 / ₹899 | Gets the first 10 customers and reviews |
| Pro Yearly | $12 / ₹499 | 365-day licence key, **not** an auto-renewing subscription (avoids Dodo's +0.5% subscription surcharge and India's recurring-payment mandate friction) |
| Pro Lifetime | $29 / ₹1,199 | 3 devices per key |

**Why they buy now:** they have just lost tabs, or just read that a reinstall wipes OneTab. The upgrade prompt appears right after an import from OneTab or Session Buddy: "You just moved 1,240 tabs. Keep them safe automatically?"

### Competitors

| Product | Price | Where we beat it |
|---|---|---|
| Toby | Free up to 60 tabs (needs an account); $4.50/mo billed yearly, $6 monthly | No account and no cap; one-time price |
| Workona | Free tier plus Pro with 90-day session backups (price not shown on its public page) | Simpler; backups go to *your* Drive, not ours |
| SupaSidebar | "Believer" lifetime $77 (rising to $99) | A quarter of the price; focused on one job |
| OneTab / Session Buddy | Free (OneTab adds encrypted sync) | Tab-group fidelity, version history, imports from both |

## 3. Unit economics

**Dodo fees** (checked on dodopayments.com/pricing, 2026-10-13): 4% + $0.40 per card payment, plus 1.5% for cards outside the US. Indian UPI and RuPay payments cost 4% + 15¢. Refunds cost $1 and disputes $30.

| Sale | Fee | Net | Margin |
|---|---|---|---|
| $12 yearly, international card | $1.06 | $10.94 | 91% |
| $29 lifetime, international card | $2.00 | $27.00 | 93% |
| ₹499 yearly, UPI | ≈ ₹33 | ≈ ₹466 | 93% |

- **Cost to serve per customer per month: ₹0.** The extension runs on the user's PC. Backups go to the user's own Drive. The licence check is a free public Dodo endpoint. The landing and privacy pages run on GitHub Pages, and builds and tests run on GitHub Actions free minutes.
- **Where the free tiers run out:** effectively never at this scale. Actions gives 2,000 free minutes a month for a private repo, and one CI run takes under 3 minutes. The real cost is support time.
- **Payout costs:** Dodo pays out from a USD wallet (**INR payouts have been discontinued**). Pages conflict on fees: the pricing page says "USD SWIFT payouts (non-US businesses) $25", while the FAQ says a $5 fee applies under $1,000. Set the payout threshold to **$200** so fees stay at or below 12.5%, and raise it once volume grows. The Indian bank may also charge an inward-remittance fee; ask for an e-FIRA for each payout.
- **Break-even:** 1 sale covers the $5 fee. 10 sales a month (≈ ₹12,000) is the point where an hour a day is worth it.
- **Tax note:** Dodo as merchant of record handles customer-side sales tax. Kalpa's income from Dodo is foreign inward remittance. **Ask a CA once** about GST: whether it counts as an export of services, whether an LUT is needed, and the registration threshold. Do this before crossing about ₹1 lakh a year.

## 4. Go-to-market

### Store listing and SEO (sets up every channel below)

- **Name (≤ 45 characters, no keyword stuffing):** "Tab Lifeboat – Session Saver & Auto Backup". The name must be unique: "TabSafe" is already taken, so quest E1 runs a name check.
- **Summary (≤ 132 characters):** "Save all tabs and tab groups in one click. Automatic backups so a crash, update or reinstall never wipes your saved tabs."
- **Description:** problem → 5 feature bullets → privacy line → plain statement of what Pro costs (CWS requires paid features to be disclosed before install; we name ourselves as seller and link the refund terms). Use each key phrase ("tab manager", "session manager", "OneTab alternative", "save tabs") **at most twice**. CWS counts more than 5 repeats as spam.
- **Assets:** 5 screenshots at 1280×800, captured automatically by Playwright from the real UI. A 440×280 promo tile in white and blue. A 30-second YouTube demo of the import-and-restore flow.
- **Localize** the summary into es, pt-BR, ru and hi in Month 3. Several OneTab complaints are in Spanish and Russian.
- **Web SEO:** 3 honest help articles on the GitHub Pages site: "OneTab lost my tabs: how to recover", "Back up Session Buddy before it breaks", "Save Chrome tab groups with names and colours". These are the exact searches losers make, and competitors already rank for them.

### First 10 customers (20 min a day)

| Day block | Action | Daily quota |
|---|---|---|
| Launch week | Founding-Lifetime offer, 50 seats. Post "I built…" in r/chrome_extensions, Show HN, Indie Hackers, Peerlist and Product Hunt (free). One a day, each written for that community. | 1 post |
| Every day | Search Reddit, the Chrome Help forum and the Session Buddy Google Group for "lost tabs" threads. Answer with **real recovery steps first**, then "I made a free tool that auto-backs up; I'm the developer." Follow each subreddit's self-promotion rule. | 2 helpful replies |
| Every day | Reply to every store review and support email within 48 h | All |
| Weekly | One SEO article or update post; one founding-buyer thank-you email asking (no incentive) for honest feedback | 1 |

Reply script outline: empathy → exact fix (export path or profile-folder restore) → how to prevent it next time → disclosure line + link. Never fake reviews, never use paid installs, never bulk-DM anyone.

### 10 → 100

Release a Firefox build (WXT builds it; listing on AMO is free) to roughly double the reach. Add the localized listings. Push the "Import from OneTab/Session Buddy" landing page. Add a "Share Tab Lifeboat" link in the restore success screen (no incentive). Once a sale arrives, post a monthly build-in-public update on Indie Hackers.

### Review → feature loop (weekly, 15 minutes)

1. Read new reviews of our listing, plus 1–3★ reviews of OneTab, Session Buddy, Toby and Tab Session Manager. Read by hand; **no scraping** (CWS has no review API). Paste them into the "b4 Reviews" Google Sheet.
2. Claude clusters them into pains, counts each, and suggests the top one as a quest.
3. Build it. Ship it with a changelog note: "You asked: …".
4. Reply to the reviewer that it shipped.
5. The uninstall page (`runtime.setUninstallURL`) shows a 1-question Google Form: "Why did you leave?" It collects no personal data.

## 5. Build plan (each quest ≤ 60 min of CEO time)

Stack from a6, all ADOPT picks: `wxt@0.21.4` (vanilla TS), WXT `storage`, `playwright@1.64.0`, `chrome-webstore-upload-cli@4.0.2`, and Dodo licence endpoints. The SDK `dodopayments@2.54.2` is used server-side only, if ever. **Permissions:** `tabs`, `tabGroups`, `storage`, `unlimitedStorage`, `alarms`. Pro asks for `downloads` / `identity` as **optional permissions** only when the user turns on backups. Never request `<all_urls>`.

### Week 1

| id | Quest | CEO action | Agent action | Done-check |
|---|---|---|---|---|
| E1 | Name and promise | Approve 1 of 3 names | Check CWS and web for name collisions; draft listing text | Name in `04-extensions/docs/decisions.md` |
| E2 | Scaffold | Open Codespace, run `npm run build` | `npx wxt@0.21.4 init 04-extensions/src -t vanilla`; port a6's freemium gate | `.output/chrome-mv3` builds; `tsc --noEmit` passes |
| E3 | Save/restore core | Load unpacked, save and restore 3 windows | Sessions in IndexedDB, tab groups restored with name and colour | Playwright test `save→close→restore` green in Actions |
| E4 | Dodo account | Sign up yourself with PAN and bank (no secrets in chat). Email support@dodopayments.com: "Are browser extensions accepted? USD payout to an Indian bank, e-FIRA?" | Draft the email; record the answer | Reply saved in `04-extensions/docs/dodo.md` |
| E5 | CWS developer account | Turn on Google 2-Step Verification; pay **$5**; choose the support email carefully (it can't be changed later) | Checklist and trader-declaration explainer | Dashboard opens |

### Weeks 2–4

| id | Quest | CEO action | Agent action | Done-check |
|---|---|---|---|---|
| E6 | Importers | Test with your own OneTab export | Parse OneTab text and Session Buddy JSON | Fixture tests pass on 1,000 tabs |
| E7 | Auto-snapshots | Approve the free and Pro limits | `alarms` every 5 min, last 3 for free, 90 days for Pro | Test: kill the browser, snapshot ≤ 5 min old |
| E8 | Licence gate | Create a test product with a licence key (lifetime: 3 activations; yearly: 365-day length) | `POST /licenses/activate` (stores `lki_` id), `/validate` every 72 h with 7 days of offline grace. Test whether CORS needs a `host_permissions` entry. | Playwright: free → enter test key → PRO → deactivate → free |
| E9 | Privacy policy and landing page | Read and approve (10 min) | GitHub Pages site: policy, Limited Use statement, refund terms, 3 FAQ | URLs live; policy matches the dashboard data form |
| E10 | Listing assets | Approve screenshots | Playwright screenshots at 1280×800, promo tile, description | Assets in `04-extensions/store/` |
| E11 | Submit v0.1 | Click **Submit for review** | `wxt zip`; fill single-purpose and permission justifications | Status "Pending review" |
| E12 | CI publishing | Create the CWS API OAuth client; paste the secrets into GitHub **Secrets** yourself | Actions workflow: build → test → zip → upload behind manual approval | One release shipped from Actions |

**Privacy policy (one page, plain English):**
- **What:** tab titles, URLs and group names, kept on your device (IndexedDB). They are used only to save and restore your sessions.
- **Where:** they never reach our servers, because we have none. Pro backups go to *your* Google Drive through `drive.file` (we can see only files this extension made) or to your Downloads folder.
- **Licence checks:** your key and a device label go to Dodo Payments. Purchase data (name, email, payment) is handled by Dodo as merchant of record.
- **No** analytics, ads, sale or transfer of data.
- **Deleting data:** uninstalling deletes local data; Drive files stay yours to delete.
- **Contact:** a DPDP Act 2023 grievance contact (email) and response time; a changes log.
- **In-product consent:** a first-run screen states the same thing in 2 lines. CWS says local-only data must still be disclosed.

### Month 2

| id | Quest | CEO | Agent | Done-check |
|---|---|---|---|---|
| E13 | Drive backup (Pro) | Create a Google Cloud OAuth client; finish basic consent-screen verification (`drive.file` is non-sensitive) | `chrome.identity` + daily upload; restore picker | Restore on a second Chrome profile works |
| E14 | Go live on Dodo | Switch to live mode; set the payout threshold to $200 | Swap the endpoint to live; add a purchase-flow test | First real sale (₹ or $) |
| E15 | Launch week | Post 1 community post a day (drafts ready) | Write 5 posts, one per community, and the reply script | 5 posts live; installs logged |
| E16 | SEO articles | Approve | 3 articles plus internal links | Indexed in Search Console |
| E17 | Review loop starts | 15 min/week reading | Sheet plus clustering | First "You asked" changelog |

### Month 3

| id | Quest | CEO | Agent | Done-check |
|---|---|---|---|---|
| E18 | Firefox | Create an AMO account (free) | `wxt build -b firefox`; submit | Listed on AMO |
| E19 | Localize | Approve the hi summary | es, pt-BR, ru, hi listing strings | 4 locales live |
| E20 | Price step | Decide whether to end Founding Lifetime | Show remaining seats; switch to $29 | Price page updated |
| E21 | Top review fix | Approve | Build the top cluster item | Shipped with a reply to the reviewers |

**When a spend is worth it:** a domain (≈ ₹800/yr) after 20 paid customers. It makes Drive OAuth branding and the support email look trustworthy. Nothing else.

## 6. Agent swarm (registry.js style, unit `b4`)

```js
A({ id:"b4.reviews",  name:"Review Miner", unit:"b4", team:"product", mission:"Cluster pasted 1–3★ reviews (ours + 4 rivals) into pains; propose the top quest.", trigger:{cron:"weekly:sun"}, inputs:["b4 Reviews sheet"], runs_as:"claude", tokens:4000, kpi:"1 shipped 'You asked' per month", validator:{checks:["quotes copied by hand, never scraped","counts add up"]} }),
A({ id:"b4.builder",  name:"Extension Builder", unit:"b4", team:"build", mission:"Implement quests in 04-extensions/src with WXT.", trigger:{event:"quest approved"}, runs_as:"claude", tokens:15000, kpi:"Quest done-checks pass", validator:{checks:["no new permission without justification","no remote code","tsc clean"]} }),
A({ id:"b4.qa",       name:"Playwright QA", unit:"b4", team:"build", mission:"Load the unpacked build headless; test save/restore/import/licence.", trigger:{event:"push"}, runs_as:"code", code:"04-extensions/src/tests/e2e.spec.ts", tokens:0, kpi:"0 red builds shipped", validator:{checks:["1,000-tab fixture","tab groups keep name+colour"]} }),
A({ id:"b4.release",  name:"Store Releaser", unit:"b4", team:"build", mission:"wxt zip → chrome-webstore-upload-cli after manual approval.", trigger:{event:"tag v*"}, runs_as:"code", code:".github/workflows/b4-release.yml", tokens:0, human_needed:true, kpi:"Release ≤ 10 min of CEO time", validator:{checks:["version bumped","changelog present"]} }),
A({ id:"b4.policy",   name:"CWS Policy Guard", unit:"b4", team:"build", mission:"Check manifest, listing and privacy policy against CWS policies before every submit.", trigger:{event:"before submit"}, runs_as:"claude", tokens:2000, kpi:"0 rejections", validator:{checks:["paid features disclosed","keyword ≤ 2 repeats","policy matches data form","Limited Use statement"]} }),
A({ id:"b4.listing",  name:"Listing & SEO Writer", unit:"b4", team:"growth", mission:"Store text, localized summaries, 1 help article a week.", trigger:{cron:"weekly:wed"}, runs_as:"claude", tokens:4000, kpi:"Store search impressions up month on month", validator:{checks:["no superlatives or rival bashing","summary ≤ 132 chars"]} }),
A({ id:"b4.community",name:"Help-First Replier", unit:"b4", team:"growth", mission:"Find 'lost my tabs' threads; draft fix-first replies for Akhil to post.", trigger:{cron:"daily"}, runs_as:"human", tokens:1500, human_needed:true, kpi:"2 replies/day, ≥1 install/day from referrals", validator:{checks:["real fix first","maker disclosed","subreddit rules followed"]} }),
A({ id:"b4.support",  name:"Support & Review Responder", unit:"b4", team:"growth", mission:"Draft replies to every review/email within 48 h; refunds per policy.", trigger:{cron:"daily"}, runs_as:"claude", tokens:1500, kpi:"100% answered ≤ 48 h", validator:{checks:["never asks for a better rating in exchange for anything"]} }),
A({ id:"b4.money",    name:"Payout Reconciler", unit:"b4", team:"finance", mission:"Match Dodo sales → payouts → bank credit + e-FIRA; hand to b6 FinOps.", trigger:{cron:"monthly:5"}, runs_as:"claude", tokens:2000, human_needed:true, kpi:"Every payout has an e-FIRA", validator:{checks:["fees match the pricing page","no keys or bank numbers in the repo"]} }),
```

## 7. Metrics & kill criteria

**Weekly numbers** (from the CWS dashboard, the Dodo dashboard and the Sheet):

| Number | Target by month 3 | Target by month 6 |
|---|---|---|
| New installs a week | 75 | 200 |
| Weekly active users | 200 | 1,000 |
| Store rating | ≥ 4.5 | ≥ 4.6 |
| Upgrade-screen views → purchases | 3% | 4% |
| Paid sales a week | 1 | 3 |
| Refund rate | < 5% | < 5% |
| Reviews answered within 48 h | 100% | 100% |

**Kill and pause rules:**
- **2027-01-31:** if total installs are under 300 **and** sales are under 3, pause b4. Leave it live in maintenance mode (bugs only) and move the hour to the best-performing world.
- **2027-04-30:** if revenue is under ₹5,000 a month, keep it in maintenance mode only.
- **Any time:** a CWS policy strike that can't be fixed in one quest means stop and rethink.

## 8. What I need from Akhil

- [ ] Approve the pick (Tab Lifeboat) and choose 1 of 3 names (E1).
- [ ] Choose the permanent CWS developer email. Use a support Gmail rather than your personal one, because it can never change.
- [ ] Turn on Google 2-Step Verification and pay the **$5** CWS fee yourself.
- [ ] Decide what to enter in the CWS trader declaration: use the Udyam business address, not your home address.
- [ ] Sign up for Dodo Payments yourself (PAN, bank account in your name) and send the support email from E4.
- [ ] Ask your bank about USD inward-remittance charges and e-FIRA. Ask a CA one GST/LUT question before ₹1 lakh a year.
- [ ] Month 2: create the Google Cloud OAuth client and the CWS API client. Put the secrets only into GitHub Secrets, **never in chat**.
- [ ] Approve prices: Founding $19 / ₹899, Yearly $12 / ₹499, Lifetime $29 / ₹1,199.

## 9. Sources

- Research a6: `00-hq/research/github/a6-extensions.md` (WXT, Dodo licence keys, Playwright, chrome-webstore-upload-cli; Stripe/ExtensionPay blocked)
- [Dodo Payments pricing](https://dodopayments.com/pricing) · [Dodo payout structure](https://docs.dodopayments.com/features/payouts/payout-structure) · [Dodo FAQ](https://docs.dodopayments.com/miscellaneous/faq) · [Dodo licence keys](https://docs.dodopayments.com/features/license-keys)
- [OneTab reviews (CWS)](https://chromewebstore.google.com/detail/onetab/chphlpgkkbolifaimnlloiipkdnihall/reviews) · [OneTab on ExtScope](https://extscope.org/extension/chphlpgkkbolifaimnlloiipkdnihall) · [OneTab troubleshooting](https://www.one-tab.com/troubleshooting) · [OneTab help (encrypted sync)](https://www.one-tab.com/help) · [Chrome Help: recover OneTab data](https://support.google.com/chrome/thread/49020169)
- [Session Buddy on ExtScope](https://extscope.org/extension/edacconmaakjimmfgnblocblbcdcpbko) · [Session Buddy troubleshooting](https://sessionbuddy.com/troubleshooting/) · [sessionbuddy-discuss group](https://groups.google.com/g/sessionbuddy-discuss) · [SupaSidebar: Session Buddy alternatives](https://supasidebar.com/blog/session-buddy-alternatives-2026) (competitor-written)
- [Toby pricing via SupaSidebar](https://supasidebar.com/blog/toby-alternatives-chrome-2026) · [Toolradar Workona vs Toby](https://toolradar.com/compare/workona-vs-toby) · [Workona pricing](https://workona.com/pricing/)
- [Text Blaze plans](https://blaze.today/plans/) · [Text Blaze on ExtScope](https://extscope.org/extension/idgadaccgipmpannjkmfddolnnhmeklj) · [Text Blaze: Magical alternatives](https://blaze.today/blog/magical-text-expander-alternatives/)
- [Attendance for Google Meet reviews (ExtScope)](https://www.extscope.org/extension/gioogehddfnceeihfoeencjbhggblkkd) · [ExtScope listing 2](https://www.extscope.org/extension/fdnipcdebaagjpicpbkildmcefflobhn)
- [ChatGPT Exporter (ExtScope card)](https://extscope.org/extension/ooleaojggfoigcdkodigbcjnabidihgi) · [Malwarebytes: 131 WhatsApp spamware extensions](https://www.malwarebytes.com/nl/blog/news/2025/10/over-100-chrome-extensions-break-whatsapps-anti-spam-rules)
- [CWS Program Policies](https://developer.chrome.com/docs/webstore/program-policies/policies) · [CWS User Data FAQ](https://developer.chrome.com/docs/webstore/user_data/) · [Limited Use](https://developer.chrome.com/docs/webstore/program-policies/limited-use/) · [Listing best practices](https://developer.chrome.com/docs/webstore/best-listing) · [Register developer account](https://developer.chrome.com/docs/webstore/register) · [$5 fee, 2026](https://extensionbooster.net/blog/chrome-web-store-developer-registration-fee-2026-guide/)
- [Google Drive API scopes (drive.file non-sensitive)](https://developers.google.com/workspace/drive/api/guides/api-specific-auth)
- Name check: ["Tabsafe" exists](https://chromeboard.com/extension/tabsafe-—-save-sync-tabs-defonmenmpedkbegdmafjckkmeolcdgo)

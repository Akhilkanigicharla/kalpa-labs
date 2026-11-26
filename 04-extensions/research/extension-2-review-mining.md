# Extension 2: evidence hunt, pass 1 (11 Nov 2026)

Akhil has two extension slots as a test. Slot 1 = Tab Lifeboat (built, in store review). Slot 2 must start from data, not from an idea (Akhil, 11 Nov: "review mining"). Nothing is chosen yet.

## What the data says about extensions in general (read today, second-hand unless marked)
| Fact | Number | Source |
|---|---|---|
| Median users per Chrome extension | 18 | Exstats, March 2026, via konabayev.com |
| Extensions with 100 users or fewer | 70.4% | same |
| Extensions with more than 10,000 users | 2.63% | same |
| Extensions earning $0 a month (in one revenue dataset) | 57.1% | bigideasdb.com, 2026 |
| Average monthly revenue in that dataset | $295; top earner about $9,742 | same |
| Why people leave 1-star reviews (400 coded) | "does not work" 43.0%; trust/ads/permissions 13.8%; pricing or paywall 11.5%; missing feature or bad UX 9.5% | extensionbooster.net, study dated 21 Oct 2026, 7,355 reviews from 798 listings |
| Free-to-paid conversion usually quoted | 1 to 5% | nichecheck.com (vendor blog) |

## The strongest lead: extensions Google removed
- **Verified on Google's own page:** all remaining Manifest V2 extensions were removed from the Chrome Web Store on 31 Aug 2026 (developer.chrome.com MV2 support timeline; also 9to5Google, AlternativeTo, AdGuard's blog).
- **Size of the gap:** one scrape counted 84,504 Manifest V2 extensions with 426 million users in total (Ian Nuttall's list on Gumroad, scraped around mid 2024; one source, numbers will have changed).
- Why it matters: those users already proved they wanted the tool. Where the author never shipped a new version, nothing replaces it. That is demand we can measure before building.
- A solo developer reports about $1,000 a month from simple, clearly named utilities (bulk delete tools), sold for a small fee (goodreads/Starter-Story style interview, 2024; one source).

## What pass 1 could NOT get
- The actual list of removed extensions with user counts. Sources found: the Gumroad CSV (free but needs an email at checkout, and is from 2024); Crawlora's dataset API (needs an API key; price unverified); a Medium analysis of 9,650 expired extensions (behind a paywall).
- So no candidate has numbers yet.

## Pass 2 (roadmap A217)
Build a shortlist of 5 candidates. Each row needs: users before removal, rating, date last updated, whether a Manifest V3 successor exists today (searched in the store), the top complaints in its 1-star reviews, how it could charge, and two sources. Only public pages; no logins. Rule out anything that needs heavy permissions, ad blocking (Manifest V3 limits it) or another company's login. Show Akhil the 5 before any code.

## Pass 1b (12 Nov 2026): where extension money actually is
Akhil, 12 Nov: "next one: solve a real problem people from all over the world will pay for."

| Finding | Source |
|---|---|
| 112 revenue-verified extensions: 57.1% earn $0, only 6.3% clear $1,000/month. Top-earning categories: social account management, AI writing/rewriting, marketplace seller automation, academic assistance. Users are 4 to 1 consumer over business. Prices seen: about $9 one-off unlock to about $40 lifetime; subscriptions single to low double digits per month. | bigideasdb.com, snapshot 12 Sep 2026 |
| Strongest revenue sits "close to expensive work: selling, prospecting, ecommerce research, outreach and professional audience growth". SuperX: $23K MRR with about 10,000 Chrome users. GMass about 400,000 users. | stealwhatworks.com, Sep 2026 |
| Public revenue reports: GMass (Gmail mail merge) about $130K/month; Closet Tools (Poshmark reseller automation, $30/month) about $42K/month; CSS Scan (developer tool, one-time $69) $100K+ total. Dates 2020 to 2024: historical, not current. | extensionpay.com, chromegoldmine.com (both cite IndieHackers) |
| Chrome Web Store payments were shut down (2020/2021); every paid extension runs its own billing (licence key or account). ExtensionPay charges 5%. | profitable.app, crxpay.io, konabayev.com |
| Tab managers typically sit at $4 to $5/month and need about 1,000 paying users to be a business. | crxpay.io (payments vendor) |

**What this means for slot 2:** the money is in tools for people whose time is worth money at work (sellers, recruiters, marketers, freelancers), not in general consumer utilities like Tab Lifeboat. Revenue per user is the deciding number, not installs.

**Kalpa rules that cut the list:** no tool that scrapes LinkedIn, Instagram or Google Maps, sends bulk messages, or automates another site in a way its terms forbid (rule 4, rule 10). Closet Tools-style posting bots and LinkedIn automation are out.

**Pass 2 (A217, updated):** pick 5 concrete candidates inside the 4 earning categories that pass our rules (for example: a helper for marketplace sellers that reads their own listing page; a platform-specific AI writing helper on free models; a study tool that is not a cheating tool). For each: 2+ paying competitors with price and users, their top 1-star complaints, what we would do better, price, and two sources. Show Akhil before any code.

## Pass 2 (27 Nov 2026, A217): the biggest removed extensions, checked
Searched and read today (Firecrawl, public pages only, no logins). Main list: Exstats "MV2 Purge in Numbers" (5 Sep 2026), which says Chrome removed **44,158 MV2 listings with 92.3 million users on 9–10 Oct 2025**, ten months before Google's 31 Aug 2026 date; 6,808 of them had zero users. Second sources per row below. "unverified" = only one source or not found.

| # | Extension (removed) | Users | Rating | Last update | Working replacement today? | Top 1-star complaint | Way to charge | Sources | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Office – Enable Copy and Paste | 9,000,000 | 2.1 | 10 Feb 2022 | Not needed in most cases: it existed only to let Office web use the clipboard (unverified that Office web works without it today) | "Microsoft installed this without my permission" (debugbear) | None: people never chose it | exstats.com/blog/mv2-purge-in-numbers; debugbear.com/blog/chrome-extension-statistics; support.google.com/chrome/thread/329265459 | SKIP |
| 2 | Postman (Chrome app) | 1,000,000 | 4.7 | 11 Jul 2022 | Yes: Postman's own desktop/web app (company product) | unverified | None for us: another company's product | exstats (above); Postman replacement = one source only (unverified) | SKIP |
| 3 | Proxy SwitchyOmega | 1,000,000 | 4.6 | 22 Nov 2020 | Yes: ZeroOmega ("SwitchyOmega V3"), rated 4.7 on Firefox Add-ons | "disabled in Chrome Web Store and not enabling" (GitHub issue #2243) | Weak: free open-source fork already exists | exstats; github.com/FelisCatus/SwitchyOmega/issues/2243; addons.mozilla.org ZeroOmega reviews | SKIP |
| 4 | JSON Viewer | 800,000 | 4.6 | 23 Dec 2020 | Yes: JSON Viewer Pro and many others; Chrome itself pretty-prints JSON | unverified | Weak: many free tools | exstats; digifix.com.au/best-chrome-extensions-for-web-developers | SKIP |
| 5 | Padlet | 700,000 | 4.4 | 8 Jan 2019 | Yes: Padlet Mini, rebuilt by Padlet itself | unverified | None for us: another company's product | exstats; padlet.blog/padlet-mini; Chrome Web Store "Padlet Mini" listing | SKIP |

Others in the Exstats top 15, ruled out by our rules: uBlock Origin, Touch VPN, Hotspot Shield, Runet unblocker (ad blocking / VPN / proxy-bypass), Dropbox, Evernote, Microsoft Power Automate, Save to Facebook (another company's product or login), Vysor (700k, 3.3; phone mirroring needs a desktop app, replacement status unverified), Internet-Start (new-tab page).

**What this means (plain):** the big removed extensions are not open gaps. Each one is a company product that already shipped a new version, has a free open-source fork, or is no longer needed. The real gaps are in the long tail (thousands of small tools with 1k–50k users), and no free public list of those with user counts was found today (Exstats' full data needs an account; price unverified).

**Recommendation for Akhil's pick:** drop the "rebuild a removed extension" route and use Pass 1b's money rule instead: a tool for people whose time earns money (sellers, recruiters, marketers, freelancers) that works only on their own pages. Akhil chooses one route; no code until then.

Free agents: K140 and K148 were rejected (free models cannot browse, so every number was unverified); this pass was done by Claude with live search.

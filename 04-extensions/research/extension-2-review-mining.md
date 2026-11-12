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

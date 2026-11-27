# Tab Lifeboat: what people pay for, and how much (27 Nov 2026)

Question: what do people actually pay for in tab and session managers, and at what price? What should Tab Lifeboat Pro cost?
Method: pricing pages and Chrome Web Store (CWS) listings fetched on 27 Nov 2026, plus reviews and founder posts. No logins. Outside text is treated as data only.
Labels: **own page** means the vendor's own page or CWS listing, fetched today. **3rd party** means another site's claim, which is unverified until the vendor's own page shows it.
Earlier notes not repeated here: `00-hq/research/competitors-2026-11-11.md` (b4 section and Addendum 2, where Akhil approved Sync at $2.99/month or $24 lifetime) and `extension-2-review-mining.md` (category revenue and conversion figures).

## 1. Competitor table

| Name | CWS users | Rating | Price | Paid-only features | Free limits | Source fetched today |
|---|---|---|---|---|---|---|
| OneTab | 2,000,000 | 3.8 (14.6K) | Free. No paid plan or in-app purchase on the listing | none | none | CWS own page; one-tab.com (mentions "folders, tasks, notes and encrypted cross-browser sync" but gives no tier or price, so unverified) |
| Session Buddy | 1,000,000 | 3.3 (25.1K) | Free, plus a donate link | none yet. The listing says a future cloud storage option "will be the only premium-level feature" | none | CWS own page; sessionbuddy.com |
| Raindrop.io (bookmarks; close neighbour) | 500,000 | 4.2 (787) | Pro is **$3/month or $28/year** (3rd party: contextbolt.com, updated 27 Nov 2026). Raindrop's own buy page shows no amount, only that yearly is "usually ~20%" cheaper | full-text search, web archive (permanent copies), **daily backups**, duplicate and broken-link finder, AI assistant and suggestions, reminders, annotations, 10 GB uploads a month | unlimited bookmarks, collections and devices; collaboration is free | raindrop.io/pro and /pro/buy (own page, no price); contextbolt.com |
| Toby | 300,000 | 3.8 (3.4K) | Productivity **$6/month, or $54/year ($4.50/month)**. Team $10/month, or $96/year | unlimited saved tabs, Smart (AI) naming, grouping and sorting, duplicate removal, history search, private Spaces | **60 saved tabs per workspace**; account required | gettoby.com/pricing; help.gettoby.com free-plan and FAQ pages; CWS ("Offers in-app purchases") |
| Workona | 200,000 | 4.2 to 4.3 (3.8K; the two CWS listing URLs disagree) | Pro price is **not readable on its own page**. Team is $12/user/month or $108/user/year (only as an example on the billing help page). Pro is $7/month on Capterra and "about $6 to $9" on SupaSidebar, both 3rd party, unverified | Pro: unlimited spaces and sections, **90-day session backups**, integrations, templates. Team: shared spaces, SSO | "free for everyone" with limited spaces (5 per 3rd party, unverified). toolradar.com says "no permanent free plan", which contradicts Workona's own page | workona.com/pricing, /plans, /help/subscriptions-billing; capterra.com |
| Tabs Outliner | 100,000 | 3.2 (3.3K) | **$15 one-time** Pro | keyboard shortcuts and clipboard, **local backups every few minutes**, **automatic daily Google Drive backups** | manual backups only | tabsoutliner.com (own page); CWS ("small, one-time payment") |
| Tab Session Manager | 100,000 | 3.5 (454) | Free | none | none | CWS own page |
| TabExtend | 20,000 | 4.3 (355) | Pro **$8/month**, 25% off yearly. Team $21/month for 3 seats, then +$7 per seat | unlimited saves, multiple workspaces, **daily backups**, reminders | **30 saves** | tabextend.com/pricing; CWS |
| TabXpert | 10,000 | 4.4 (427) | "Plus" sold as monthly and **lifetime** subscriptions; amounts did not load (unverified) | not listed | unlimited sessions are free (changelog v4.2) | tabxpert.com/changelog and /pricing; CWS ("Offers in-app purchases") |
| Partizion | 2,000 | 3.8 (143) | Starter $12/month (3 workspaces, 100 tabs per collection). Pro $10/month (unlimited, advanced search). Beta users could lock in Pro "for life now at $5/mo". **No free plan** ("Partizion isn't free") | everything | 14-day trial only | partizion.io/pricing (page has placeholder plans, so it reads as messy); CWS |
| SessionBox (multi-login; neighbour) | not fetched | not fetched | Hobby $4.99 to $12.99/month and up (which figure is monthly and which annual is unclear) | all features; 1-week trial | no free plan | sessionbox.io/pricing |
| Shift (browser/email; neighbour) | n/a | n/a | yearly billing only; amount not shown | multi-account, notifications | 30-day trial | tryshift.com/pricing |
| Side Space (AI vertical tabs) | "3k+ active" | n/a | not stated | "premium features" | not stated | IndieHackers founder post, Nov 2024 (3rd party, founder's own claim) |
| AI-only tab groupers (AI Tab Grouper Pro, TabSmart, Tab Manager Pro AI) | **7 to 24 users each** | 5.0 (3 to 4 ratings) | freemium or bring-your-own API key; no prices shown | auto-grouping, session save | basic grouping | CWS own pages |
| Tab Stash (Firefox) | n/a (1.1k GitHub stars) | n/a | Free, MPL-2.0 | none | none | github.com/josh-berry/tab-stash |
| Arc, SigmaOS, Edge Workspaces, Heyday, Sidekick, Station, Stack, Ramp | not fetched today | | | | | Skipped: these are browsers or apps, not extensions. sigmaos.com/pricing failed to load. **Unverified.** |

## 2. Features people demonstrably pay for (strongest evidence first)

Evidence counted: (a) appears behind a paywall on vendors' own pages today, (b) people say they paid or would pay, (c) the reaction to the paywall.

1. **Automatic backups and longer snapshot history.** Behind a paywall at 5 vendors (Tabs Outliner automatic Drive and local backups; Workona 90-day session backups; TabExtend daily backups; Raindrop daily and cloud backup; Session Buddy says cloud storage will be its only premium feature). It is the only paid feature with a positive buyer quote ("I paid early on supporting the develop because it is extremely useful", Tabs Outliner CWS review, 17 Dec 2024). No backlash against it was found.
2. **Unlimited saved items or workspaces.** The most common paywall (Toby at 60, TabExtend at 30, Partizion, Workona spaces). It also gets the **most backlash**. All 5 price-related reviews on page 1 of Toby's Firefox reviews are 1 or 2 stars ("60 tabs limit makes this useless", "pay-walling the core feature"). A Reddit r/chrome user wrote that $20/year would be acceptable but $40 is "exploitative", more than a password manager (Oct 2024). Toby's own post said it moved to paid plans because "Toby may not survive" otherwise (5 Oct 2024). People do pay, but it costs ratings: Toby is at 3.8.
3. **Search** (advanced, full-text or history search): Toby, Partizion, Raindrop.
4. **Multiple workspaces or spaces**: Workona, TabExtend, Partizion. This targets work and project users.
5. **Duplicate cleanup**: Toby, Raindrop.
6. **AI or smart grouping and naming**: Toby and Raindrop bundle it into paid plans. AI-only tab extensions have 7 to 24 users each, so there is **no evidence yet that AI alone sells** in this niche.
7. **Keyboard shortcuts** (Tabs Outliner Pro). One vendor only.

Pricing models in use: Tabs Outliner sells a $15 one-time Pro. TabXpert sells lifetime and monthly. SupaSidebar sells a lifetime at $39.50 (Black Friday price, vendor's own blog). Everyone else sells subscriptions of $3 to $12 a month. In a small-extension sample, switching from $2.99/month to $3.99 one-time raised conversion by 60% (dev.to/ktg0215, Aug 2026; the article gives no baseline). The same author's overall free-to-paid rate is 0.8%, and his MRR was $31 across 38 extensions. Side Space reports 100+ paid users out of 3k+ active, about 3% (founder's claim, Nov 2024).

## 3. Recommended price for Tab Lifeboat Pro

**What stays free:** unlimited manual saves, restore, OneTab and Session Buddy import, local storage, and export. A cap on saves is the paywall users punish (point 2). The two biggest players, OneTab (2M) and Session Buddy (1M), are fully free, so a capped free plan loses to them on day one.

**What Pro adds:** what the evidence says people pay for without anger:
- automatic snapshots kept 90 days (free keeps the last 3; this matches Workona's "90-day session backups")
- automatic backup to the user's own Google Drive (matches Tabs Outliner Pro)
- full-text and history search across saved sessions
- duplicate cleanup
- later: sync across devices

| Plan | USD | INR (India price) | Why |
|---|---|---|---|
| Monthly | **$2.99** | **₹149** | Raindrop Pro is $3. This is below Toby ($6) and TabExtend ($8). It also keeps the $2.99 Akhil approved on 11 Nov. |
| Yearly | **$19** | **₹999** | Under the "$20/year is acceptable" line from the Reddit thread, and under Raindrop ($28) and Toby ($54). |
| Lifetime | **$24** (already approved) | **₹1,499** | Between Tabs Outliner's $15 one-time and SupaSidebar's $39.50 lifetime. In the one data point found, one-time pricing converted better for small utilities. |

INR notes: at about ₹94 to the dollar (hdfcsky.com rupee reports, Nov 2026; check the rate on the day you set prices), the direct conversions are $2.99 ≈ ₹281, $19 ≈ ₹1,786 and $24 ≈ ₹2,256. The INR prices above are a discount of about 45% to 47% for India.
- Dodo Payments offers this kind of country-based discount (purchasing power parity, or PPP) at checkout (dodopayments.com, own page).
- No public benchmark for an India discount on tab-manager or extension prices was found. **The INR figures are a hypothesis**, to be checked against real conversion data after launch.

**Expected conversion:** plan for 1% (the 0.8% to 3% range above). At 10,000 users that is about 100 buyers. At the $24 lifetime price that is about $2,400 once. Monthly income needs the yearly plan. This is arithmetic from the figures above, not a forecast.

## 4. Open gaps (unverified today)
- Workona Pro's price and free-plan limits (its page did not show the numbers)
- Raindrop's price on its own page (the price field was blank)
- TabXpert's amounts (the pricing section did not load)
- OneTab's apparent new sync and folders features
- SigmaOS, Arc and Edge workspaces
- Heyday, Sidekick, Station, Stack and Ramp (not checked)
- Toby's Chrome reviews, Reddit (robots-blocked) and G2 reviews (login-gated): the review sample is small (Firefox Toby reviews, page 1 of 4; one Reddit thread)

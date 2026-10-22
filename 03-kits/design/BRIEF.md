# Kits landing pages: design brief (A11)

**Built as real pages** on the calculator site (`05-deals/site`), because PLAN.md makes the free calculators the funnel for paid kits:
- `/kits/`: all kits plus the full price ladder.
- `/kits/gate-2027/`, `/kits/upsc-2027/`, `/kits/tax-sip-2026-27/`
- `/legal/{about,contact,terms,privacy,refunds,delivery}/`
- A "Kalpa Kit" link under the income-tax, salary, SIP, EMI and HRA calculators, in English and Telugu.

Data: `05-deals/site/src/lib/kits.ts`. Tests: `kits.test.ts` (prices = `03-kits/PLAN.md` ladder, official exam dates, tax preview = the site's tax engine, no dark patterns, policy pages). Screens: `scripts/screens.py` (52 at 390 px, light + dark).

## Research (16 Oct 2026)
- **Razorpay** won't issue live keys for a website that lacks these pages: About, Contact, Pricing, Terms, Privacy, Cancellation/Refund and Shipping. Payment Links still work without them. ([Razorpay docs](https://razorpay.com/docs/us/payments/dashboard/account-settings/business-website-details))
- **Consumer Protection (E-Commerce) Rules 2020:** the site must show the seller's legal name, address and contact. It must name a grievance officer who acknowledges complaints in 48 hours and resolves them in a month. It must also state refund/return terms and the total price. ([summary](https://www.indialaw.in/blog/consumer-protection-e-commerce-rules/))
- **CCPA Dark Patterns Guidelines, 2023:** they ban false urgency, drip pricing, confirm-shaming, basket sneaking and similar tricks ([JSA summary](https://www.jsalaw.com/newsletters-and-updates/ccpa-issues-guidelines-for-prevention-and-regulation-of-dark-patterns-2023/)). So the pages have:
  - no countdown timers or "only N left";
  - one full price with nothing added;
  - an early-bird price shown only when it's live and real.
- **Exam dates:**
  - GATE 2027 on 6, 7, 13, 14, 20 and 21 Feb 2027, organised by IIT Madras ([IIT Madras](https://www.iitm.ac.in/happenings/press-releases-and-coverages/iit-madras-announces-dates-syllabus-revision-new-paper)).
  - UPSC Prelims on 23 May 2027 ([Deccan Herald](https://deccanherald.com/education/upsc-cse-prelims-2027-on-may-23-mains-begins-aug-20-check-full-calendar-4015277)).
- **Layout pattern:** the top Astro landing templates (AstroWind 5.9k★, ScrewFast 1.4k★, both landing-page themes) go hero → proof → pricing cards → FAQ. We use the same order on our own Kalpavruksha tokens. The "proof" is a real slice of the sheet's layout drawn in HTML: no stock screenshots, no invented reviews.

## Until payment is live
Every paid button reads "Opens soon" and leads nowhere, so nobody can pay for something that doesn't exist. To go live, put the Razorpay Payment Page link into `buyUrl` for that tier (tests allow only `rzp.io` / `pages.razorpay.com`), and the Lite sheet link into the Lite tier.

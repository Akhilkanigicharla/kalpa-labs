# Sales kit scan (A07): contracts, DPDP, WhatsApp opt-in, evidence · 16 Oct 2026

Goal: the BotBhai sales kit (plan item P1-W2-05): an A5 card (Telugu + English), a proposal, an agreement with a DPDP processor clause, a privacy notice and an objection sheet. Everything below was checked on 16 Oct 2026. **I'm not a lawyer.** The agreement is a careful template; get it reviewed before the first signature (CEO item C23).

## Answer first
- **Agreement: adapt Common Paper**, not GitHub. Its Cloud Service Agreement v2.1 and DPA v1.1 are free to reuse and modify under **CC BY 4.0** if we credit them. We kept their structure (service, fees, term, data processing, sub-processors, breach notice, deletion on exit, liability cap, law) and rewrote it in plain English for an Indian sole proprietor and the DPDP Act.
- **GitHub has nothing better.** The `contract-templates` topic tops out at 3 stars with no licences shown. [open-agreements](https://github.com/open-agreements/open-agreements) (57★, Apache-2.0 code) only wraps Common Paper-style templates.
- **DPDP timing:** the Rules were notified on **13–14 Nov 2025** (G.S.R. 843(E)). Most duties, including the Rule 3 notice, Rule 6 security, Rule 7 breach and Rule 8 erasure, start around **13 May 2027**. We build to them now, so salons signed today don't need new paperwork later.
- **What the agreement must carry (Act s.8):**
  - The salon is the Data Fiduciary and stays responsible (s.8(1)).
  - It may use a processor only "under a valid contract" (s.8(2)).
  - Rule 6 wants security safeguards written into that contract, and logs kept for at least a year.
  - Rule 7 wants a detailed breach report to the Board within 72 hours. So we promise the salon notice within **24 hours**, which leaves them time to act.
- **Privacy notice (Rule 3):** it must stand on its own and list the data, the purposes, the service, and how to use rights and withdraw consent. Ours is bilingual and is made per salon from the same JSON as the proposal.
- **WhatsApp opt-in (Meta):** say clearly that the person is opting in, and to which business by name. Any method is fine (in person, paper, website). Give clear opt-out and honour it. BotBhai's STOP/START and the OFFERS opt-in already do this; the kit repeats it in the agreement (section 6) and the notice.
- **Evidence for reminders:** a [Cochrane review](https://www.cochrane.org/evidence/CD007458_mobile-phone-messaging-reminders-attendance-healthcare-appointments) (2013, healthcare, 7 studies, 5,841 people) found text reminders raised attendance from **67.8% to 78.6%** (RR 1.14, moderate certainty). That's about one in three no-shows saved, which is the only "saving" rate the proposal uses. Marketing blogs claiming "70%" or "40%" are unsourced, so we don't use them.

## Sources ranked
| Source | What we took | Licence / status |
|---|---|---|
| [Common Paper CSA v2.1](https://commonpaper.com/standards/cloud-service-agreement/) | Section structure, liability cap idea, plain-English approach | CC BY 4.0 (credited on the agreement) |
| [Common Paper DPA v1.1](https://commonpaper.com/standards/data-processing-agreement/) | Instructions-only processing, sub-processor notice (10 business days) + objection, breach notice, return/delete at end | CC BY 4.0 |
| [DPDP Rules 2025 (PIB)](https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc20251117695301.pdf) · [taxmann analysis](https://www.taxmann.com/post/blog/analysis-indias-dpdp-act-and-rules) · [timeline](https://www.dpdpactindia.com/timeline.html) | Rule 3, 6, 7, 8 duties; 18-month start | Law |
| [Meta: Get opt-in for WhatsApp](https://developers.facebook.com/documentation/business-messaging/whatsapp/getting-opt-in) | Opt-in wording, opt-out | Platform policy |
| [Cochrane CD007458](https://www.cochrane.org/evidence/CD007458_mobile-phone-messaging-reminders-attendance-healthcare-appointments) | 67.8% → 78.6% attendance | Peer-reviewed |
| [hyperleap.ai salon guide](https://hyperleap.ai/blog/whatsapp-salons-spas-india) | Objection list ideas only (staff, cost, accuracy, privacy) | Its numbers are mostly unsourced, so not used |

## Rules the kit follows (and the test enforces)
- Every ₹ figure comes from `01-botbhai/docs/sales/prices.json`, which must equal PLAN.md §2 (the roadmap check), or from the proposal maths, which the test recomputes independently.
- The kit uses no "guarantee", "100%", "risk-free" or GST wording. Results are always called an estimate.
- Telugu is never set in a font without Telugu letters. The Anek Telugu font is embedded in every PDF that has Telugu text.
- The card's QR codes scan (OpenCV) to the demo.

## Found on the way
- `setups/salon/setup.meta.json` still had the old ₹9,999 + ₹2,999 price. It now shows the Standard tier and points to `prices.json`.
- Half of a ₹2,999 setup fee isn't a whole rupee. The proposal now says ₹1,500 on signing and ₹1,499 at go-live, instead of rounding without saying so.

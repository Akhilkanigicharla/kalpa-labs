# A150 · b6 AI FinOps + AI Guardrails consulting plan

Research run: 6 Nov 2026 (cloud session, lane A). Status: **draft for Akhil's approval.**
Rule: two sources per fact (CLAUDE.md rule 8). Single-source items are marked *(1 source)*. Prices change; recheck on the provider's page on the day you pay.
Money conversions use ≈ ₹95 per US$ (mid-market quotes seen today ranged ₹90–97). Treat ₹ figures as rough.

## 1. The answer in 5 lines
1. Cheapest real credential first: **FinOps Certified Practitioner, $325 (≈ ₹31k), 3 attempts, unproctored.** Then **IAPP AIGP ($799 non-member, ≈ ₹76k)**. ISO/IEC 42001 Lead Implementer last.
2. Big catch on ISO 42001: with no work experience, PECB only gives **"Provisional Implementer"**. The "Lead Implementer" title needs 5 years' experience (2 in AI) and 300 hours of AIMS project work. Kalpa must never say "Lead Implementer" until that is true.
3. All three certificates together cost about ₹1.6–1.8 lakh. That is far above the ₹0–5,000 budget, so certificates are paid **from consulting income**, not before.
4. Start with 3 packages, priced well below the market because Akhil has no certificate and no case study yet. The first 3 clients are **free pilots** (rule of 18 Oct: no money until delivery is proven). Pilots buy case studies, not cash.
5. First clients: Indian SaaS/AI startups and agencies that already pay for AI APIs and sell to EU/US customers. Reach them with a free "AI bill X-ray" (the old Ledger Peaks tool) and LinkedIn posts, never cold calls (TRAI).

## 2. Certification paths for Akhil (fees checked today)

| Certificate | Fee today | Prep time (1 hr/day) | What you can honestly say after passing | Sources |
|---|---|---|---|---|
| **FinOps Certified Practitioner (FOCP)** | $325 exam-only (3 attempts in 12 months, 50 Q, 60 min, 75% pass, not proctored, valid 24 months); $500 with the official self-paced course | ~1–2 months *(estimate: unverified hours)* | "FinOps Certified Practitioner" | devopscube.com (2026 price table); finopsweekly.com; open-exam-prep.com quoting learn.finops.org |
| **FinOps Certified: AI Value** (new 2026; for token, GPU and agent spend) | $500 | after FOCP | "FinOps Certified: AI Value" | devopscube.com; opslyft.com (18 Oct 2026) |
| **IAPP AIGP** (AI governance) | $799 non-member / $649 member (+ $295/yr membership); retake $625 / $475; certification maintenance $250 per 2 years for non-members; 100 Q, 2 h 45 min, pass 300/500 | ~80–180 hours ≈ 3–6 months | "AIGP" | store.iapp.org (official, $799 / $649); trainingcamp.com; open-exam-prep.com |
| **PECB ISO/IEC 42001 Lead Implementer course + exam** | No separate exam price: exam is inside the course price. Self-study / e-learning bundles seen at $599–$799 (resellers); 5 days (4 training + 1 exam) | ~1–2 months | With no experience: **"PECB Certified ISO/IEC 42001 Provisional Implementer"** only | pecb.com course page (levels + "fees included in training"); riskprofs.com ($599); 1st-academy.org ($799) |

**PECB credential ladder (official page, fetched today):** Provisional Implementer = no experience. Implementer = 2 years (1 in AI) + 200 h AIMS project work. Lead Implementer = 5 years (2 in AI) + 300 h. Senior Lead = 10 years (7 in AI) + 1,000 h. The same ladder is on GlobalKnowledge's course page (second source).

**Suggested order:** FOCP (first income) → AIGP (after ~₹1 lakh revenue) → ISO 42001 course → AI Value. Free study material first: IAPP gives the AIGP Body of Knowledge as a free download *(1 source: certcrush.app)*, and Kalpa already has the MIT ISO 42001 control list from Probo (facts register, 18 Oct).

## 3. Three consulting packages

What the market charges today:
- **LLM / AI cost audit:** fixed-fee audits at $2,500 (1 week) on entuit; $3,000–6,000 (3–5 days) on activewizards, which says it isn't worth it below $2k/month AI spend. Follow-on optimisation sprints run $12k–25k (activewizards) or $15k–40k (a Wellfound founder post).
- **ISO 42001 gap assessment for a small firm:** $1,500–2,500 for a 2–3 day job (certbetter.com); $3,000–10,000+ is the general range (Vanta; ud.hk). Full first-year certification for a small company runs $15k–75k+ (complyjet; certpro).
- **India:** ISO 42001 consulting is quoted at an indicative ₹1.5–5 lakh, 8–12 weeks to readiness *(1 source: tcsa.in)*. The same firm prices ISO 27001 consulting at ₹1–3 lakh, plus ₹0.7–1.2 lakh to the certification body (tcsa.in cost guide; wattlecorp agrees on the cost layers). That is a cross-check for the general price level only.

Kalpa's proposed prices: below market while unproven, and raised after 3 case studies.

| # | Package | What the client gets | Delivered by | India price | World price | Raise to (after 3 case studies + cert) |
|---|---|---|---|---|---|---|
| P1 | **AI Cost Audit** ("AI bill X-ray") | 30–90 day spend baseline by model/feature; top-10 waste list (wrong model, no caching, long prompts, retries); routing + caching plan with ₹ savings; 1 review call | Ledger Peaks tool + agent Ledger + Akhil's review | ₹14,999 | $750 | ₹35,000 / $2,500 |
| P2 | **AI Guardrails Setup** | AI use policy; AI system inventory; risk register; prompt-injection and data-leak tests on their bots; DPDP and EU AI Act Art. 50 (transparency) checklist; staff one-pager | agents Guard + Vigil, Probo ISO 42001 control list, Akhil's review | ₹39,999 | $1,800 | ₹75,000 / $4,000 |
| P3 | **ISO 42001 Readiness (gap assessment only)** | Clause-by-clause + Annex A gap report, scope statement, 90-day roadmap. **Not** certification: the certificate only comes from an accredited body. | same + Akhil (only after the PECB course) | ₹74,999 | $2,500 | ₹1.5 lakh / $5,000 |

Optional retainer after P1/P2: monthly AI spend + guardrail watch, ₹7,999/mo (India) or $400/mo (world). This uses the same delivery stack.

Unit economics: delivery runs on free models and n8n (≈ ₹0 cash); Akhil's time is about 2–4 h per P1, 6–10 h per P2 and 15–20 h per P3. At 1 hr/day, take **at most 1 paid project at a time**.

## 4. What Kalpa can do before Akhil holds any certificate (honest wording)
- **Can say:** "AI cost and AI governance reviews using the FinOps Framework, ISO/IEC 42001 controls and the NIST AI RMF." "Founder is preparing for FinOps / AIGP certification." Free tools (AI bill X-ray), checklists and blog posts.
- **Can sell after pilots:** P1 and P2 (no law requires a certificate for advice), with the plain line "not a certification body; we do not issue certificates".
- **Must not say:** "certified", "ISO 42001 certified consultant", "Lead Implementer", "guaranteed compliance", or "guaranteed savings" without written terms. No fake logos or testimonials. Website copy must match what is built (rule of 18 Oct).

## 5. How to find the first clients (no spam, no cold calls)
1. **Free pilots (3):** offer P1 free to founders already using AI APIs, in exchange for a written case study + testimonial, with permission.
2. **Lead magnet:** the free "AI bill X-ray" page: paste last month's AI invoice totals and get a waste estimate. People opt in, then follow-up happens by email only.
3. **LinkedIn content, 3 posts/week** (agents Kavi + Echo draft, Akhil approves): real cost-cutting numbers from the pilots; the EU AI Act Art. 50 deadline for generative-AI marking (the transitional period ends 2 Dec 2026, per the facts register).
4. **Where buyers are:** Indian SaaS founders selling to the EU/US (enterprise buyers ask for AI governance), AI chatbot agencies, D2C brands with AI support bots. Use public, opt-in channels (founder communities, LinkedIn, events). The first-customer-finder skill can build the shortlist.
5. **Partners:** ISO 27001 consultancies that don't do AI yet. Kalpa does the AI part, white-labelled; the partner owns the client relationship.

## 6. Risks
- Budget: certificate fees (≈ ₹1.6–1.8 lakh in all) need revenue first. Don't buy them on a card before income.
- Credibility: no experience → price low, deliver the pilots very well, publish real numbers.
- Time: 1 hr/day. P3 waits until the P1/P2 flow runs on agents.
- Small market at the low end: below $2k/month AI spend, an audit pays back slowly. Qualify leads by spend first.

## 7. For Akhil to approve (CEO queue)
1. Approve the 3 packages and the launch prices above (or change them).
2. Approve "3 free pilots first, then paid".
3. Approve the certification order: FOCP → AIGP → ISO 42001 (paid from income).

# b6 Offer pack: AI FinOps + AI Guardrails consulting

Built 6 Nov 2026 from the approved plan (`../research/a150-consulting-plan.md`). Prices approved by Akhil on 6 Nov.
**Nothing here goes public or to a customer until Akhil says "go"** (CLAUDE.md rule 9). Pilots come first; no money is taken until delivery is proven (rule of 18 Oct).

## 1. Package one-pagers

### P1 · AI Cost Audit ("AI bill X-ray"): ₹4,999 India (rebuilt 21 Nov 2026, A215)
**Headline:** Cut your AI API bill without sharing your prompts.
**Sub-line:** We install open-source Langfuse on your own account, find the savings, and hand you the India paperwork.
**For:** Indian startups and agencies spending ₹50k+/month on AI APIs.

**Why it works**
- **We never see your prompts.** We read model, tokens, cost and status only; prompt and answer text are never requested.
- **Your tool, your data.** Langfuse runs on your server or your own Langfuse Cloud project. Its core is MIT-licensed, so it stays yours after we leave.
- **Paperwork in the box.** Drafts of your DPDP privacy notice, staff AI usage policy and model register, each marked "lawyer review needed".

**What we do (5 working days after the install)**
1. **Install:** we add Langfuse to your app on staging, then production. You create the keys and keep them; you never send them to us by chat or email.
2. **Measure:** 7–30 days of real calls, or your past usage export if you have one.
3. **Audit:** `langfuse_pull.py` + `audit.py` give spend by model and feature, the top-10 waste list (wrong model, no caching, repeat prompts, retries) and a savings plan with ₹ estimates.
4. **Hand over:** one 30-minute review call, the report, the handover note (`langfuse-handover.md`) and the paperwork pack. Then you delete our key pair.

**Fee (approved by Akhil 11 Nov 2026)**
- Fixed: **₹4,999** for the audit.
- Or, for the first 3 clients only: **20% of the savings proven in your first 3 months** after the fixes, instead of the fixed fee. Proven = billed AI spend measured the same way before and after, adjusted for traffic. No proven saving, no fee.

**FAQ**
- *Do you see our customers' data?* No. Only usage numbers. We delete them 30 days after delivery.
- *Will Langfuse slow or break our app?* We test on staging first, including with Langfuse switched off.
- *Are the policy drafts legally final?* No. They are drafts for your lawyer; we are not a law firm and we certify nothing.
- *Who makes the code fixes?* You, or us on a separate quote.

**Not included:** making the code changes (separate sprint quote); legal sign-off. Helicone instead of Langfuse: not built yet (no importer), so do not offer it.

### P2 · AI Guardrails Setup: ₹39,999 India / $1,800 world
**For:** companies running customer-facing chatbots or AI features.
**You get in 2–3 weeks:**
1. AI use policy (1–2 pages, plain English).
2. AI system inventory and a risk register.
3. Prompt-injection and data-leak tests on your bots, with a fix list.
4. DPDP and EU AI Act Art. 50 (transparency / AI-content marking) checklist.
5. Staff one-pager: "safe use of AI at work".

### P3 · ISO/IEC 42001 Readiness (gap assessment): ₹74,999 India / $2,500 world
**For:** AI companies whose enterprise customers ask for AI governance.
**You get in 3–4 weeks:**
1. Clause 4–10 + Annex A gap report.
2. AIMS scope statement.
3. 90-day roadmap to audit readiness.
**Important:** Kalpa is not a certification body and does not issue certificates. Only an accredited body can certify you. Offered only after Akhil completes the PECB ISO 42001 course.

**Retainer (after P1 or P2):** ₹7,999/month India, $400/month world, for a monthly AI spend and guardrail check.

## 2. Free pilot terms (first 3 clients)
- P1: the savings-share fee above (no proven saving, no fee). P2 delivered free.
- In return, the client agrees in writing to (a) a short case study with real before/after numbers (anonymised if they want) and (b) a testimonial, only if they are happy.
- Read-only data only. We sign their NDA or use ours. Data is deleted 30 days after delivery (DPDP-friendly).
- No promise of savings. We report what we find.

## 3. Honest wording (use as-is)
- Use: "AI cost and governance reviews based on the FinOps Framework, ISO/IEC 42001 controls and the NIST AI RMF."
- Use: "Founder preparing for FinOps Certified Practitioner and IAPP AIGP."
- Never: "certified", "ISO 42001 certified consultant", "Lead Implementer", "guaranteed savings", "guaranteed compliance".

## 4. First message for a warm or opt-in contact (LinkedIn DM / email, never cold calls)
> Hi {name}, I run Kalpa Labs in Hyderabad. We're doing 3 free AI bill reviews this month for teams using OpenAI/Anthropic/Gemini APIs. You share read-only usage exports; in 5 days you get a ranked list of where the spend leaks and what each fix saves. In return: a short case study if it helps you. Want one of the 3 slots?

## 5. Three LinkedIn post drafts (Akhil edits, approves, posts)
1. **"Where AI bills leak":** the 5 usual leaks (wrong model, no caching, huge prompts, retries, forgotten keys), plus one line on each fix. CTA: "Comment AUDIT for the free checklist."
2. **"2 Dec 2026, AI content marking":** the EU AI Act Art. 50 transitional period for generative AI ends 2 Dec 2026 (facts register). What Indian SaaS selling into the EU should check this week.
3. **"Guardrails in 1 page":** a sample AI use policy outline: who may use which tool, with what data, and who checks.

## 6. Delivery workflow (agents → Akhil)
`client export → Ledger (cost baseline) → Guard + Vigil (risk/guardrail tests) → Doc (report draft) → Akhil review (30–60 min) → send`. Models: today's free router models; Telugu/Hindi client notes may use `sarvamai/sarvam-105b` if a free host appears (A158 found none; Sarvam lists sarvam-30b as deprecated legacy).

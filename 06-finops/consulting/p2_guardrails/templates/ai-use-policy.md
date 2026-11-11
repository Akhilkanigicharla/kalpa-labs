# AI Use Policy: {{CLIENT}}

**[LAWYER CHECK]** Check with a lawyer before giving this to a client. This template is Kalpa Labs' starting draft, not legal advice. Fill every `{{...}}`, delete what does not apply, and have the client's lawyer review the legal points (marked [LAWYER CHECK]).

| Field | Value |
|---|---|
| Version | {{1.0}} |
| Owner (named person) | {{NAME, ROLE}} |
| Approved by (top management) | {{NAME}} on {{DATE}} |
| Next review | {{DATE, at most 12 months}} or after any big change |
| Linked policies | Information security, privacy, HR/conduct, vendor management |

## 1. Why we have this policy
We use AI to {{PURPOSE, e.g. answer customer questions faster}}. We want AI to be useful, safe, fair, private and honest with the people it affects. This policy says what is allowed, what is not, and who decides.

## 2. Who and what it covers
- All staff, contractors and interns.
- All AI systems we build, buy or use, listed in the **AI System Inventory** (`ai-system-inventory.csv`). An AI tool not on the inventory may not be used for work.

## 3. Rules for everyone
1. **Approved tools only.** Use AI tools from the inventory. Ask {{OWNER}} to add a new one.
2. **No secret or personal data in public AI tools.** Never paste customer personal data, passwords, API keys, source code marked confidential, contracts or financials into an AI tool that is not approved for that data class. [LAWYER CHECK]
3. **A human checks before it counts.** AI output that goes to a customer, decides about a person, or is published is reviewed by a person first.
4. **Say when it is AI.** Customers talking to a bot are told it is an AI at the start. AI-made images, audio and video are labelled. [LAWYER CHECK]
5. **No AI for banned uses:** {{e.g. hiring decisions without human review, emotion recognition, profiling children, deep fakes of real people}}. [LAWYER CHECK]
6. **Report problems.** Wrong, harmful, biased or leaked output goes to {{CHANNEL}} the same day. No one is punished for reporting in good faith.

## 4. Rules for teams that build AI features
1. Add the system to the inventory and the **risk register** before launch.
2. Run the **prompt-injection and data-leak tests** (`prompt-injection-data-leak-tests.md`) before launch and after every model or prompt change.
3. Strip or mask personal data before it reaches a model where possible; keep logs for {{RETENTION, e.g. 1 year}} with access limited to {{ROLES}}. [LAWYER CHECK]
4. Use AI providers only under signed terms that cover data use, storage region and deletion. [LAWYER CHECK]
5. Watch cost, errors and misuse after launch; name one person who acts on alerts.

## 5. Roles
| Role | Person | Does what |
|---|---|---|
| AI policy owner | {{NAME}} | Keeps this policy, inventory and risk register current |
| System owner (per AI system) | see inventory | Testing, monitoring, incidents for that system |
| Approver | {{NAME}} | Signs off new AI systems and high risks |
| Privacy contact | {{NAME}} | Data questions, user rights requests, breaches [LAWYER CHECK] |

## 6. Incidents
An AI incident is any harmful, wrong, leaked or unlawful AI output, or an attack on an AI system. Steps: stop or limit the system, tell {{OWNER}}, record it in the risk register, fix the cause, and tell affected people and regulators where the law requires (for personal data breaches in India, the DPDP Rules set timelines). [LAWYER CHECK]

## 7. Breaking the policy
Breaking this policy may lead to {{CONSEQUENCES, in line with HR policy}}. [LAWYER CHECK]

## 8. Sign-off
Approved by: ____________________  Date: __________

---
Template by Kalpa Labs (AI FinOps + AI Guardrails consulting). Not a certification, not legal advice.

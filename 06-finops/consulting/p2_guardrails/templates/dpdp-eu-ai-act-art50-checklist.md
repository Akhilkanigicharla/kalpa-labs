# DPDP + EU AI Act Art. 50 transparency checklist: Client

**[LAWYER CHECK]** Check with a lawyer before giving this to a client. Every line below is a legal point. This is Kalpa Labs' plain-English summary, not the legal text, not legal advice and not a certification.

How to use: tick Yes / No / N.A. for each line, write where the evidence is, and give the client the open items as tasks. Dates change: recheck the sources on the day you deliver.

## Part A. EU AI Act Article 50 (transparency)

Applies from 2026-08-02; last checked 2026-10-18. First answer ART50-06: with no EU users, Art. 50 likely does not reach the client.

| ID | Para | Who | Check | Evidence to collect | Yes/No/N.A. | Where |
|---|---|---|---|---|---|---|
| ART50-01 | Art. 50(1) | provider | People are told they are talking to an AI system (chatbots, voice agents), unless it is obvious [LAWYER CHECK] | first-message disclosure text; screenshot |  |  |
| ART50-02 | Art. 50(2) | provider | AI-generated audio, image, video or text is marked in a machine-readable way as AI-generated (grace period until 2026-12-02 for generative systems already on the market before 2 Aug 2026; single source, unverified) [LAWYER CHECK] | watermark or metadata method per output type |  |  |
| ART50-03 | Art. 50(3) | deployer | People exposed to emotion recognition or biometric categorisation are told it is running [LAWYER CHECK] | notice text or 'not used' |  |  |
| ART50-04 | Art. 50(4) | deployer | Deep fakes, and AI text published to inform the public, are disclosed as AI-generated or manipulated [LAWYER CHECK] | label on published content or 'not used' |  |  |
| ART50-05 | Art. 50(5) | provider+deployer | The disclosure is clear and given at the latest at the first interaction or exposure, and is accessible [LAWYER CHECK] | where and when the disclosure shows |  |  |
| ART50-06 | Art. 50(1) | provider | You know whether you have EU users at all (if none, Art. 50 likely does not reach you) [LAWYER CHECK] | user country split |  |  |

## Part B. India DPDP Act 2023 + Rules 2025 (AI usage)

Rules published 2025-11-13; most duties from 2027-05-13; last checked 2026-10-18. Rule 1(2)-(4): Rules 1, 2, 17-21 on publication; Rule 4 one year later; Rules 3, 5-16, 22, 23 eighteen months later. Act sections 3-16 are assumed to start with them (check the MeitY commencement notification before relying on it).

| ID | Check | Cites | Evidence to collect | Max penalty (Rs crore) | Yes/No/N.A. | Where |
|---|---|---|---|---|---|---|
| DPDP-01 | Have a lawful ground (consent or a listed legitimate use) for each AI purpose [LAWYER CHECK] | Act s.4(1), Act s.7 | feature list with purpose per feature | 50 |  |  |
| DPDP-02 | Give a clear notice before or at consent: data, purpose, how to withdraw, how to complain [LAWYER CHECK] | Act s.5(1), Rule 3 | privacy notice URL; AI providers named in notice | 50 |  |  |
| DPDP-03 | Consent is free, specific, informed and as easy to withdraw as to give [LAWYER CHECK] | Act s.6(1), Act s.6(4) | consent record reference per purpose | 50 |  |  |
| DPDP-04 | Be able to prove notice and consent if challenged [LAWYER CHECK] | Act s.6(10) | consent logs kept | 50 |  |  |
| DPDP-05 | Stay responsible for processing done by AI providers on your behalf [LAWYER CHECK] | Act s.8(1) | model and provider inventory | 50 |  |  |
| DPDP-06 | Use a provider (Data Processor) only under a valid contract [LAWYER CHECK] | Act s.8(2), Rule 6(1)(f) | signed DPA or provider terms per provider | 50 |  |  |
| DPDP-07 | Keep personal data used for decisions complete, accurate and consistent [LAWYER CHECK] | Act s.8(3) | data quality checks on AI inputs | 50 |  |  |
| DPDP-08 | Encrypt, mask or tokenise personal data (e.g. strip PII before prompts) [LAWYER CHECK] | Act s.8(5), Rule 6(1)(a) | PII-exposure counts from the PII scan (F-15) | 250 |  |  |
| DPDP-09 | Control who can access AI logs and raw prompts [LAWYER CHECK] | Act s.8(5), Rule 6(1)(b) | access list for log stores | 250 |  |  |
| DPDP-10 | Log, monitor and review access to personal data [LAWYER CHECK] | Act s.8(5), Rule 6(1)(c) | access logs; usage_event table | 250 |  |  |
| DPDP-11 | Keep backups so processing can continue after a breach or outage [LAWYER CHECK] | Act s.8(5), Rule 6(1)(d) | backup policy | 250 |  |  |
| DPDP-12 | Keep logs and the personal data in them for at least one year (unless another law says otherwise) [LAWYER CHECK] | Rule 6(1)(e), Rule 8(3) | log retention setting >= 365 days | 250 |  |  |
| DPDP-13 | Have technical and organisational measures that make the safeguards work [LAWYER CHECK] | Act s.8(4), Rule 6(1)(g) | named owner and yearly review | 50 |  |  |
| DPDP-14 | Tell each affected user about a breach without delay [LAWYER CHECK] | Act s.8(6), Rule 7(1) | breach plan that covers AI providers | 200 |  |  |
| DPDP-15 | Tell the Data Protection Board at once, then send a detailed report within 72 hours [LAWYER CHECK] | Act s.8(6), Rule 7(2) | breach plan with 72-hour Board report template | 200 |  |  |
| DPDP-16 | Erase personal data when consent is withdrawn or the purpose is no longer served [LAWYER CHECK] | Act s.8(7), Act s.8(8), Rule 8(1) | retention period per feature; deletion job | 50 |  |  |
| DPDP-17 | Warn the user at least 48 hours before erasing for inactivity [LAWYER CHECK] | Rule 8(2) | erasure warning message | 50 |  |  |
| DPDP-18 | Publish contact details of a DPO or a person who answers data questions [LAWYER CHECK] | Act s.8(9), Rule 9 | contact on website or app | 50 |  |  |
| DPDP-19 | Run a grievance system and answer within 90 days [LAWYER CHECK] | Act s.8(10), Act s.13, Rule 14(3) | grievance channel and response log | 50 |  |  |
| DPDP-20 | Publish how users can ask to access, correct or erase their data [LAWYER CHECK] | Act s.11, Act s.12, Rule 14(1) | rights request page; one-user lookup across AI logs | 50 |  |  |
| DPDP-21 | Get verifiable parental consent for children's data; no tracking or targeted ads at children [LAWYER CHECK] | Act s.9(1), Act s.9(3), Rule 10 | age gate or parental consent flow | 200 |  |  |
| DPDP-22 | Do not process children's data in a way likely to harm their well-being [LAWYER CHECK] | Act s.9(2) | impact note for child users | 200 |  |  |
| DPDP-23 | Check whether you are a Significant Data Fiduciary; if so, DPO in India, yearly DPIA and audit [LAWYER CHECK] | Act s.10(2), Rule 13 | SDF self-check | 150 |  |  |
| DPDP-24 | Track which countries receive data (provider regions) and follow any Government restriction [LAWYER CHECK] | Act s.16(1), Rule 15 | provider region per model in the inventory | 50 |  |  |

Penalties: penalty_max_inr_crore is from the Act's Schedule (s.33(1)): s.8(5) up to 250, s.8(6) up to 200, s.9 up to 200, s.10 up to 150, anything else up to 50.

## Sources

- Article 50 text: https://artificialintelligenceact.eu/article/50/ (checked 2026-10-18)
- In force 2 Aug 2026; Omnibus marking grace period: https://www.goodwinlaw.com/en/insights/publications/2026/08/alerts-technology-dpc-eu-ai-act-transparency-obligations-now-in-force (checked 2026-10-18)
- Act text (official Gazette PDF): https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf (checked 2026-10-18)
- Rules text, rule-by-rule: https://www.dpdpa.com/dpdparules.html (checked 2026-10-18)
- Rules summary (law firm): Rule 6 one-year logs, Rule 7 72 hours: https://ourtake.bakerbotts.com/post/102lund/india-notifies-final-rules-for-digital-data-protection-act (checked 2026-10-18)

**[LAWYER CHECK]** Check with a lawyer before giving this to a client.

# Client intake questionnaire (Kalpa Labs AI FinOps + AI Guardrails)

Send before the first call, or fill it in together (30 minutes). Answers go into `intake.json` (shape: `intake.schema.json`); check it with `python3 validate_intake.py intake.json`.
Do not collect passwords, API keys or customer personal data here. Ask for **exports** (CSV/JSON) instead of logins.

## 1. About you (`company`)
1. Company name, website, city and country.
2. What you sell, in one line. Team size.
3. Contact person: name, role, email.

## 2. AI you use today (`ai_systems`, list one per system)
1. Name and purpose (e.g. support chatbot, document summary, lead scoring).
2. Built in-house or bought? Model provider(s) and model(s).
3. Who uses or is affected by it: staff, customers, children, public?
4. Customer-facing? Does it say it is an AI?
5. Does it process personal data? Which kinds?
6. Status: idea, pilot, live, retired.

## 3. AI spend (`spend`, for P1 AI Cost Audit)
1. Monthly AI spend (rough), currency.
2. Providers billed (OpenAI, Anthropic, Google, AWS Bedrock, Azure, OpenRouter, other).
3. Can you export usage for the last 30-90 days (CSV with date, feature, model, input_tokens, output_tokens, cost)? Optional extras that help: `requests`, `cached_tokens`, `prompt_hash`, `status`.
4. Do you tag calls by feature or customer today?
5. Do you use prompt caching, response caching or batch APIs?

## 4. Where you sell and which rules apply (`markets`, for P2)
1. Countries of your users: India, EU, US, UK, other.
2. Industry rules you already follow (e.g. RBI, IRDAI, HIPAA, SOC 2, ISO 27001).
3. Have enterprise customers asked you for AI governance or security answers?

## 5. Governance today (`governance`, for P2 and P3)
1. Written AI use policy? (yes / draft / no)
2. List of all AI systems (inventory)? Risk register?
3. Anyone named as owner of AI risk?
4. Have you ever tested your bots for prompt injection or data leaks?
5. Privacy notice that names your AI providers? Grievance / data-protection contact?
6. Do you hold ISO 27001 or SOC 2? Are you aiming for ISO/IEC 42001?

## 6. What you want (`goals`)
1. Which package(s): P1 AI Cost Audit, P2 AI Guardrails Setup, P3 ISO/IEC 42001 Readiness.
2. Top worry in one line (cost, a customer questionnaire, a law, a past incident).
3. Deadline, if any.

## 7. Consent (`consent`)
1. I agree Kalpa Labs may process the data I share only to deliver this work, and delete it within {{30}} days after delivery unless I ask otherwise.
2. Case study: may Kalpa Labs publish an anonymised case study? (yes / with review / no)

---
Kalpa Labs is not a certification body and does not issue certificates. Reports are estimates and readiness checks, not legal advice.

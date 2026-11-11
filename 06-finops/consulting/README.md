# b6 consulting delivery kit (AI FinOps + AI Guardrails)

Tools and templates to deliver the 3 packages in [../research/a150-consulting-plan.md](../research/a150-consulting-plan.md).
Everything runs offline here (no network, no accounts, no secrets). Akhil reviews every output before a client sees it.

**Honest wording:** say "AI FinOps + AI Guardrails consultant". Never say "certified", "Lead Implementer" or "guaranteed" until it is true. Kalpa Labs is not a certification body.

## What is in here

| Folder | For | What it is |
|---|---|---|
| `intake/` | all | `questionnaire.md` to send the client; `intake.schema.json` shape of the answers; `validate_intake.py` checks an `intake.json`; `example_intake_SYNTHETIC.json` |
| `p1_cost_audit/` | P1 AI Cost Audit | `audit.py` turns a usage CSV into a markdown audit report; `sample_usage_SYNTHETIC.csv` (made-up data) |
| `p2_guardrails/templates/` | P2 AI Guardrails Setup | AI use policy, AI system inventory (CSV), risk register (CSV), prompt-injection + data-leak tests, DPDP + EU AI Act Art. 50 checklist, staff one-pager |
| `p2_guardrails/build_checklist.py` | P2 | rebuilds the DPDP + Art. 50 checklist from `../src/frameworks/*.json` |
| `p3_iso42001/` | P3 ISO/IEC 42001 Readiness | `gap.py` turns an answers file into a scored gap report + 90-day roadmap; `areas.json` (Kalpa's own words); `answers_example_SYNTHETIC.json` |
| `tests/` | | pytest for all the generators |

## How to run (from `06-finops/consulting/`)

```bash
# Intake: check the client's answers
python3 intake/validate_intake.py intake/example_intake_SYNTHETIC.json

# P1: usage CSV -> report. Columns: date, feature, model, input_tokens, output_tokens, cost
#     (optional: provider, requests, cached_tokens, prompt_hash, status, is_retry)
python3 p1_cost_audit/audit.py p1_cost_audit/sample_usage_SYNTHETIC.csv --client "Demo Co" --currency USD --out p1-report.md

# P2: refresh the legal checklist after ../src/frameworks changes, then copy templates/ for the client
python3 p2_guardrails/build_checklist.py --client "Demo Co" --out dpdp-art50-checklist.md

# P3: blank answers file -> fill scores 0-3 (or "na" + reason for Annex A) -> report
python3 p3_iso42001/gap.py template > answers.json
python3 p3_iso42001/gap.py report p3_iso42001/answers_example_SYNTHETIC.json --out p3-gap-report.md

# Tests (from 06-finops/)
python3 -m pytest -q
```

## How each piece works, in short
- **P1** uses the client's billed `cost` as the spend. It finds 4 waste signals: big model on short prompts, long prompts without prompt caching, repeat prompts (needs `prompt_hash`), and failed/retried calls. Savings re-price rows on public list prices through the Ledger Peaks engine (`../src/price`) and apply only the price *ratio* to the billed cost. Every assumption is printed in the report; the total never counts the same money twice; the low end is half the estimate.
- **P2** templates have `{{...}}` blanks. Every legal point says **[LAWYER CHECK]: check with a lawyer before giving to a client.** The DPDP + Art. 50 checklist is generated from the same framework files Ledger Peaks uses, so dates stay in one place.
- **P3** uses the 70 clause and Annex A IDs + short titles from `../src/frameworks/iso42001-2023.json` (Probo, MIT). The check questions and area descriptions are Kalpa's own words; no ISO text is copied. Clauses 4-10 are mandatory (no "na"). The roadmap orders gaps by phase (days 1-30 foundations, 31-60 build, 61-90 check and improve), mandatory clauses first, biggest gaps first. It is a readiness check, not a certification.

## Before using with a real client
1. Get the client's lawyer to review the P2 legal points and the DPDP/Art. 50 checklist.
2. Recheck the dates and sources in `../src/frameworks/*.json` on the delivery day.
3. Ask for exports, never logins. Delete client data within the agreed days.
4. Ask the client to log `prompt_hash` and `status` for 7 days if they can: P1 gets sharper.

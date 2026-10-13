# PII scan (A32 / F-15)

Scans a customer's LLM log exports (CSV, JSONL, JSON, text) for Indian personal data and writes **counts and HMAC hashes only**. Raw values are never printed, stored or sent.

```
cd 06-finops/src
python -m pii.scan ../tests/fixtures/pii/ --out report.json --fail-on AADHAAR,PAN
```

- `--engine builtin` (default fallback, zero dependencies): IN_MOBILE, UPI_ID, IFSC, AADHAAR (Verhoeff check), PAN, GSTIN (check character), EMAIL, CARD (Luhn).
- `--engine presidio` / `auto`: adds Microsoft Presidio's pattern recognizers, run **pattern-only** through a stub NLP engine, so no 400 MB spaCy model is downloaded.
- Hashes use `ingest.schema.hash_id` (HMAC-SHA256 with the customer's `LP_HASH_SALT`).
- Workflow for the customer's repo: `06-finops/.github-workflow-drafts/pii-scan.yml`.

Licences: Presidio is MIT (Microsoft; now github.com/data-privacy-stack/presidio), used as an unmodified dependency. Verhoeff, Luhn and the GSTIN check-character algorithm are public. All recognizer code here is our own.

Tests: `cd 06-finops && python -m pytest -q tests/test_pii.py` (synthetic fixtures only; Presidio tests skip when it is not installed).

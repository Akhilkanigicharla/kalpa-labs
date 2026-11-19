# Free models and customer personal data (A244, 19 Nov 2026)

**Answer:** customer chats (names, phone numbers, bookings) go only to **Groq** (main) and **Cloudflare Workers AI** (backup). Never to free Gemini. OpenRouter `:free` only for agent work with no customer data. Sources and quotes: `00-hq/audit/facts.md` rows dated 2026-11-19.

| Provider (free tier) | Trains on our API data? | Customer PII? |
|---|---|---|
| Groq | No (trust.groq.com/faq); logs up to 30 days for reliability/abuse only | Yes (main) |
| Cloudflare Workers AI | No (workers-ai/platform/data-usage); zero retention by default | Yes (backup; don't turn on AI Gateway logging for customer flows) |
| OpenRouter `:free` | Depends on the model's provider; account setting + per-request `data_collection: "deny"` | No, until a live test proves `:free` + deny works |
| Gemini free (AI Studio key) | Yes, and human reviewers may read it (India gets unpaid terms) | Never. Paid key only (`GEMINI_PAID_TIER=1` in the voice agent) |

## What the code now does
- `00-hq/llm-router`: PII-safe by default (only `pii: true` providers get a key). `ROUTER_ALLOW_TRAINING_PROVIDERS=1` only on an agents-only copy. Test: `node make-config.test.js`.
- `01-botbhai/botbhai/voice`: `VOICE_ENGINE=gemini_live` is ignored unless `GEMINI_PAID_TIER=1`. Test: `python3 voice/test_prompt.py`.

## Messages per salon vs free caps (estimates)
Volume from K118 (free model, estimate): 20 / 80 / 200 messages per salon per day (low / typical / busy). K118 used 400 tokens per message; with a 5-language system prompt plus chat history a realistic request is nearer **1,500 tokens (1,300 in, 200 out)**, my estimate, not measured. Caps are from the official pages fetched today.

| Free cap (official, 19 Nov) | Requests/day it allows at 1,500 tokens | Typical salons (80/day) |
|---|---|---|
| Groq gpt-oss-120b: 1K RPD, 200K TPD, 8K TPM | ~133 (token cap binds first) | ~1.5 |
| Groq qwen3.8-27b (separate model cap, same numbers) | ~133 | ~1.5 more |
| Workers AI llama-3.1-8b fp8-fast: 10,000 neurons/day (~12 neurons/request) | ~800 | ~10 |
| Workers AI llama-3.3-70b fp8-fast (~76 neurons/request) | ~130 | ~1.5 |

Reading: free tiers carry the **first 2–10 salons** while testing, if prompts stay short (trim history, cache the business facts). 8K TPM on Groq means about 5 requests a minute at 1,500 tokens, so a busy hour queues. Past ~10 salons a paid tier is needed (Groq Developer or Workers AI Paid); prices **unverified** here and not a decision for now. Measure real tokens per request in the first pilot before planning on these numbers.

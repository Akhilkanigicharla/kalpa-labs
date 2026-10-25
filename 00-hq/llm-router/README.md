# Kalpa LLM router (A120)

One OpenAI-compatible address (`/v1`) in front of many **official** free LLM tiers. It is used by the n8n agents and as a fallback for the bots. It runs [FreeLLMAPI](https://github.com/tashfeenahmed/freellmapi) (MIT, pinned `v0.16.9`) in a **Hugging Face Space** (free CPU Space).

**Why only some providers?** FreeLLMAPI also supports many unofficial "free" resellers. Kalpa enables only providers with an official free tier (`allowed.json`). Every key comes from Space secrets that Akhil sets; nothing is in git. FreeLLMAPI's own README calls itself single-user and "not production", so we keep these safeguards:

- Every API call needs the router's **unified key**, and the dashboard needs the admin login, which has login throttling. The Space is public so callers can reach it: a private Space would put the HF token in the same `Authorization` header the router reads its own key from (`server/src/routes/proxy.ts`). FreeLLMAPI's compose file binds to localhost by default and calls itself single-user. Running it public is our choice, made with a strong admin password and a secret key.
- Customer bots call it only as a **fallback** after their main model (Groq, A85), so a free tier going away never stops a booking.
- Providers' terms are re-checked by the n8n task "Reel 25 Oct #5". If a provider forbids app use, it is removed from `allowed.json`.

| Secret (HF Space → Settings → Variables and secrets) | What |
|---|---|
| `ENCRYPTION_KEY` | 64 hex characters; stores keys encrypted (required) |
| `ROUTER_ADMIN_EMAIL`, `ROUTER_ADMIN_PASSWORD` | dashboard login, 8+ characters (required) |
| `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `GOOGLE_AI_API_KEY`, `CEREBRAS_API_KEY`, `MISTRAL_API_KEY`, `NVIDIA_API_KEY`, `COHERE_API_KEY`, `HF_TOKEN` | any you have; empty ones are skipped |

**Deploy:** GitHub → Actions → "LLM router" → Run workflow with `deploy` ticked. It needs the GitHub secret `HF_WRITE_TOKEN` and the variable `HF_SPACE` (for example `kalpalabs5145/kalpa-llm-router`).

**Free-tier limit:** the Space sleeps after a period with no use, and the first call after that waits for it to wake (unverified how long).

**Tests:** `node make-config.test.js` checks the allowlist and the secrets handling. The Action also builds the image and checks that the router starts.

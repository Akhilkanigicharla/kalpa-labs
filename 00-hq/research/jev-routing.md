# Jev decision layer: "Jev decides, n8n routes, the right model answers"

Checked 18 Oct 2026 (IST). Video: SSRR Rise, "Stop Wasting Tokens! Smart AI Routing with n8n & Jev AI" (youtube.com/watch?v=LVfa6EMAmk4, 16 Oct 2026, 18:49, transcript read in full).

## What Jev is
A decision model, not a chatbot. You send a **state** (text or JSON) and **questions**; it returns probabilities instead of prose:
- `noul`: yes/no → P(yes)
- `choice`: one option from a list → option + probabilities + confidence
- `score`: a level on your scale → expected level + confidence

Score and confidence are different signals: the score routes; low confidence → stronger model, a clarifying question, or a human.

## Two versions we use

| | TypeSafe Jev (hosted) | jevos (open source) |
|---|---|---|
| Where | n8n node `@typesafe-ai/n8n-nodes-typesafe-ai.typeSafeAi(Tool)`; paid from **n8n gateway credits** (no key). Also reachable through OpenRouter. | https://github.com/feder-cr/jev, MIT, jevos-v4 (Oct 2026). One CPU binary, ~1 GB RAM, `POST /v1/systemone` on 127.0.0.1:8017, same wire format. |
| Used by | Chitti `triage_message` (intent, mood, needs_human), Vigil `risk_flags`, workflow **Kalpa Smart Router (Jev)** (`1gqT8Ye3ttd3bLhm`) | Claude Code on Akhil's PC via MCP server `kalpa-jev` (`jev_decide`, `jev_health`). Installed 18 Oct with Akhil's explicit OK (exception to rule 2, logged). |
| Privacy | Text leaves to TypeSafe → test chats only until the privacy notice names it (DPDP) | Fully local, offline |

Not used: **OpenJev** 27B GGUF (CC BY-NC 4.0, non-commercial, ~24 GB RAM) — see `docs/toolkit/TOOLKIT.md` row 53.

## The router workflow (built 18 Oct, draft, not activated)
Chat → **Jev: Score Complexity** (route, score levels low/medium/high) →
- low → Laguna XS 2.1 (fast, free)
- medium → Nemotron 3 Nano Omni reasoning (free)
- high → Nemotron 3 Super 120B (free)

All three share one chat memory. Why: OpenRouter free models give ~50 requests/day; sending "what is Docker?" to a 120B model wastes the quota the deep jobs need.

## Measured on Akhil's PC (jevos-v4, i5-10310U, 4 threads)
- Salon message "book haircut + beard trim tomorrow 6pm, last time I waited 40 mins": booking 0.99, intent=booking (conf 0.96), mood "a bit annoyed" (0.82), needs_human 0.25.
- "Price for bridal makeup package? 5 people, 12 Nov": intent=price 0.98, is_lead 0.81.
- Latency ~2.5 s per request on this laptop CPU (the README's 28–130 ms is on a newer CPU).

## Next ideas (not built)
- BotBhai `core/` could call jevos for intent when the rules-based NLU is unsure (offline, ₹0) — needs a test set first.
- Score-based model routing inside Kalpa's own delegation (Jev picks the cheapest capable sub-agent).

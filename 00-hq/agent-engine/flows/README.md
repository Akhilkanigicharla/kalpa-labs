# Engine flows (A242)

One n8n flow per world (DESIGN.md §5). Each file imports into the Kalpa n8n engine; each has a test that runs its Code nodes with fake inputs.

| World | Flow | Test |
|---|---|---|
| b1 BotBhai | `b1-frontdesk-watchdog.json` (built by `b1_watchdog_build.py`): every 15 min, reads handed-over chats (status human), staff replies and business names from BotBhai Supabase (GET only, no message text), tells Akhil privately on Telegram when a customer waited 20+ min for a person, and when the WhatsApp 24 h window is closing or closed. Phones masked, alerts deduped, max 10 lines | `node test_b1_frontdesk_watchdog.js` |
| b4 Tab Lifeboat | `b4-review-replies.json`: daily 10:20 IST, reads `04-extensions/store/reviews.json` (id, rating, text; no names), drafts up to 3 replies with a free OpenRouter model, checks them, sends drafts to Akhil's private Telegram | `node test_b4_review_replies.js` |

Import: n8n → Workflows → Import from file. b1: set the Supabase URL in its Settings node and a Custom Auth credential "BotBhai Supabase (read only)" (headers apikey + Authorization; a read-only key, never the service key in chat) yourself. Set the two credentials (OpenRouter header `Authorization: Bearer …`, Kalpa Telegram) yourself in n8n. Files ship `active: false`; nothing has a public URL.

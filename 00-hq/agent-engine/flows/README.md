# Engine flows (A242)

One n8n flow per world (DESIGN.md §5). Each file imports into the Kalpa n8n engine; each has a test that runs its Code nodes with fake inputs.

| World | Flow | Test |
|---|---|---|
| b1 BotBhai | `b1-frontdesk-watchdog.json` (built by `b1_watchdog_build.py`): every 15 min, reads handed-over chats (status human), staff replies and business names from BotBhai Supabase (GET only, no message text), tells Akhil privately on Telegram when a customer waited 20+ min for a person, and when the WhatsApp 24 h window is closing or closed. Phones masked, alerts deduped, max 10 lines | `node test_b1_frontdesk_watchdog.js` |
| b2 App studio | `b2-review-watcher.json` (built by `b2_review_watcher_build.py`): daily 09:40 IST, reads `02-jobcard/store/reviews.json` (app, id, rating, text; no names), no model: keyword topics (crash, login, notifications, data, slow, payment) in 5 languages, repeat-problem alerts, ★1–2 reviews worst first, injected text flagged and not shown, one private Telegram digest to Akhil | `node test_b2_review_watcher.js` |
| b3 Exam Kits | `b3-exam-alerts.json` (built by `b3_exam_alerts_build.py`): daily 07:40 IST, reads `03-kits/engine/dist/exam-dates.json` (made by `03-kits/engine/export_dates.py` from the kit YAML key_dates), no model: drafts alerts for new/changed CONFIRMED dates from official sites (.gov.in/.nic.in/.ac.in/.edu.in) and 7-day/1-day reminders, flags past dates, clashes, unofficial or missing sources; drafts (English + Telugu when the data has it) go only to Akhil's private Telegram, never to students | `node test_b3_exam_alerts.js` |
| b4 Tab Lifeboat | `b4-review-replies.json`: daily 10:20 IST, reads `04-extensions/store/reviews.json` (id, rating, text; no names), drafts up to 3 replies with a free OpenRouter model, checks them, sends drafts to Akhil's private Telegram | `node test_b4_review_replies.js` |

Import: n8n → Workflows → Import from file. b1: set the Supabase URL in its Settings node and a Custom Auth credential "BotBhai Supabase (read only)" (headers apikey + Authorization; a read-only key, never the service key in chat) yourself. Set the two credentials (OpenRouter header `Authorization: Bearer …`, Kalpa Telegram) yourself in n8n. Files ship `active: false`; nothing has a public URL.

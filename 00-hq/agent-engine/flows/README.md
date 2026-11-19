# Engine flows (A242)

One n8n flow per world (DESIGN.md §5). Each file imports into the Kalpa n8n engine; each has a test that runs its Code nodes with fake inputs.

| World | Flow | Test |
|---|---|---|
| b4 Tab Lifeboat | `b4-review-replies.json`: daily 10:20 IST, reads `04-extensions/store/reviews.json` (id, rating, text; no names), drafts up to 3 replies with a free OpenRouter model, checks them, sends drafts to Akhil's private Telegram | `node test_b4_review_replies.js` |

Import: n8n → Workflows → Import from file. Set the two credentials (OpenRouter header `Authorization: Bearer …`, Kalpa Telegram) yourself in n8n. Files ship `active: false`; nothing has a public URL.

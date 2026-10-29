# BotBhai on Telegram (A130): setup, about 10 minutes

Telegram's Bot API is official and free. The bot uses the same engine, calendar, inbox and owner dashboard as WhatsApp.
Akhil does steps 1–3 himself; the bot token is a secret and never goes into chat, code or the repo.

1. **Make the bot (3 min).** In Telegram, open **@BotFather** (blue tick) → `/newbot` → name `Glow Studio Bookings` (the salon's name) → username ending in `bot`. BotFather replies with a token. Keep it private.
2. **Put the secrets in Netlify (3 min).** Netlify → the BotBhai site → Site configuration → Environment variables → add `TELEGRAM_BOT_TOKEN` (the token) and `TELEGRAM_WEBHOOK_SECRET` (any 20+ random letters and digits). Redeploy.
3. **Point Telegram at BotBhai (2 min).** In a browser, type (not paste into chat) this, with your own values:
   `https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<site>/.netlify/functions/telegram?client=<client id>&secret_token=<the same secret>`
   Telegram answers `"Webhook was set"`.
4. **Link the owner (1 min).** The salon owner opens the bot and sends `/owner` + the first 8 characters of their dashboard code. Owner alerts then arrive in that chat.

Customers find the bot by its link `t.me/<username>` or a QR code on the salon's counter. Only private chats are answered; groups are ignored.
Test: `NO_DELAY=1 node core/functions/telegram.test.js` (part of `tools/test-all.sh`).

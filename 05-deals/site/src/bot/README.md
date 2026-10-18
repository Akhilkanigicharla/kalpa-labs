# Deal Poster Bot (b5.W1.3, roadmap A18)

`post.py` posts due rows of `queue.csv` to the Telegram channel. Python standard library only.

- **Dry run by default.** It prints what it would post. `--live` posts only when the
  `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` secrets exist (Akhil adds them in GitHub Secrets himself).
- **Disclosure Gate (ASCI):** refuses any post without `#ad · affiliate link / అనుబంధ లింక్` in its first 2 lines.
- **Price rule:** price goes in the `price` column, never in the text; the bot adds
  "₹X as of 19 Oct, 8:30 am; may change". Prices older than 24 h are refused.
- **Never:** loan, insurance, mutual fund or broker words or links.
- Slots missed by more than 6 h are skipped. Posted ids go to `sent.log` so nothing posts twice.

Queue columns: `id,post_at,text,link,price,price_as_of` (times as `YYYY-MM-DD HH:MM`, IST; `\n` = new line).

```
python3 post.py --now "2026-10-19 09:00"     # dry run
python3 -m unittest -v test_post.py           # tests
```

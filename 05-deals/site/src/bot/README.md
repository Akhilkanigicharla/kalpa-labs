# Deals channel bots (b5)

Python standard library only. Two posters share one Disclosure Gate (`post.py`).

## `channel.py`: the scheduled Telugu deals channel (roadmap A58)

- **Input:** `deals.json` (the team fills it by hand from deal pages opened in their own browser; never scraped)
  and `tips.json` (weekly money tips). Field list is in the `_how` line at the top of each file.
- **Schedule:** `.github/workflows/deals-poster.yml`, 5 deal slots a day at 09:00, 12:30, 17:30, 20:00, 21:30 IST
  and a weekly money tip on Sundays at 10:30 IST. A slot missed by more than 2 h is not posted late.
  3–5 deals a day; fewer than 3 prints a warning.
- **Live only when all three exist:** `--live`, secrets `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`
  (or `TELEGRAM_CHANNEL_ID`) that Akhil adds himself, and repo variable `DEALS_LIVE=go`. Otherwise it is a dry run
  that only prints and never fails for missing secrets. Deals marked `"sample": true` never post live.
- **Rules (PLAN.md §3b):** every deal starts with `#ad · affiliate link / అనుబంధ లింక్`; prices carry "as of" time
  and "may change" and must be checked within 24 h; no loan/insurance/MF/broker words or links; no "no-cost EMI".
  Credit cards: EarnKaro/BankKaro links only, joining fee, annual fee, eligibility, issuer terms link and the RBI
  disclaimer on every post, "free" only for lifetime-free cards, at most 1 card post a day.
- **Links:** UTM tags added (`utm_source=telegram&utm_medium=channel&utm_campaign=deals-YYYYMMDD&utm_content=<id>`);
  short links (ekaro.in, amzn.to, fkrt.it, bit.ly) are left alone. Before a live post the link is checked
  (HEAD, then GET, 10 s timeout); 404/410/unreachable = dead, skipped, next deal takes the slot.
- **No duplicates:** `state.json` (committed by the workflow after live posts) keeps posted ids and links.
  An id never repeats; the same link not within 30 days. Delete a line from `dead` to retry a link.

```
python3 channel.py --day 2026-10-25     # print a full day's posts (dry run, sample data)
python3 channel.py                      # dry run of what is due now
python3 -m unittest -v test_post.py test_channel.py
```

## `post.py`: one-off queue poster (roadmap A18)

Posts due rows of `queue.csv`. Dry run by default; `--live` needs the two secrets. Queue columns:
`id,post_at,text,link,price,price_as_of` (times `YYYY-MM-DD HH:MM` IST; `\n` = new line).

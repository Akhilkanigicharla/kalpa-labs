# BotBhai Social Team (add-on)

A "social media team with zero employees" for a BotBhai client. It reads the client's `setups/<setup>/bot.config.json`
(services, prices, FAQs, WhatsApp) and makes a month of Instagram/Facebook content. The owner approves on WhatsApp.

```
strategist (plan) → copywriter → compliance → designer → owner OK on WhatsApp → publisher → analyst
```

## Run it (in Codespaces or GitHub Actions, nothing on Akhil's PC)
```bash
cd 01-botbhai/botbhai
python3 -m social.team --setup salon --start 2026-10-19 --weeks 4 --out out/social
#   → out/social/plan.csv, manifest.json, approval.txt, images + Reel MP4s
python3 -m social.team --out out/social --reply "skip 3, rest ok"      # owner's WhatsApp answer
python3 -m social.team --out out/social --publish --base-url https://<public-folder>/ --ig-user <IG user id>
#   dry run by default; add --live only when the client's IG_ACCESS_TOKEN secret is set
python3 -m social.team --insights results.json                          # weekly report + new pillar mix
python3 -m social.walkthrough --setup realestate --photos listing/ --rooms "Living room,Kitchen,..." \
    --title "3 BHK, Kondapur" --out out/walk.mp4 [--voice voice.mp3]   # 6-12 listing photos -> 9:16 walkthrough Reel
```

## Tests
`python3 social/test_social.py` (offline; part of `tools/test-all.sh`).

## Rules it keeps
- Never invents reviews or results: review/photo posts wait for the owner's real content.
- Blocks ad claims Indian rules forbid (ASCI, Drugs & Magic Remedies Act, CCPA coaching guidelines, RERA).
- Posts only with Meta's official API, only approved items, only with the client's own token.

Research and sources: `../../research/social-team.md`.

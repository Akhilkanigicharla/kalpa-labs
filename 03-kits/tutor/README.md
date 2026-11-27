# Socratic tutor mode (A301)

The b3 doubt bot (`00-hq/agent-engine/flows/b3-doubt-bot.json`) answers doubts. Send `"mode": "tutor"` and it teaches instead: one guiding question per reply, never the final answer until the student says it, in the student's own language (English, Telugu, Hindi, Tenglish, Hinglish).

- `prompt.txt`: the tutor rules. The build script embeds it: `python3 00-hq/agent-engine/flows/b3_doubt_bot_build.py`.
- Request: `{ "user": "...", "mode": "tutor", "text": "<student's latest turn>", "history": [{ "role": "student"|"tutor", "text": "..." }] }`. Up to 6 earlier turns are kept; each is cleaned, capped at 500 characters, masked (emails, phone numbers) and checked for leak or injection requests. Nothing is stored.
- The guard turns any tutor reply that does not end on a question into the safe fallback.
- `dialogues.json`: 10 test dialogues (2 per language). Test: `node 03-kits/tutor/test_tutor.js`.

Method adapted from Jane Street's `socratic-tutor` skill (github.com/janestreet/agent_skills, MIT licence, Copyright (c) 2026 Jane Street Group, LLC). Licence checked in the repo's LICENSE.md on 27 Nov 2026 (commit 469868f). No text copied word for word.

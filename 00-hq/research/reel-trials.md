# Reel repos part 3: trial verdicts (A207, 13 Nov 2026)

Measured in GitHub Actions only (`.github/workflows/reel-trials.yml`, run 43427908876, green), pinned commits, no logins, no secrets, nothing on Akhil's PC. Raw numbers: `reel-trials-raw.md`. Licences read from each repo's own LICENSE file at the pinned commit.

| Tool (licence) | Measured against | Numbers | Verdict |
|---|---|---|---|
| **claude-mem** 15.18.3 (Apache-2.0) | Graft + our HANDOFF.md/log memory | Installs in 22.1 s, 83 MB, CLI runs. Its memory compression calls a model: 25 source files read a model key (Anthropic/Gemini/OpenRouter). Our memory costs a session ~3,658 tokens (HANDOFF) + ~3,833 (newest log) and needs no key. | **Drop.** It cannot do its job without a secret (rule 1/12 trial was no-secrets), and it adds a background worker + database per session. Our files already work across both lanes. |
| **ECC** d2ef268 (MIT) | Superpowers (in use) + our 13-skill ECC subset | Full ECC: 1,068 skills, 67,146 tokens of skill descriptions loaded into every session's list. Superpowers: 15 skills, 849 tokens. Our ECC subset: 13 skills, 1,053 tokens. | **Keep the subset only, drop full ECC.** Installing all of it would cost ~79× Superpowers' listing tokens per session, against our token rule. |
| **Worktrunk** v0.81.0 (MIT / Apache-2.0) | `git worktree` + TEAM.md lanes | 3 worktrees: `wt switch --create` 0.99 s (3/3 ok) vs `git worktree add` 0.71 s. Our lanes are separate cloud containers, so worktrees in one container do not stop two lanes colliding; TEAM.md claims do. | **Drop for now.** No time saved and it solves a one-laptop problem we do not have. Revisit if one session ever runs parallel subagents in one checkout. |
| **Agent Reach** c70ae6d (MIT) | plain fetch (Firecrawl needs a key, not used here) | 11 of 16 channels need a login/session (not allowed for us). Public web read: example.com 0.50 s / 125 tokens vs curl 0.05 s / 84 tokens; RFC 2606 page 1.90 s / 2,449 tokens vs 0.10 s / 1,786 tokens. Every read goes through r.jina.ai (a third party sees the URL). | **Drop.** The 5 public channels are slower than a plain fetch, add a third-party hop, and Firecrawl (connected) already covers web reading. |

Net: nothing new adopted; one measured reason each. No sign-ups, payments or installs needed from Akhil.

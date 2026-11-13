# Reel repos part 3: trial verdicts (A207, 13 Nov 2026)

Measured in GitHub Actions only (`.github/workflows/reel-trials.yml`, run 43427908876, green), pinned commits, no logins, no secrets, nothing on Akhil's PC. Raw numbers: `reel-trials-raw.md`. Licences read from each repo's own LICENSE file at the pinned commit.

| Tool (licence) | Measured against | Numbers | Verdict |
|---|---|---|---|
| **claude-mem** 15.18.3 (Apache-2.0) | Graft + our HANDOFF.md/log memory | Installs in 22.1 s, 83 MB, CLI runs. Its memory compression calls a model: 25 source files read a model key (Anthropic/Gemini/OpenRouter). Our memory costs a session ~3,658 tokens (HANDOFF) + ~3,833 (newest log) and needs no key. | **Drop.** It cannot do its job without a secret (rule 1/12 trial was no-secrets), and it adds a background worker + database per session. Our files already work across both lanes. |
| **ECC** d2ef268 (MIT) | Superpowers (in use) + our 13-skill ECC subset | Full ECC: 1,068 skills, 67,146 tokens of skill descriptions loaded into every session's list. Superpowers: 15 skills, 849 tokens. Our ECC subset: 13 skills, 1,053 tokens. | **Keep the subset only, drop full ECC.** Installing all of it would cost ~79× Superpowers' listing tokens per session, against our token rule. |
| **Worktrunk** v0.81.0 (MIT / Apache-2.0) | `git worktree` + TEAM.md lanes | 3 worktrees: `wt switch --create` 0.99 s (3/3 ok) vs `git worktree add` 0.71 s. Our lanes are separate cloud containers, so worktrees in one container do not stop two lanes colliding; TEAM.md claims do. | **Drop for now.** No time saved and it solves a one-laptop problem we do not have. Revisit if one session ever runs parallel subagents in one checkout. |
| **Agent Reach** c70ae6d (MIT) | plain fetch (Firecrawl needs a key, not used here) | 11 of 16 channels need a login/session (not allowed for us). Public web read: example.com 0.50 s / 125 tokens vs curl 0.05 s / 84 tokens; RFC 2606 page 1.90 s / 2,449 tokens vs 0.10 s / 1,786 tokens. Every read goes through r.jina.ai (a third party sees the URL). | **Drop.** The 5 public channels are slower than a plain fetch, add a third-party hop, and Firecrawl (connected) already covers web reading. |

Net: nothing new adopted; one measured reason each. No sign-ups, payments or installs needed from Akhil.

## Reel repos part 4: fit check for the rest (A209, 13 Nov 2026)

Each fact below was checked today: the provider's own file or page plus a live call from this cloud session (no keys, no sign-ups).

| Tool (licence) | Checked | Numbers | Verdict |
|---|---|---|---|
| **LiquidAI LFM2.5** (LFM Open License v1.0, read from `LiquidAI/LFM2.5-24B-A2B/LICENSE` on Hugging Face) | Licence text; HF model API `inferenceProviderMapping`; OpenRouter `/api/v1/models` live | Licence: commercial use allowed only while our annual revenue is under US$10 million (§5, "Threshold"); fine for us today, must be re-read if we grow. HF: **no inference provider serves it** (mapping empty), and our `allowed.json` already excludes HF inference (no monthly free credit, 27 Oct). OpenRouter: `liquid/lfm-2.5-24b-a2b` is **paid** ($0.05 per million input tokens); only `liquid/lfm-3-1.7b:free` is free, and it is a different, smaller model. | **Not added to `llm-router.yml`.** No free, no-card endpoint exists for LFM2.5 today. Groq + OpenRouter `:free` stay. Revisit if a `:free` LFM2.5 appears on OpenRouter. |
| **Switch** (sandbox-quantum/switch; Apache-2.0 + modified Commons Clause, read from its `LICENSE`) | LICENSE file; repo README via search | Commons Clause forbids "Sell the Software or any derivative". Needs its own always-on server plus a Slack/Teams/Telegram app. | **Internal use only, not adopted now.** It may never be inside anything we sell (BotBhai, Agent Engine). Our own agents already run through GitHub Actions + the Agent Engine (A240). |
| **Openverse API** (api.openverse.org; code MIT, WordPress/openverse) | Live image search 13 Nov; response headers; docs page "Made with Openverse" | Works with no key. Anonymous limits from headers: **20/min, 200/day**. 2 of 5 calls returned **504**, so retries are required. Docs: "Openverse cannot make any claims about the accuracy of license information. You should always verify the license". | **Adopted** for Deals (b5) and Kits (b3) page images: `00-hq/tools/openverse_images.py` (CC0, Public Domain Mark, CC BY only; commercial; mature off; 3 tries with 2 s/4 s backoff; 20 s timeout; credit line built; source page link to check by hand before publishing). Test: `python3 00-hq/tools/test_openverse_images.py` 20 checks PASS (+ `--live` passed once); runs in `quality.yml`. |
| **blueprint.io** (paid site) | n/a | AI hardware design. | **Written off:** not one of the 7 streams. |
| **Ghidra** (Apache-2.0, read from its LICENSE) | LICENSE file | Reverse-engineering suite. | **Written off:** we do not analyse binaries in any stream. |
| **BLA (Blind LLM Agents)** | n/a | Reverse-engineering defence. | **Written off:** not relevant to any stream; licence not checked because nothing is used. |

Net: one adopted (Openverse, with a test); LFM2.5 waits for a free endpoint; Switch blocked for selling by its Commons Clause. Nothing for Akhil to sign up for or pay.

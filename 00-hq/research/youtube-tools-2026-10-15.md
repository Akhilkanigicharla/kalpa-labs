# Tools from Akhil's YouTube Shorts (15 Oct 2026)

How they were reviewed: the session can't play videos. It read each Short's title (YouTube oEmbed) and looked at the public preview frames YouTube publishes (hq1–3, oar1–3). The video description page returned a bot check, which was not bypassed.

## "5 GitHub Repos Every AI Builder Should Know" (Valeri Sabev, THKQdImIl60)
| Frame shows | Repo | Confidence | Licence | What we did |
|---|---|---|---|---|
| `using-superpowers`, `verification-before-completion`, `writing-plans` folders, "actually ship" | [obra/superpowers](https://github.com/obra/superpowers) | Certain (folder names) | MIT | Installed on Akhil's account (Anthropic directory). CLAUDE.md tells build sprints to use it. |
| "500+ ready prompts" + image grid (UI screens, posters, product ads, logo sheets) | [freestylefly/awesome-gpt-image-2](https://github.com/freestylefly/awesome-gpt-image-2) ("500+" headline, 520 cases, 13 categories incl. UI, posters, products, logos) | Likely, not certain | MIT | Its "atomic" prompt idea → BotBhai Social Team now writes a structured `image_prompt` for tip/offer/festival posts (our own text, no prompts copied). Never for work/review/team posts: those need real photos. |
| "FROM SCRATCH" + crossed-out pixel robot | Possibly [rohitg00/ai-engineering-from-scratch](https://github.com/rohitg00/ai-engineering-from-scratch) (65k stars, 523 lessons, ships `/start-learning` skills) | Guess | MIT | Nothing installed; noted as a free learning path for Akhil if he wants it. |
| (2 repos not in any preview frame) | unknown | — | — | Need the video description or a screenshot. |

## "Why the Reverse Engineer Anything Repo Gained 100k Stars in a Day" (Nate Herk, CklLenf9fNc)
[morluto/rea](https://github.com/morluto/rea), MIT, ~255k stars, a local MCP server (`npx rea-agents setup`). Not in the connector directory; needs Node + local tools; the session's safety check blocked running it in the cloud. Akhil chose to skip it. Use only on software we own or are allowed to examine.

## Update: the video description (screenshot from Akhil, 15 Oct)
The 5 repos are: Superpowers, Taskmaster AI, Awesome GPT Image 2, Awesome Agents, I Have ADHD. (The "from scratch" guess above was wrong.)

| Repo | Licence | Decision |
|---|---|---|
| Superpowers (obra) | MIT | Installed; CLAUDE.md uses it. |
| [Taskmaster AI](https://npmjs.com/package/task-master-ai) (eyaltoledano/claude-task-master) | MIT **with Commons Clause** (free to use; may not be sold or hosted as a service) | Not installed: it's a local MCP (npx) and our ROADMAP.md already does PRD → tasks. Fine to use internally later; never resell it. |
| Awesome GPT Image 2 | MIT | Idea used: Social Team `image_prompt`. |
| Awesome Agents (likely kyrolabs/awesome-agents) | list | Reference list for future research; nothing to install. |
| [I Have ADHD](https://github.com/ayghri/i-have-adhd) (Ayoub Ghriss) | MIT | Adapted as a `short-answers` skill (with attribution) and sent to Akhil to save. Its rules match CLAUDE.md's "Writing style for Akhil". |

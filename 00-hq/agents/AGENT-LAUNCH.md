# Launching a Kalpa agent (free n8n version of Anthropic's "launch-your-agent" method)

Source: [anthropics/launch-your-agent](https://github.com/anthropics/launch-your-agent) (Apache-2.0, copy in `00-hq/vendor/launch-your-agent/`).
We use its method, not its runtime: its launch step needs a paid Anthropic API key (Claude Managed Agents, "runs cost cents"). Our agents run on n8n with free models (`SERVICE-DESK.md`).

## The 5 steps for every new or changed agent

| Step | What we do | Where it lives |
|---|---|---|
| 1. Interview | One job, in Akhil's words. Who reads the output, what "done" means, and what the agent must never do. | KL Tasks row (`notes`) |
| 2. v0 | The smallest agent that does the core job: one prompt, its tools, a free model plus a fallback. **Drafts only**: no posting, no sending, no paying. | n8n workflow |
| 3. Outcome rubric | 3–6 yes/no checks the output must pass, e.g. "every price matches SERVICE-DESK", "no claim that is not in Kalpa facts", "#ad on affiliate links". Vigil grades every run against them. | Vigil prompt + this table |
| 4. Evals | Save 1–3 real past cases with known-good answers. Run them again before any prompt or model change goes live. The first verified good output becomes case 1. | `00-hq/agents/evals/<agent>/` |
| 5. Version rail | Everything not in v0 goes on a numbered list (v1, v2, …), each with **why later**: (a) not possible, (b) needs Akhil's account or secret, (c) planned. | KL Tasks + ROADMAP |

## Rules carried over from the source
- **Mock connectors first.** In v0 the agent writes the exact WhatsApp, Telegram or email message as a draft file. Wiring the real send is a later version, and only after Akhil says "go" (CLAUDE.md rule 9).
- **No literal dates in scheduled prompts.** Say "today" or "this week", because a cron re-uses the same text every run.
- **Change one thing per iteration** (prompt, tool or model), then re-run the evals.
- **Secrets only in n8n credentials or GitHub secrets.** Never in chat, prompts or files.

## Checklist before an agent is marked live
- [ ] Rubric written and Vigil grading against it
- [ ] At least 1 eval case saved and passing
- [ ] Drafts-only, or Akhil said "go" for the real action
- [ ] Free model and fallback verified today (rule 8)
- [ ] Version rail written

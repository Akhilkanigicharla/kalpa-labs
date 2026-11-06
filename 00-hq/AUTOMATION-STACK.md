# Kalpa automation stack: who does what (6 Nov 2026)

Akhil asked to split the work across n8n, GitHub Actions and similar free tools. Rule: each tool does the part it is best at, so no single free tier carries everything. Free = recurring and no card (CLAUDE.md rule 8).

## The split

| Job | Tool | Why this tool | Free limit that matters |
|---|---|---|---|
| **Heavy scheduled work**: 228 agents, lead lists, backtests, kit builds, daily brief, n8n sync | **GitHub Actions** | Unlimited minutes on a public repo; runs Python/Node; logs kept | Schedules run "best effort" and can be late or dropped (only 8 of about 400 keep-awake runs landed, 4–6 Nov) |
| **Precise timing + incoming webhooks**: keep n8n awake, start jobs at an exact minute, receive Telegram/WhatsApp callbacks later | **Cloudflare Workers** (code ready: `00-hq/cf-timer/`, tested) | Cron fires on time, down to every minute; always on | 5 cron triggers per account, 10 ms CPU per run, 100,000 requests a day (Cloudflare docs) |
| **Visual agent flows** (drag-and-drop editing, AI agent nodes) | **n8n** self-hosted on Render | Best visual editor, 400+ integrations; Akhil already set it up | 512 MB, sleeps after 15 min without traffic, 750 h/month shared |
| **Code scripts with a small UI/form**, second always-on runner | **Windmill Cloud** (optional) | Python/TypeScript scripts become apps and schedules | 1,000 executions a day free (automationatlas; dailyaifixs). AGPL core: fine for our own use, never embed in a product we sell |
| **Automation inside products we sell** (e.g. BotBhai client flows) | **Activepieces** (later, self-hosted) | MIT core: allowed in a sold product; n8n's licence is not | Self-host free; cloud free tier reports differ (2 flows / 1,000 tasks vs 10 flows), check before use |
| **Odd connectors n8n lacks** (tiny volume only) | **Zapier** (already connected) or **Make** | Huge app catalogues | Zapier free: 100 tasks/month, 2-step Zaps. Make free: 1,000 credits/month, 2 active scenarios, 15-min minimum gap |
| **AI mini-app demos** | **Google Opal** | Free, quick | No self-hosting, no code export. Demos only |

Not chosen (checked 6 Nov): **Trigger.dev** (free = $5 credit/month; it also had a security incident in Nov 2026), **Pipedream** (free tier reports conflict: 100 credits/day vs 300/month), **Huginn** (49k stars but Ruby, old), **Automatisch** (cloud shut down, repo quiet since Jan 2026), **Kestra** (Apache-2.0, strong but heavy Java; overkill), **Google Workspace Studio** (needs a paid Workspace plan).

## GitHub stars (July 2026, automationatlas): n8n much larger than all others; Huginn 49k+; Kestra 27k+; Activepieces 23k+; Windmill 17k+.

## Order of switch-on
1. **Cloudflare timer** → needs Akhil's free Cloudflare account + the Cloudflare connector (2 min, C65). Then Claude deploys `00-hq/cf-timer/` and retires the GitHub keepalive cron.
2. Keep n8n + Actions as they are.
3. Windmill / Activepieces only when a job needs them.

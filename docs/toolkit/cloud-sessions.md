# What every Kalpa cloud session has (18 Oct 2026)

**Answer first:** a Claude cloud session on this repo starts with Akhil's claude.ai connectors and plugins, plus this repo's config. Nothing is installed on Akhil's PC from here.

## 1. Loaded automatically from Akhil's claude.ai account
- **Connectors (MCP):** n8n (22 agents, data tables, workflows), Hugging Face, Firecrawl (web search/scrape), PostHog, Zapier, Gmail, Google Calendar/Docs/Sheets/Slides, Supabase, Netlify, Floot, PaperOffice, Coinversa Pulse, TEXT_TO_QUANT, SlickTrip, Claude Docs.
- **Plugins/skills:** Superpowers, design, engineering, marketing, sales, finance, small-business, product-management, data, legal, operations, productivity, customer-support, brand-voice, product-tracking, pdf-viewer.
- Add a connector or plugin once in claude.ai settings and every new cloud session gets it. That is the main way to "power up" sessions.

## 2. From this repo
| File | What it does |
|---|---|
| `.mcp.json` | Playwright MCP, pinned `@playwright/mcp@0.0.83`, headless + isolated (uses the session's pre-installed Chromium). PostHog and Perplexity were removed here: PostHog already arrives as an account connector; Perplexity needs a paid key. |
| `.claude/settings.json` | Telemetry off for `npx skills`, TradingAgents and headroom; Anthropic's official plugin marketplace with **claude-code-setup** enabled; repo MCP servers auto-approved; SessionStart hook. |
| `.claude/hooks/toolkit-status.sh` | Read-only: prints node/python/uv/ffmpeg/gh/Chromium status at session start. Installs nothing. |
| `.claude/skills/short-answers/` | How to write to Akhil. |
| `00-hq/vendor/superpowers/` | Fallback copy of the Superpowers skills. |

## 3. Tools that run on demand (not at session start)
| Tool | How | Where |
|---|---|---|
| TradingAgents v0.7.0 | `.github/workflows/tradingagents.yml` (manual) | GitHub Actions; needs secret `OPENROUTER_API_KEY` set by Akhil |
| Scrapling, HyperFrames render, Presenton | per `docs/toolkit/cloud-hosting-plan.md` | Actions / Codespaces |
| Jev (hosted) | n8n gateway credits | n8n agents + Smart Router workflow |
| jevos (local) | MCP `kalpa-jev` | Akhil's PC only, Claude Code |

## 4. Waiting for Akhil's OK (third-party code)
The session's safety check blocked installing these into sessions automatically, because they are third-party code that would run in every session. They are vetted ADOPT items in `TOOLKIT.md`. Say "approve skills" and the next session adds them (project-scoped, pinned):
1. `mattpocock/skills` → grill-me (MIT)
2. `cloudflare/security-audit-skill` → security-audit (MIT)
3. `emilkowalski/skills` (MIT)
4. `heygen-com/hyperframes` plugin (Apache-2.0)

Better route that needs no repo change: install them once as claude.ai account skills/plugins, and they load in every session like section 1.

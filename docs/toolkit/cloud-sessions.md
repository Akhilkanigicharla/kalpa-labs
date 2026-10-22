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

## 4. Approved third-party skills (installed 18 Oct, Akhil: "approveskills")
Committed in `.claude/skills/` (pinned by hash in `/skills-lock.json`, licences in `.claude/skills/THIRD_PARTY.md`), so every cloud session and Claude Code in this repo has them:

| Skill | Use it for | Agent/world |
|---|---|---|
| `grill-me` / `grilling` (Matt Pocock) | Stress-test a plan with rounds of questions before building | Kalpa, every world's PLAN.md |
| `security-audit` (Cloudflare) | Security review of our own code before BotBhai or any site goes live | Vigil, Probe; b1, b5, b6 |
| `emil-design-eng`, `animate`, `animate-expo`, `mobile-native`, `review-animations`, `break-ui`, `prototype`, `pick-ui-library` (Emil Kowalski) | UI polish, motion, phone feel, worst-case data tests, quick variants | Pixel, Lens, Forge; all UIs (Kalpavruksha rules still win) |

Plugin: **HyperFrames** `hyperframes@hyperframes` pinned to `v0.8.169` (HTML → video; skills only). Render with `npx hyperframes@0.8.169`, not `@latest`.

Left out on purpose from Emil's set: `write-swift`, `apple-design`, `ask-sonner`, `animation-*`, `improve-animations`, `find-animation-opportunities` (no iOS work; others overlap the ones above).

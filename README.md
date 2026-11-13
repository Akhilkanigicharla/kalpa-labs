> Akhil's 7 streams are defined in [00-hq/VISION.md](00-hq/VISION.md). It wins over anything below.

# 🏰 Kalpa Labs · START HERE

A one-person company in Hyderabad (Udyam UDYAM-TS-02-0382711), run by Akhil with Claude, one hour a day. One HQ and seven business worlds. **Build mode:** free tiers only, no paid sign-ups until the CEO decides to go public.

## The map

| # | Folder | Label | World | What it sells | Status |
|---|---|---|---|---|---|
| 00 | [00-hq](00-hq/) | 🏰 HQ | The Citadel | Company plan, roadmap + task engine, agents, vendored skills, shared tools | Plan approved-pending, 215-agent org built |
| b1 | [01-botbhai](01-botbhai/) | 🤖 BotBhai | Botforge | AI agents for salons, gyms and real estate agents: customers, bookings, social media | **Built (v3)**, ready to sell |
| b2 | [02-jobcard](02-jobcard/) | 📱 Mobile app | Workshop Valley | Worldwide paid app: idea being researched (JobCard parked) | Research |
| b3 | [03-kits](03-kits/) | 📚 Exam Kits | Library of Ranks | Exam kits for all govt, bank and private exams: tracker, reminders, alerts, best material + videos | Planned (agents build Kit #1 now) |
| b4 | [04-extensions](04-extensions/) | 🧩 Tab Lifeboat | Plugin Isles | Chrome extension that never loses your tabs | Planned (agent-only) |
| b5 | [05-deals](05-deals/) | 🛍️ Deals & Tools | Bazaar Bay | Telugu + English calculators, deals channel | Planned (agents start now) |
| b6 | [06-finops](06-finops/) | 🛡️ AI FinOps + Guardrails | Ledger Peaks | Consulting: AI cost (FinOps) + AI guardrails/governance (AIGP, ISO 42001); tools are one piece | Planned (agents start now, selling 16 Nov) |
| b7 | [07-trading](07-trading/) | 🔮 Trading | The Market Maze | Real-money algo trading for Akhil (research → backtest → paper → small live) | Planned (paper only) |
| b8 | [08-microapps](08-microapps/) | 🌱 Micro-apps | Seedling Grove | Many small one-problem apps picked from real revenue data; first: Kalpa QR (codes never stop working) | Building (Kalpa QR v1) |

## Every world folder looks the same

```
0X-world/
├── README.md     ← label card: what, status, price, where things are
├── PLAN.md       ← the money plan (verdict, customers, economics, quests, kill rules)
├── research/     ← GitHub repos found, cloned, run: adopt / learn / avoid
├── docs/         ← decisions, requirements, sales material
├── design/       ← UI design brief + mockups
└── <code>/       ← the product
```

## The three files to read first

1. [00-hq/PLAN.md](00-hq/PLAN.md): how the seven worlds become one money machine (order, money, the CEO's hour).
2. [00-hq/ROADMAP.md](00-hq/ROADMAP.md): every remaining task, split into **Agent queue** (Claude builds it automatically) and **CEO queue** (Akhil's 1 hour).
3. [00-hq/LINKS.md](00-hq/LINKS.md): every Claude artifact, document, scheduled task and cloud account, labelled.

AI toolkit (vetted tools, Claude setup on Windows, hosting plan, local models): [docs/toolkit/TOOLKIT.md](docs/toolkit/TOOLKIT.md). Project MCP servers: [.mcp.json](.mcp.json).

## Rules

- **Build mode:** free tiers only; paid items wait in the Launch phase.
- **Nothing heavy on the local PC:** code runs in GitHub Codespaces/Actions, Colab, Supabase, Netlify or Cloudflare.
- **No secrets in this repo:** keys go in GitHub/Netlify/Supabase secrets, passwords in Bitwarden.
- **Every product gets its own brand name**, trademark-checked before launch.
- `archive/` holds files from this repo's earlier life.

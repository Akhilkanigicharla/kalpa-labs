# 🏰 Kalpa Labs · START HERE

A one-person company in Hyderabad (Udyam UDYAM-TS-02-0382711), run by Akhil with Claude, one hour a day. One HQ and seven business worlds. **Build mode:** free tiers only, no paid sign-ups until the CEO decides to go public.

## The map

| # | Folder | Label | World | What it sells | Status |
|---|---|---|---|---|---|
| 00 | [00-hq](00-hq/) | 🏰 HQ | The Citadel | Company plan, roadmap + task engine, agents, vendored skills, shared tools | Plan approved-pending, 215-agent org built |
| b1 | [01-botbhai](01-botbhai/) | 🤖 BotBhai | Botforge | WhatsApp + voice automation for salons, gyms, coaching, real estate | **Built (v3)**, ready to sell |
| b2 | [02-jobcard](02-jobcard/) | 🛠️ JobCard | Workshop Valley | Voice job-card + invoice app for AC technicians | Planned (build Dec–Feb) |
| b3 | [03-kits](03-kits/) | 📚 Kits | Library of Ranks | Google Sheets kits for exams and tax | Planned (agents build Kit #1 now) |
| b4 | [04-extensions](04-extensions/) | 🧩 Tab Lifeboat | Plugin Isles | Chrome extension that never loses your tabs | Planned (agent-only) |
| b5 | [05-deals](05-deals/) | 🛍️ Deals & Tools | Bazaar Bay | Telugu + English calculators, deals channel | Planned (agents start now) |
| b6 | [06-finops](06-finops/) | 📊 Ledger Peaks | Ledger Peaks | AI cost in ₹ + DPDP evidence pack (flagship) | Planned (agents start now, selling 16 Nov) |
| b7 | [07-trading](07-trading/) | 🔮 Trading Lab | The Market Maze | Nothing (paper-trading research) | Planned (paper only) |

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
